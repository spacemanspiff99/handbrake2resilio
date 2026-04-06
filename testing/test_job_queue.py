"""Unit tests for shared/job_queue.py — ConversionJob, JobStatus, ResourceMonitor."""
from __future__ import annotations

import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch

from shared.job_queue import ConversionJob, JobQueue, JobStatus, ResourceMonitor


class TestJobStatus:
    """Tests for the JobStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All 6 expected status values are defined."""
        expected = {"pending", "running", "completed", "failed", "cancelled", "retrying"}
        actual = {s.value for s in JobStatus}
        assert expected == actual

    def test_status_values_are_strings(self) -> None:
        """Each JobStatus value is a lowercase string."""
        for status in JobStatus:
            assert isinstance(status.value, str)
            assert status.value == status.value.lower()


class TestConversionJob:
    """Tests for the ConversionJob dataclass."""

    def test_creation_with_required_fields(self) -> None:
        """ConversionJob can be created with minimum required fields."""
        job = ConversionJob(id="job1", input_path="/in/a.mp4", output_path="/out/a.mkv")
        assert job.id == "job1"
        assert job.input_path == "/in/a.mp4"
        assert job.output_path == "/out/a.mkv"

    def test_default_status_is_pending(self) -> None:
        """Default status is PENDING."""
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        assert job.status == JobStatus.PENDING

    def test_created_at_auto_set(self) -> None:
        """created_at is automatically set to current UTC time."""
        before = datetime.utcnow()
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        after = datetime.utcnow()
        assert job.created_at is not None
        assert before <= job.created_at <= after

    def test_to_dict_returns_serializable(self) -> None:
        """to_dict() returns a dict with string status and ISO timestamps."""
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        d = job.to_dict()
        assert isinstance(d, dict)
        assert d["status"] == "pending"
        assert isinstance(d["created_at"], str)
        # Should be ISO format — fromisoformat will raise if not
        datetime.fromisoformat(d["created_at"])

    def test_to_dict_null_timestamps_when_not_set(self) -> None:
        """started_at and completed_at are None when not set."""
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        d = job.to_dict()
        assert d["started_at"] is None
        assert d["completed_at"] is None

    def test_default_quality(self) -> None:
        """Default quality is 23."""
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        assert job.quality == 23

    def test_default_progress_is_zero(self) -> None:
        """Default progress is 0.0."""
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        assert job.progress == 0.0

    def test_custom_status_preserved(self) -> None:
        """Status passed at creation is preserved."""
        job = ConversionJob(
            id="j", input_path="/in", output_path="/out", status=JobStatus.RUNNING
        )
        assert job.status == JobStatus.RUNNING

    def test_to_dict_contains_all_core_keys(self) -> None:
        """to_dict() result contains all expected keys."""
        job = ConversionJob(id="j", input_path="/in", output_path="/out")
        d = job.to_dict()
        for key in ("id", "input_path", "output_path", "status", "progress", "created_at"):
            assert key in d, f"Missing key: {key}"


class TestResourceMonitor:
    """Tests for ResourceMonitor system resource checks."""

    @staticmethod
    def _make_monitor() -> ResourceMonitor:
        """Create a ResourceMonitor with a minimal config stub."""

        class FakeResources:
            cpu_limit_percent = 80
            memory_limit_percent = 80
            max_concurrent_jobs = 4

        class FakeConfig:
            resources = FakeResources()

        return ResourceMonitor(FakeConfig())

    def test_get_system_usage_returns_dict(self) -> None:
        """get_system_usage() returns a dict with expected keys."""
        monitor = self._make_monitor()
        usage = monitor.get_system_usage()
        assert isinstance(usage, dict)
        for key in (
            "cpu_percent",
            "memory_percent",
            "memory_available_gb",
            "disk_percent",
            "disk_free_gb",
        ):
            assert key in usage, f"Missing key: {key}"

    def test_get_system_usage_values_are_numbers(self) -> None:
        """All usage values are numeric."""
        monitor = self._make_monitor()
        usage = monitor.get_system_usage()
        for key, val in usage.items():
            assert isinstance(val, (int, float)), f"{key} is not numeric: {val}"

    def test_can_start_job_returns_bool(self) -> None:
        """can_start_job() returns a boolean."""
        monitor = self._make_monitor()
        result = monitor.can_start_job()
        assert isinstance(result, bool)

    def test_get_optimal_job_count_positive(self) -> None:
        """get_optimal_job_count() returns a positive integer."""
        from unittest.mock import patch

        monitor = self._make_monitor()
        # psutil.cpu_count() may raise PermissionError in sandboxed environments;
        # patch it to a known value so the test is environment-independent.
        with patch("psutil.cpu_count", return_value=4):
            count = monitor.get_optimal_job_count()
        assert isinstance(count, int)
        assert count >= 1


class TestJobQueue:
    """Tests for JobQueue with worker threads disabled."""

    @staticmethod
    def _fake_config(db_path: str):
        class FakeResources:
            cpu_limit_percent = 80
            memory_limit_percent = 80
            max_concurrent_jobs = 2

        class FakeStorage:
            database_path = db_path

        class FakeConfig:
            resources = FakeResources()
            storage = FakeStorage()

        return FakeConfig()

    @patch.object(JobQueue, "_start_workers", lambda self: None)
    def test_init_creates_database_and_queue_status(self, tmp_path) -> None:
        """JobQueue initializes DB and reports empty queue."""
        db_path = str(tmp_path / "jq.db")
        cfg = self._fake_config(db_path)
        jq = JobQueue(cfg, db_path)
        try:
            status = jq.get_queue_status()
            assert status["queue_size"] == 0
            assert status["running_jobs"] == 0
        finally:
            jq.shutdown()

    @patch.object(JobQueue, "_start_workers", lambda self: None)
    def test_add_job_increases_queue(self, tmp_path) -> None:
        """add_job enqueues a ConversionJob."""
        db_path = str(tmp_path / "jq2.db")
        cfg = self._fake_config(db_path)
        jq = JobQueue(cfg, db_path)
        try:
            job = ConversionJob(
                id="jid-1",
                input_path="/in/a.mp4",
                output_path="/out/a.mkv",
            )
            assert jq.add_job(job) is True
            assert jq.get_queue_status()["queue_size"] >= 1
        finally:
            jq.shutdown()
