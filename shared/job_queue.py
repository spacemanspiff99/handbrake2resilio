#!/usr/bin/env python3
"""
Job Queue System for HandBrake2Resilio
Handles video conversion jobs with resource management and error recovery
"""

import threading
import time
import queue
import sqlite3
import psutil
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class ConversionJob:
    """Video conversion job data"""

    id: str
    input_path: str
    output_path: str
    quality: int = 23
    resolution: str = "720x480"
    video_bitrate: int = 1000
    audio_bitrate: int = 96
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    estimated_duration: int = 0  # seconds

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = (
            self.completed_at.isoformat() if self.completed_at else None
        )
        return data


class ResourceMonitor:
    """Monitor system resources and manage limits"""

    def __init__(self, config):
        self.config = config
        self.cpu_threshold = config.resources.cpu_limit_percent
        self.memory_threshold = config.resources.memory_limit_percent
        self.max_jobs = config.resources.max_concurrent_jobs

    def get_system_usage(self) -> Dict[str, float]:
        """Get current system resource usage"""
        try:
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

    def can_start_job(self) -> bool:
        """Check if a new job can be started based on resource limits"""
        usage = self.get_system_usage()

        # Check CPU usage
        if usage["cpu_percent"] > self.cpu_threshold:
            logger.debug(f"CPU usage too high: {usage['cpu_percent']}%")
            return False

        # Check memory usage
        if usage["memory_percent"] > self.memory_threshold:
            logger.debug(f"Memory usage too high: {usage['memory_percent']}%")
            return False

        # Check available memory (minimum 2GB)
        if usage["memory_available_gb"] < 2.0:
            logger.debug(
                f"Available memory too low: {usage['memory_available_gb']:.1f}GB"
            )
            return False

        # Check disk space (minimum 5GB)
        if usage["disk_free_gb"] < 5.0:
            logger.debug(f"Available disk space too low: {usage['disk_free_gb']:.1f}GB")
            return False

        return True

    def get_optimal_job_count(self) -> int:
        """Calculate optimal number of concurrent jobs based on resources"""
        usage = self.get_system_usage()

        # Base calculation on CPU cores and current usage
        cpu_count = psutil.cpu_count()
        current_cpu = usage["cpu_percent"]

        # Conservative approach: use fewer jobs if CPU is high
        if current_cpu > 70:
            optimal = max(1, cpu_count // 4)
        elif current_cpu > 50:
            optimal = max(2, cpu_count // 2)
        else:
            optimal = min(self.max_jobs, cpu_count)

        return optimal


class JobQueue:
    """Thread-safe job queue with persistence and error recovery"""

    def __init__(self, config, db_path: str):
        self.config = config
        self.db_path = db_path
        self.resource_monitor = ResourceMonitor(config)

        # Thread-safe queue
        self.job_queue = queue.Queue()
        self.running_jobs: Dict[str, ConversionJob] = {}
        self.completed_jobs: Dict[str, ConversionJob] = {}

        # Threading
        self.lock = threading.RLock()
        self.worker_threads: List[threading.Thread] = []
        self.shutdown_event = threading.Event()

        # Initialize database
        self._init_database()

        # Start worker threads
        self._start_workers()

    def _init_database(self):
        """Initialize job queue database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                        completed_at TIMESTAMP,
                        estimated_duration INTEGER DEFAULT 0
                    )
                """
                )
                conn.commit()
                logger.info("Job queue database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize job queue database: {e}")
            raise

    def _start_workers(self):
        """Start worker threads"""
        worker_count = self.resource_monitor.get_optimal_job_count()

        for i in range(worker_count):
            worker = threading.Thread(
                target=self._worker_loop, name=f"JobWorker-{i}", daemon=True
            )
            worker.start()
            self.worker_threads.append(worker)

        logger.info(f"Started {worker_count} job worker threads")

    def _worker_loop(self):
        """Main worker loop"""
        while not self.shutdown_event.is_set():
            try:
                # Wait for job or shutdown
                try:
                    job = self.job_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # Check if we can start the job
                if not self.resource_monitor.can_start_job():
                    # Put job back in queue and wait
                    self.job_queue.put(job)
                    time.sleep(5)
                    continue

                # Process the job
                self._process_job(job)

                # Mark task as done
                self.job_queue.task_done()

            except Exception as e:
                logger.error(f"Worker thread error: {e}")
                time.sleep(1)

    def _process_job(self, job: ConversionJob):
        """Process a single conversion job"""
        try:
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            self._update_job_in_db(job)

            logger.info(f"Starting job {job.id}: {job.input_path}")

            # Run conversion
            success = self._run_conversion(job)

            if success:
                job.status = JobStatus.COMPLETED
                job.progress = 100.0
                job.completed_at = datetime.utcnow()
                logger.info(f"Job {job.id} completed successfully")
            else:
                # Handle retry logic
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = JobStatus.RETRYING
                    logger.warning(
                        f"Job {job.id} failed, retrying ({job.retry_count}/{job.max_retries})"
                    )

                    # Put back in queue for retry
                    time.sleep(30)  # Wait before retry
                    self.job_queue.put(job)
                else:
                    job.status = JobStatus.FAILED
                    logger.error(f"Job {job.id} failed after {job.max_retries} retries")

            # Update database
            self._update_job_in_db(job)

            # Move to completed jobs
            with self.lock:
                if job.id in self.running_jobs:
                    del self.running_jobs[job.id]
                self.completed_jobs[job.id] = job

        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self._update_job_in_db(job)

    def _run_conversion(self, job: ConversionJob) -> bool:
        """Run the actual HandBrake conversion"""
        try:
            # Execute handbrake2resilio.sh via subprocess
            script_path = "/app/handbrake2resilio.sh"

            # Ensure output directory exists
            os.makedirs(os.path.dirname(job.output_path), exist_ok=True)

            # Build command with proper arguments
            cmd = [
                script_path,
                job.input_path,
                job.output_path,
                str(self.config.resources.max_concurrent_jobs),  # parallel jobs
            ]

            logger.info(f"Starting conversion for job {job.id}: {' '.join(cmd)}")

            # Run conversion with timeout (1 hour)
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=3600, cwd="/app"
            )

            if result.returncode == 0:
                logger.info(f"Conversion successful for job {job.id}")
                return True
            else:
                logger.error(f"Conversion failed for job {job.id}: {result.stderr}")
                job.error_message = result.stderr
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Conversion timeout for job {job.id}")
            job.error_message = "Conversion timed out after 1 hour"
            return False
        except Exception as e:
            logger.error(f"Conversion failed for job {job.id}: {e}")
            job.error_message = str(e)
            return False

    def _update_job_progress(self, job: ConversionJob, progress: float):
        """Update job progress"""
        job.progress = progress
        self._update_job_in_db(job)

    def _update_job_in_db(self, job: ConversionJob):
        """Update job in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO jobs (
                        id, input_path, output_path, quality, resolution,
                        video_bitrate, audio_bitrate, status, progress,
                        error_message, retry_count, max_retries,
                        created_at, started_at, completed_at, estimated_duration
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        job.estimated_duration,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update job in database: {e}")

    def add_job(self, job: ConversionJob) -> bool:
        """Add a new job to the queue"""
        try:
            with self.lock:
                # Check if job already exists
                if job.id in self.running_jobs or job.id in self.completed_jobs:
                    logger.warning(f"Job {job.id} already exists")
                    return False

                # Add to queue
                self.job_queue.put(job)
                self.running_jobs[job.id] = job

                # Save to database
                self._update_job_in_db(job)

                logger.info(f"Added job {job.id} to queue")
                return True

        except Exception as e:
            logger.error(f"Failed to add job {job.id}: {e}")
            return False

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        try:
            with self.lock:
                if job_id in self.running_jobs:
                    job = self.running_jobs[job_id]
                    job.status = JobStatus.CANCELLED
                    self._update_job_in_db(job)

                    # Remove from running jobs
                    del self.running_jobs[job_id]

                    logger.info(f"Cancelled job {job_id}")
                    return True
                else:
                    logger.warning(f"Job {job_id} not found or not running")
                    return False

        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False

    def get_job_status(self, job_id: str) -> Optional[ConversionJob]:
        """Get job status"""
        with self.lock:
            if job_id in self.running_jobs:
                return self.running_jobs[job_id]
            elif job_id in self.completed_jobs:
                return self.completed_jobs[job_id]
            else:
                return None

    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        usage = self.resource_monitor.get_system_usage()

        with self.lock:
            return {
                "queue_size": self.job_queue.qsize(),
                "running_jobs": len(self.running_jobs),
                "completed_jobs": len(self.completed_jobs),
                "system_usage": usage,
                "can_start_job": self.resource_monitor.can_start_job(),
                "optimal_job_count": self.resource_monitor.get_optimal_job_count(),
            }

    def shutdown(self):
        """Shutdown the job queue"""
        logger.info("Shutting down job queue...")
        self.shutdown_event.set()

        # Wait for workers to finish
        for worker in self.worker_threads:
            worker.join(timeout=5)

        logger.info("Job queue shutdown complete")


# Global job queue instance
job_queue = None


def init_job_queue(config):
    """Initialize the global job queue"""
    global job_queue
    job_queue = JobQueue(config, config.storage.database_path)
    return job_queue
