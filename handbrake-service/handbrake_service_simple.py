#!/usr/bin/env python3
"""
HandBrake Service for HandBrake2Resilio (Simplified)
Provides REST API interface for video conversion operations with SQLite storage
"""

import os
import logging
import threading
import time
import sqlite3
import json
import subprocess
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import structlog

# Import our modules
from config import config
from job_queue import ConversionJob, JobStatus

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

app = Flask(__name__)
CORS(app)

# Global job tracking
active_jobs = {}
job_lock = threading.Lock()


def init_job_database():
    """Initialize SQLite database for job tracking"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                input_path TEXT NOT NULL,
                output_path TEXT NOT NULL,
                quality INTEGER DEFAULT 23,
                resolution TEXT DEFAULT '720x480',
                video_bitrate INTEGER DEFAULT 1000,
                audio_bitrate INTEGER DEFAULT 96,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
        """
        )
        conn.commit()
        logger.info("Job database initialized")


# Initialize database
init_job_database()


def get_system_usage():
    """Get current system resource usage"""
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
        }
    except Exception as e:
        logger.error(f"Error getting system usage: {e}")
        return {
            "cpu_percent": 0,
            "memory_percent": 0,
            "memory_available_gb": 0,
            "disk_percent": 0,
            "disk_free_gb": 0,
        }


def can_start_job():
    """Check if system can handle another job"""
    usage = get_system_usage()
    max_jobs = int(os.getenv("MAX_CONCURRENT_JOBS", 8))

    with job_lock:
        active_count = len(
            [j for j in active_jobs.values() if j.status == JobStatus.RUNNING]
        )

    return (
        usage["cpu_percent"] < 80
        and usage["memory_percent"] < 80
        and usage["disk_free_gb"] > 5
        and active_count < max_jobs
    )


def save_job_to_db(job):
    """Save job to SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO jobs (
                id, input_path, output_path, quality, resolution,
                video_bitrate, audio_bitrate, status, progress,
                error_message, retry_count, max_retries,
                created_at, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job.id,
                job.input_path,
                job.output_path,
                job.quality,
                job.resolution,
                job.video_bitrate,
                job.audio_bitrate,
                job.status.value,
                job.progress,
                job.error_message,
                job.retry_count,
                job.max_retries,
                job.created_at.isoformat() if job.created_at else None,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
            ),
        )
        conn.commit()


def get_job_from_db(job_id):
    """Get job from SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT * FROM jobs WHERE id = ?
        """,
            (job_id,),
        )
        row = cursor.fetchone()

        if row:
            # Convert row to ConversionJob object
            job = ConversionJob(
                id=row[0],
                input_path=row[1],
                output_path=row[2],
                quality=row[3],
                resolution=row[4],
                video_bitrate=row[5],
                audio_bitrate=row[6],
                status=JobStatus(row[7]),
                progress=row[8],
                error_message=row[9],
                retry_count=row[10],
                max_retries=row[11],
            )
            return job
        return None


def get_all_jobs_from_db():
    """Get all jobs from SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        rows = cursor.fetchall()

        jobs = []
        for row in rows:
            job = ConversionJob(
                id=row[0],
                input_path=row[1],
                output_path=row[2],
                quality=row[3],
                resolution=row[4],
                video_bitrate=row[5],
                audio_bitrate=row[6],
                status=JobStatus(row[7]),
                progress=row[8],
                error_message=row[9],
                retry_count=row[10],
                max_retries=row[11],
            )
            jobs.append(job.to_dict())

        return jobs


