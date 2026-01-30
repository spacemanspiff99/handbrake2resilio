#!/usr/bin/env python3
"""
Unit tests for job queue system
"""

import os
import tempfile
import unittest
import threading
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

from job_queue import JobQueue, ResourceMonitor, ConversionJob, JobStatus


class TestResourceMonitor(unittest.TestCase):
    """Test resource monitoring"""

    def setUp(self):
        """Set up test environment"""
        self.config = MagicMock()
        self.config.resources.cpu_limit_percent = 80
        self.config.resources.memory_limit_percent = 80
        self.config.resources.max_concurrent_jobs = 8

        self.monitor = ResourceMonitor(self.config)

    @patch("job_queue.psutil.cpu_percent")
    @patch("job_queue.psutil.virtual_memory")
    @patch("job_queue.psutil.disk_usage")
    def test_get_system_usage(self, mock_disk, mock_memory, mock_cpu):
        """Test system usage monitoring"""
        # Mock system resources
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(
            percent=65.2, available=4 * 1024**3  # 4GB available
        )
        mock_disk.return_value = MagicMock(percent=75.0, free=10 * 1024**3)  # 10GB free

        usage = self.monitor.get_system_usage()

        self.assertEqual(usage["cpu_percent"], 45.5)
        self.assertEqual(usage["memory_percent"], 65.2)
        self.assertEqual(usage["memory_available_gb"], 4.0)
        self.assertEqual(usage["disk_percent"], 75.0)
        self.assertEqual(usage["disk_free_gb"], 10.0)

    @patch("job_queue.psutil.cpu_percent")
    @patch("job_queue.psutil.virtual_memory")
    @patch("job_queue.psutil.disk_usage")
    def test_can_start_job_under_limits(self, mock_disk, mock_memory, mock_cpu):
        """Test job start when under resource limits"""
        # Mock system resources under limits
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(
            percent=60.0, available=3 * 1024**3  # 3GB available
        )
        mock_disk.return_value = MagicMock(percent=70.0, free=8 * 1024**3)  # 8GB free

        can_start = self.monitor.can_start_job()

        self.assertTrue(can_start)

    @patch("job_queue.psutil.cpu_percent")
    @patch("job_queue.psutil.virtual_memory")
    @patch("job_queue.psutil.disk_usage")
    def test_can_start_job_over_cpu_limit(self, mock_disk, mock_memory, mock_cpu):
        """Test job start when over CPU limit"""
        # Mock system resources over CPU limit
        mock_cpu.return_value = 85.0
        mock_memory.return_value = MagicMock(percent=60.0, available=3 * 1024**3)
        mock_disk.return_value = MagicMock(percent=70.0, free=8 * 1024**3)

        can_start = self.monitor.can_start_job()

        self.assertFalse(can_start)

    @patch("job_queue.psutil.cpu_percent")
    @patch("job_queue.psutil.virtual_memory")
    @patch("job_queue.psutil.disk_usage")
    def test_can_start_job_low_memory(self, mock_disk, mock_memory, mock_cpu):
        """Test job start when memory is low"""
        # Mock system resources with low memory
        mock_cpu.return_value = 50.0
        mock_memory.return_value = MagicMock(
            percent=60.0, available=1 * 1024**3  # 1GB available (below 2GB minimum)
        )
        mock_disk.return_value = MagicMock(percent=70.0, free=8 * 1024**3)

        can_start = self.monitor.can_start_job()

        self.assertFalse(can_start)

    @patch("job_queue.psutil.cpu_count")
    @patch("job_queue.psutil.cpu_percent")
    def test_get_optimal_job_count(self, mock_cpu_percent, mock_cpu_count):
        """Test optimal job count calculation"""
        mock_cpu_count.return_value = 8

        # Test with low CPU usage
        mock_cpu_percent.return_value = 30.0
        optimal = self.monitor.get_optimal_job_count()
        self.assertEqual(optimal, 8)  # Should use all cores

        # Test with high CPU usage
        mock_cpu_percent.return_value = 80.0
        optimal = self.monitor.get_optimal_job_count()
        self.assertEqual(optimal, 2)  # Should use half cores


