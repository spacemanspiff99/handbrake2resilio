"""Unit tests for handbrake-service/handbrake_service_simple.py."""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "handbrake-service"
    ),
)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, handbrake_client) -> None:
        """Health endpoint returns 200 with expected keys."""
        resp = handbrake_client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "system" in data
        assert "active_jobs" in data

    def test_health_service_name(self, handbrake_client) -> None:
        """Health response identifies the service as 'handbrake'."""
        resp = handbrake_client.get("/health")
        data = resp.get_json()
        assert data.get("service") == "handbrake"


class TestConvertEndpoint:
    """Tests for POST /convert."""

    def test_missing_input_path_returns_400(self, handbrake_client) -> None:
        """Request without input_path returns 400."""
        resp = handbrake_client.post(
            "/convert", json={"output_path": "/media/output/out.mkv"}
        )
        assert resp.status_code == 400

    def test_invalid_input_path_returns_400(self, handbrake_client) -> None:
        """Path outside /media/input is rejected with 400."""
        resp = handbrake_client.post("/convert", json={"input_path": "/etc/passwd"})
        assert resp.status_code == 400

    def test_path_traversal_rejected(self, handbrake_client) -> None:
        """Path with .. segment is rejected with 400."""
        resp = handbrake_client.post(
            "/convert", json={"input_path": "/media/input/../etc/passwd"}
        )
        assert resp.status_code == 400

    @patch("handbrake_service_simple.subprocess.Popen")
    @patch("handbrake_service_simple.can_start_job", return_value=True)
    def test_valid_convert_returns_job_id(
        self, _mock_can, mock_popen, handbrake_client
    ) -> None:
        """Valid input_path under /media/input starts a job and returns job_id."""
        mock_proc = MagicMock()
        mock_proc.stdout.readline.return_value = ""
        mock_proc.poll.return_value = 0
        mock_popen.return_value = mock_proc

        resp = handbrake_client.post(
            "/convert",
            json={
                "input_path": "/media/input/test.mp4",
                "output_path": "/media/output/test.mkv",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "job_id" in data

    @patch("handbrake_service_simple.can_start_job", return_value=False)
    def test_system_overloaded_returns_503(self, _mock, handbrake_client) -> None:
        """Returns 503 when system resources are at capacity."""
        resp = handbrake_client.post(
            "/convert",
            json={"input_path": "/media/input/test.mp4"},
        )
        assert resp.status_code == 503


class TestJobManagement:
    """Tests for job status, listing, cancellation, and deletion endpoints."""

    def test_get_nonexistent_job_returns_404(self, handbrake_client) -> None:
        """GET /job/<id> for unknown job returns 404."""
        resp = handbrake_client.get("/job/nonexistent-id")
        assert resp.status_code == 404

    def test_list_jobs_returns_list(self, handbrake_client) -> None:
        """GET /jobs returns a response with a 'jobs' list."""
        resp = handbrake_client.get("/jobs")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "jobs" in data
        assert isinstance(data["jobs"], list)

    def test_cancel_nonexistent_job_returns_404(self, handbrake_client) -> None:
        """POST /cancel/<id> for unknown job returns 404."""
        resp = handbrake_client.post("/cancel/nonexistent-id")
        assert resp.status_code == 404

    def test_delete_nonexistent_job_returns_404(self, handbrake_client) -> None:
        """DELETE /jobs/<id> for unknown job returns 404."""
        resp = handbrake_client.delete("/jobs/nonexistent-id")
        assert resp.status_code == 404

    def test_root_endpoint_returns_200(self, handbrake_client) -> None:
        """GET / returns 200 with service info."""
        resp = handbrake_client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "service" in data


class TestValidateInputPath:
    """Tests for the validate_input_path helper function."""

    def test_valid_path_under_media_input(self) -> None:
        """Path under /media/input is valid."""
        from handbrake_service_simple import validate_input_path  # type: ignore[import]

        assert validate_input_path("/media/input/video.mp4") is True

    def test_exact_media_input_root(self) -> None:
        """Exact /media/input path is valid."""
        from handbrake_service_simple import validate_input_path  # type: ignore[import]

        assert validate_input_path("/media/input") is True

    def test_path_outside_media_input_invalid(self) -> None:
        """Path outside /media/input is invalid."""
        from handbrake_service_simple import validate_input_path  # type: ignore[import]

        assert validate_input_path("/etc/passwd") is False

    def test_path_traversal_invalid(self) -> None:
        """Path with .. is invalid."""
        from handbrake_service_simple import validate_input_path  # type: ignore[import]

        assert validate_input_path("/media/input/../etc/passwd") is False

    def test_empty_string_invalid(self) -> None:
        """Empty string is invalid."""
        from handbrake_service_simple import validate_input_path  # type: ignore[import]

        assert validate_input_path("") is False

    def test_none_invalid(self) -> None:
        """None is invalid."""
        from handbrake_service_simple import validate_input_path  # type: ignore[import]

        assert validate_input_path(None) is False  # type: ignore[arg-type]