def run_handbrake_conversion(job):
    """Run HandBrake conversion for a job"""
    try:
        logger.info(f"Starting conversion for job {job.id}")

        # Update job status
        with job_lock:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            active_jobs[job.id] = job

        # Save to database
        save_job_to_db(job)

        # Build HandBrake command
        cmd = [
            "HandBrakeCLI",
            "-i",
            job.input_path,
            "-o",
            job.output_path,
            "-q",
            str(job.quality),
            "-r",
            job.resolution,
            "-b",
            str(job.video_bitrate),
            "-B",
            str(job.audio_bitrate),
            "--json",  # Enable JSON output for progress
        ]

        # Run conversion
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        # Monitor progress
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                try:
                    # Parse JSON progress updates
                    progress_data = json.loads(output.strip())
                    if "Progress" in progress_data:
                        job.progress = progress_data["Progress"]["Progress"] * 100
                        logger.info(f"Job {job.id} progress: {job.progress:.1f}%")
                        save_job_to_db(job)
                except json.JSONDecodeError:
                    pass  # Skip non-JSON output

        # Check result
        return_code = process.poll()
        if return_code == 0:
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            logger.info(f"Job {job.id} completed successfully")
        else:
            job.status = JobStatus.FAILED
            job.error_message = f"HandBrake failed with return code {return_code}"
            logger.error(f"Job {job.id} failed: {job.error_message}")

        # Save to database
        save_job_to_db(job)

    except Exception as e:
        logger.error(f"Error in conversion for job {job.id}: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        save_job_to_db(job)


@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        usage = get_system_usage()
        with job_lock:
            active_count = len(
                [j for j in active_jobs.values() if j.status == JobStatus.RUNNING]
            )

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "handbrake",
                "system": usage,
                "active_jobs": active_count,
                "database": "sqlite",
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/convert", methods=["POST"])
def start_conversion():
    """Start a new video conversion job"""
    try:
        data = request.get_json()

        # Validate required fields
        input_path = data.get("input_path")
        output_path = data.get("output_path")

        if not input_path or not output_path:
            return (
                jsonify(
                    {
                        "error": "Missing required fields",
                        "message": "input_path and output_path are required",
                    }
                ),
                400,
            )

        # Check if system can handle the job
        if not can_start_job():
            return (
                jsonify(
                    {
                        "error": "System overloaded",
                        "message": "System resources are currently at capacity",
                    }
                ),
                503,
            )

        # Create job
        job = ConversionJob(
            id=data.get("job_id", f"job_{int(time.time())}"),
            input_path=input_path,
            output_path=output_path,
            quality=data.get("quality", 23),
            resolution=data.get("resolution", "720x480"),
            video_bitrate=data.get("video_bitrate", 1000),
            audio_bitrate=data.get("audio_bitrate", 96),
        )

        # Save to database
        save_job_to_db(job)

        # Start conversion in background thread
        thread = threading.Thread(target=run_handbrake_conversion, args=(job,))
        thread.daemon = True
        thread.start()

        logger.info(f"Started conversion job {job.id}")

        return jsonify(
            {"message": "Conversion started", "job_id": job.id, "job": job.to_dict()}
        )

    except Exception as e:
        logger.error(f"Error starting conversion: {e}")
        return jsonify({"error": "Failed to start conversion", "message": str(e)}), 500


@app.route("/job/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get status of a specific job"""
    try:
        # Check active jobs first
        with job_lock:
            if job_id in active_jobs:
                return jsonify(active_jobs[job_id].to_dict())

        # Check database
        job = get_job_from_db(job_id)
        if job:
            return jsonify(job.to_dict())

        return (
            jsonify(
                {"error": "Job not found", "message": f"Job {job_id} does not exist"}
            ),
            404,
        )

    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({"error": "Failed to get job status", "message": str(e)}), 500


@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List all jobs"""
    try:
        # Get jobs from database
        jobs = get_all_jobs_from_db()

        # Add active jobs
        with job_lock:
            for job in active_jobs.values():
                jobs.append(job.to_dict())

        return jsonify({"jobs": jobs, "count": len(jobs)})

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({"error": "Failed to list jobs", "message": str(e)}), 500


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """Cancel a running job"""
    try:
        with job_lock:
            if job_id in active_jobs:
                job = active_jobs[job_id]
                if job.status == JobStatus.RUNNING:
                    # TODO: Implement actual job cancellation
                    job.status = JobStatus.CANCELLED
                    save_job_to_db(job)
                    logger.info(f"Job {job_id} cancelled")
                    return jsonify(
                        {"message": "Job cancelled successfully", "job_id": job_id}
                    )
                else:
                    return (
                        jsonify(
                            {
                                "error": "Job not running",
                                "message": f"Job {job_id} is not currently running",
                            }
                        ),
                        400,
                    )
            else:
                return (
                    jsonify(
                        {
                            "error": "Job not found",
                            "message": f"Job {job_id} does not exist",
                        }
                    ),
                    404,
                )

    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        return jsonify({"error": "Failed to cancel job", "message": str(e)}), 500


@app.route("/")
def root():
    """Root endpoint"""
    return jsonify(
        {
            "service": "HandBrake Service",
            "version": "2.0.0",
            "status": "running",
            "endpoints": {
                "health": "/health",
                "convert": "/convert",
                "jobs": "/jobs",
                "job_status": "/job/<job_id>",
                "cancel": "/cancel/<job_id>",
            },
        }
    )


if __name__ == "__main__":
    # Log startup information
    logger.info("Starting HandBrake Service (Simplified)...")
    logger.info(f"Max concurrent jobs: {os.getenv('MAX_CONCURRENT_JOBS', 8)}")
    logger.info(
        f"Database Path: {os.getenv('DATABASE_PATH', '/app/data/handbrake2resilio.db')}"
    )

    # Start the service
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8081)),
        debug=False,
    )