class TestConversionJob(unittest.TestCase):
    """Test conversion job data structure"""

    def test_job_creation(self):
        """Test job creation with default values"""
        job = ConversionJob(
            id="test-job-1",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )

        self.assertEqual(job.id, "test-job-1")
        self.assertEqual(job.input_path, "/test/input.mkv")
        self.assertEqual(job.output_path, "/test/output.mp4")
        self.assertEqual(job.status, JobStatus.PENDING)
        self.assertEqual(job.progress, 0.0)
        self.assertEqual(job.retry_count, 0)
        self.assertEqual(job.max_retries, 3)
        self.assertIsNotNone(job.created_at)

    def test_job_creation_with_custom_values(self):
        """Test job creation with custom values"""
        job = ConversionJob(
            id="test-job-2",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
            quality=20,
            resolution="1080x720",
            video_bitrate=2000,
            audio_bitrate=128,
            max_retries=5,
        )

        self.assertEqual(job.quality, 20)
        self.assertEqual(job.resolution, "1080x720")
        self.assertEqual(job.video_bitrate, 2000)
        self.assertEqual(job.audio_bitrate, 128)
        self.assertEqual(job.max_retries, 5)

    def test_job_to_dict(self):
        """Test job serialization"""
        job = ConversionJob(
            id="test-job-3",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )

        job_dict = job.to_dict()

        self.assertEqual(job_dict["id"], "test-job-3")
        self.assertEqual(job_dict["status"], "pending")
        self.assertIn("created_at", job_dict)
        self.assertIsInstance(job_dict["created_at"], str)


class TestJobQueue(unittest.TestCase):
    """Test job queue functionality"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_jobs.db")

        self.config = MagicMock()
        self.config.storage.database_path = self.db_path
        self.config.resources.cpu_limit_percent = 80
        self.config.resources.memory_limit_percent = 80
        self.config.resources.max_concurrent_jobs = 2

        self.job_queue = JobQueue(self.config, self.db_path)

    def tearDown(self):
        """Clean up test environment"""
        self.job_queue.shutdown()
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_job_queue_initialization(self):
        """Test job queue initialization"""
        self.assertIsNotNone(self.job_queue)
        self.assertEqual(len(self.job_queue.worker_threads), 2)  # Based on config

    def test_add_job(self):
        """Test adding job to queue"""
        job = ConversionJob(
            id="test-job-1",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )

        success = self.job_queue.add_job(job)

        self.assertTrue(success)
        self.assertIn("test-job-1", self.job_queue.running_jobs)

    def test_add_duplicate_job(self):
        """Test adding duplicate job"""
        job = ConversionJob(
            id="test-job-1",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )

        # Add job first time
        success1 = self.job_queue.add_job(job)
        self.assertTrue(success1)

        # Try to add same job again
        success2 = self.job_queue.add_job(job)
        self.assertFalse(success2)

    def test_get_job_status(self):
        """Test getting job status"""
        job = ConversionJob(
            id="test-job-1",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )

        self.job_queue.add_job(job)

        retrieved_job = self.job_queue.get_job_status("test-job-1")

        self.assertIsNotNone(retrieved_job)
        self.assertEqual(retrieved_job.id, "test-job-1")

    def test_get_job_status_nonexistent(self):
        """Test getting status of nonexistent job"""
        job = self.job_queue.get_job_status("nonexistent-job")

        self.assertIsNone(job)

    def test_cancel_job(self):
        """Test job cancellation"""
        job = ConversionJob(
            id="test-job-1",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )

        self.job_queue.add_job(job)

        success = self.job_queue.cancel_job("test-job-1")

        self.assertTrue(success)
        self.assertNotIn("test-job-1", self.job_queue.running_jobs)

    def test_cancel_nonexistent_job(self):
        """Test cancelling nonexistent job"""
        success = self.job_queue.cancel_job("nonexistent-job")

        self.assertFalse(success)

    def test_get_queue_status(self):
        """Test getting queue status"""
        # Add a job
        job = ConversionJob(
            id="test-job-1",
            input_path="/test/input.mkv",
            output_path="/test/output.mp4",
        )
        self.job_queue.add_job(job)

        status = self.job_queue.get_queue_status()

        self.assertIn("queue_size", status)
        self.assertIn("running_jobs", status)
        self.assertIn("completed_jobs", status)
        self.assertIn("system_usage", status)
        self.assertIn("can_start_job", status)
        self.assertIn("optimal_job_count", status)

        self.assertEqual(status["running_jobs"], 1)

    @patch("job_queue.psutil.cpu_percent")
    @patch("job_queue.psutil.virtual_memory")
    @patch("job_queue.psutil.disk_usage")
    def test_resource_based_throttling(self, mock_disk, mock_memory, mock_cpu):
        """Test resource-based job throttling"""
        # Mock high resource usage
        mock_cpu.return_value = 90.0
        mock_memory.return_value = MagicMock(percent=85.0, available=1 * 1024**3)
        mock_disk.return_value = MagicMock(percent=80.0, free=3 * 1024**3)

        can_start = self.job_queue.resource_monitor.can_start_job()

        self.assertFalse(can_start)


if __name__ == "__main__":
    unittest.main()
