#!/usr/bin/env python3
"""
HandBrake Service for HandBrake2Resilio (Simplified)
Provides REST API interface for video conversion operations with SQLite storage
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import threading
import time
import json
import subprocess
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import structlog

# Import our modules
from shared.db import get_db_connection
from shared.job_queue import ConversionJob, JobStatus

OUTPUT_ROOT = os.environ.get("OUTPUT_ROOT", "/media/output")


INPUT_MOUNT_PREFIX = "/media/input"


def validate_input_path(path: str) -> bool:
    """
    Ensure input_path stays under the container mount ``/media/input`` (must be that
    prefix or a path under ``/media/input/``), blocks ``..`` segments, and when the
    mount exists, rejects symlink escape via ``realpath``.
    """
    if not path or not isinstance(path, str):
        return False
    normalized = path.replace("\\", "/")
    if any(seg == ".." for seg in normalized.split("/")):
        return False
    norm = os.path.normpath(path)
    norm_fwd = norm.replace("\\", "/")
    if any(seg == ".." for seg in norm_fwd.split("/")):
        return False
    root = INPUT_MOUNT_PREFIX
    if not (norm_fwd == root or norm_fwd.startswith(root + "/")):
        return False
    if os.path.isdir(root):
        try:
            resolved_input = os.path.realpath(norm)
            resolved_root = os.path.realpath(root)
            if not (
                resolved_input == resolved_root
                or resolved_input.startswith(resolved_root + os.sep)
            ):
                return False
        except OSError:
            return False
    return True


def default_output_path_from_input(input_path: str) -> str:
    """
    When no output_path is provided, map input under OUTPUT_ROOT:
    strip /media/input prefix, preserve subdirs, use .mkv extension.
    """
    input_norm = os.path.normpath(input_path)
    prefixes = (INPUT_MOUNT_PREFIX,)
    relative: str | None = None
    for prefix in prefixes:
        if input_norm == prefix:
            relative = ""
            break
        if input_norm.startswith(prefix + os.sep):
            relative = input_norm[len(prefix) + 1 :]
            break
    if relative is None:
        stem, _ = os.path.splitext(os.path.basename(input_norm))
        return os.path.join(OUTPUT_ROOT, f"{stem}.mkv")
    if not relative:
        stem, _ = os.path.splitext(os.path.basename(input_norm))
        return os.path.join(OUTPUT_ROOT, f"{stem}.mkv")
    stem, _ = os.path.splitext(relative)
    return os.path.join(OUTPUT_ROOT, f"{stem}.mkv")


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


def check_media_directories() -> None:
    """Warn at startup if standard Docker mount points are missing or unusable."""
    input_root = INPUT_MOUNT_PREFIX
    output_root = os.environ.get("OUTPUT_ROOT", "/media/output")
    if not os.path.isdir(input_root):
        logger.warning(
            "media input mount missing or not a directory — conversions require paths under /media/input",
            path=input_root,
        )
    elif not os.access(input_root, os.R_OK):
        logger.warning("media input path is not readable", path=input_root)
    if not os.path.isdir(output_root):
        logger.warning(
            "media output mount missing or not a directory — job output may fail",
            path=output_root,
        )
    elif not os.access(output_root, os.W_OK):
        logger.warning("media output path is not writable", path=output_root)


app = Flask(__name__)
CORS(app)
check_media_directories()

# Global job tracking
active_jobs = {}
job_lock = threading.Lock()


def init_job_database():
    """Initialize SQLite database for job tracking"""
    db_path = os.getenv("DATABASE_PATH", "/data/handbrake.db")

    with get_db_connection(db_path) as conn:
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
            [entry["job"] for entry in active_jobs.values() if entry["job"].status == JobStatus.RUNNING]
        )

    return (
        usage["cpu_percent"] < 80
        and usage["memory_percent"] < 80
        and usage["disk_free_gb"] > 5
        and active_count < max_jobs
    )


def save_job_to_db(job):
    """Save job to SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/data/handbrake.db")

    with get_db_connection(db_path) as conn:
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
    db_path = os.getenv("DATABASE_PATH", "/data/handbrake.db")

    with get_db_connection(db_path) as conn:
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
    db_path = os.getenv("DATABASE_PATH", "/data/handbrake.db")

    with get_db_connection(db_path) as conn:
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

        # Update job status and register in active_jobs (no process yet)
        with job_lock:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            active_jobs[job.id] = {"job": job, "process": None}

        # Save to database
        save_job_to_db(job)

        out_dir = os.path.dirname(job.output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

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

        # Run conversion and store Popen reference for cancellation
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        with job_lock:
            if job.id in active_jobs:
                active_jobs[job.id]["process"] = process

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

        # Check result — skip DB update if job was externally cancelled
        return_code = process.poll()
        with job_lock:
            was_cancelled = job.status == JobStatus.CANCELLED

        if was_cancelled:
            logger.info(f"Job {job.id} was cancelled; skipping completion update")
            return

        if return_code == 0:
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.completed_at = datetime.utcnow()
            logger.info(f"Job {job.id} completed successfully")
        else:
            job.status = JobStatus.FAILED
            job.error_message = f"HandBrake failed with return code {return_code}"
            logger.error(f"Job {job.id} failed: {job.error_message}")

        # Save to database and remove from active tracking
        save_job_to_db(job)
        with job_lock:
            active_jobs.pop(job.id, None)

    except Exception as e:
        logger.error(f"Error in conversion for job {job.id}: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        save_job_to_db(job)
        with job_lock:
            active_jobs.pop(job.id, None)


@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        usage = get_system_usage()
        with job_lock:
            active_count = len(
                [e for e in active_jobs.values() if e["job"].status == JobStatus.RUNNING]
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
        raw_output = data.get("output_path")

        if not input_path:
            return (
                jsonify(
                    {
                        "error": "Missing required fields",
                        "message": "input_path is required",
                    }
                ),
                400,
            )

        if not validate_input_path(input_path):
            return (
                jsonify(
                    {
                        "error": "Invalid input_path",
                        "message": "input_path must be under /media/input with no path traversal (..)",
                    }
                ),
                400,
            )

        if raw_output is not None and str(raw_output).strip():
            output_path = str(raw_output).strip()
        else:
            output_path = default_output_path_from_input(input_path)

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
            id=data.get("job_id") or data.get("id") or f"job_{int(time.time())}",
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
                return jsonify(active_jobs[job_id]["job"].to_dict())

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
            for entry in active_jobs.values():
                jobs.append(entry["job"].to_dict())

        return jsonify({"jobs": jobs, "count": len(jobs)})

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({"error": "Failed to list jobs", "message": str(e)}), 500


def _terminate_process(process: subprocess.Popen, job_id: str) -> None:
    """Send SIGTERM then SIGKILL to a HandBrakeCLI subprocess."""
    if process is None:
        return
    try:
        process.terminate()
        logger.info(f"Sent SIGTERM to process for job {job_id}, waiting up to 5s")
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"Process for job {job_id} did not exit after SIGTERM; sending SIGKILL")
            process.kill()
            process.wait()
        logger.info(f"Process for job {job_id} terminated (returncode={process.returncode})")
    except OSError as exc:
        # Process may have already exited
        logger.warning(f"OSError while terminating process for job {job_id}: {exc}")


def _cleanup_partial_output(output_path: str, job_id: str) -> None:
    """Remove a partial output file left by a cancelled conversion."""
    if output_path and os.path.exists(output_path):
        try:
            os.remove(output_path)
            logger.info(f"Removed partial output file for job {job_id}: {output_path}")
        except OSError as exc:
            logger.warning(f"Could not remove partial output for job {job_id}: {exc}")


@app.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """Cancel a running job by killing the HandBrakeCLI subprocess."""
    try:
        process_to_kill = None
        output_path_to_clean = None

        with job_lock:
            if job_id not in active_jobs:
                return (
                    jsonify({"error": "Job not found", "message": f"Job {job_id} does not exist"}),
                    404,
                )

            entry = active_jobs[job_id]
            job = entry["job"]

            if job.status != JobStatus.RUNNING:
                return (
                    jsonify({"error": "Job not running", "message": f"Job {job_id} is not currently running"}),
                    400,
                )

            # Mark cancelled and capture references before releasing lock
            job.status = JobStatus.CANCELLED
            process_to_kill = entry.get("process")
            output_path_to_clean = job.output_path
            active_jobs.pop(job_id)

        # Kill the subprocess outside the lock to avoid blocking
        _terminate_process(process_to_kill, job_id)

        # Persist cancelled status and clean up partial file
        save_job_to_db(job)
        _cleanup_partial_output(output_path_to_clean, job_id)

        logger.info(f"Job {job_id} cancelled successfully")
        return jsonify({"message": "Job cancelled successfully", "job_id": job_id})

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
        f"Database Path: {os.getenv('DATABASE_PATH', '/data/handbrake.db')}"
    )

    # Start the service
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8081)),
        debug=False,
    )
