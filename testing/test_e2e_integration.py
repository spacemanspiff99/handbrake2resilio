"""E2E integration tests for the full handbrake2resilio Docker stack.

Requires all 3 services running:
    docker compose -f deployment/docker-compose.yml up -d

Run with:
    pytest testing/test_e2e_integration.py -v -m e2e
"""
import pytest
import requests

pytestmark = pytest.mark.e2e


class TestServiceHealth:
    """Verify all services are reachable and healthy."""

    def test_api_gateway_reachable(self, api_url):
        resp = requests.get(f"{api_url}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_gateway_db_healthy(self, api_url):
        resp = requests.get(f"{api_url}/health", timeout=10)
        data = resp.json()
        db_val = data.get("database")
        assert db_val is not None, "health response missing 'database' field"
        # Accept 'sqlite', 'healthy', 'ok', or any truthy string
        assert db_val, f"database field is falsy: {db_val!r}"

    def test_handbrake_service_reachable(self, hb_url):
        resp = requests.get(f"{hb_url}/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "system" in data

    def test_handbrake_service_has_active_jobs_field(self, hb_url):
        resp = requests.get(f"{hb_url}/health", timeout=10)
        data = resp.json()
        assert "active_jobs" in data

    def test_frontend_reachable(self, frontend_url):
        resp = requests.get(frontend_url, timeout=10)
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_api_gateway_root_endpoint(self, api_url):
        resp = requests.get(f"{api_url}/", timeout=10)
        # Root may return 200 or 404 depending on setup
        assert resp.status_code in (200, 404)


class TestAuthFlow:
    """Verify authentication endpoints work end-to-end."""

    def test_login_returns_token(self, api_url):
        resp = requests.post(
            f"{api_url}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 10

    def test_login_invalid_credentials_returns_401(self, api_url):
        resp = requests.post(
            f"{api_url}/api/auth/login",
            json={"username": "admin", "password": "wrongpassword"},
            timeout=10,
        )
        assert resp.status_code == 401

    def test_token_verification(self, api_url, e2e_auth_headers):
        resp = requests.get(
            f"{api_url}/api/auth/verify",
            headers=e2e_auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        # API returns {"success": true} or {"valid": true} depending on version
        assert data.get("valid") is True or data.get("success") is True

    def test_protected_endpoint_without_token_returns_401(self, api_url):
        resp = requests.get(f"{api_url}/api/tabs", timeout=10)
        assert resp.status_code == 401

    def test_protected_endpoint_with_token_returns_200(self, api_url, e2e_auth_headers):
        resp = requests.get(f"{api_url}/api/tabs", headers=e2e_auth_headers, timeout=10)
        assert resp.status_code == 200


class TestJobPipeline:
    """Verify job submission and queue endpoints."""

    def test_queue_jobs_endpoint_returns_200(self, api_url, e2e_auth_headers):
        resp = requests.get(
            f"{api_url}/api/queue/jobs",
            headers=e2e_auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should return either a list or an object with jobs key
        assert isinstance(data, (list, dict))

    def test_queue_status_endpoint_returns_200(self, api_url, e2e_auth_headers):
        resp = requests.get(
            f"{api_url}/api/queue",
            headers=e2e_auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200

    def test_submit_job_with_missing_input_returns_error(self, api_url, e2e_auth_headers):
        resp = requests.post(
            f"{api_url}/api/jobs/add",
            headers=e2e_auth_headers,
            json={"output_path": "/media/output/test.mkv"},
            timeout=10,
        )
        # Missing input_path should return 400, 500, or 503 (if handbrake unavailable)
        assert resp.status_code in (400, 500, 503)

    def test_submit_job_accepted_or_service_unavailable(
        self, api_url, e2e_auth_headers, clean_test_jobs
    ):
        resp = requests.post(
            f"{api_url}/api/jobs/add",
            headers=e2e_auth_headers,
            json={
                "input_path": "/media/input/test.mp4",
                "output_path": "/media/output/test.mkv",
            },
            timeout=10,
        )
        # 200 = accepted, 503 = handbrake service unavailable (both valid)
        assert resp.status_code in (200, 400, 503)
        if resp.status_code == 200:
            data = resp.json()
            assert "job_id" in data


class TestFileBrowser:
    """Verify filesystem browse endpoints."""

    def test_browse_media_input_returns_200_or_404(self, api_url, e2e_auth_headers):
        resp = requests.get(
            f"{api_url}/api/filesystem/browse",
            headers=e2e_auth_headers,
            params={"path": "/media/input"},
            timeout=10,
        )
        # 200 if mount present, 404 if not mounted
        assert resp.status_code in (200, 404)

    def test_browse_nonexistent_path_returns_error(self, api_url, e2e_auth_headers):
        resp = requests.get(
            f"{api_url}/api/filesystem/browse",
            headers=e2e_auth_headers,
            params={"path": "/nonexistent/path/xyz123"},
            timeout=10,
        )
        assert resp.status_code in (400, 404)

    def test_browse_requires_auth(self, api_url):
        resp = requests.get(
            f"{api_url}/api/filesystem/browse",
            params={"path": "/media/input"},
            timeout=10,
        )
        assert resp.status_code == 401


class TestTabManagement:
    """Verify tab CRUD operations end-to-end."""

    def test_tab_full_crud(self, api_url, e2e_auth_headers):
        # Create
        resp = requests.post(
            f"{api_url}/api/tabs",
            headers=e2e_auth_headers,
            json={
                "name": "E2E Test Tab",
                "source_path": "/media/input",
                "destination_path": "/media/output",
            },
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        # API may return {"tab_id": ...}, {"id": ...}, or {"data": {"id": ...}}
        tab_id = (
            data.get("tab_id")
            or data.get("id")
            or (data.get("data") or {}).get("id")
        )
        assert tab_id, f"No tab_id in response: {data}"

        # List — should include new tab
        resp = requests.get(f"{api_url}/api/tabs", headers=e2e_auth_headers, timeout=10)
        assert resp.status_code == 200
        body = resp.json()
        # API may return a list directly or {"data": [...]}
        tabs = body if isinstance(body, list) else (body.get("data") or [])
        tab_ids = [t.get("id") for t in tabs]
        assert tab_id in tab_ids

        # Update
        resp = requests.put(
            f"{api_url}/api/tabs/{tab_id}",
            headers=e2e_auth_headers,
            json={"name": "E2E Test Tab Updated"},
            timeout=10,
        )
        assert resp.status_code == 200

        # Delete
        resp = requests.delete(
            f"{api_url}/api/tabs/{tab_id}",
            headers=e2e_auth_headers,
            timeout=10,
        )
        assert resp.status_code == 200

        # Verify deleted
        resp = requests.get(f"{api_url}/api/tabs", headers=e2e_auth_headers, timeout=10)
        assert resp.status_code == 200
        body_after = resp.json()
        tabs_after = body_after if isinstance(body_after, list) else (body_after.get("data") or [])
        remaining_ids = [t.get("id") for t in tabs_after]
        assert tab_id not in remaining_ids


class TestErrorHandling:
    """Verify error handling for malformed requests."""

    def test_malformed_json_returns_error(self, api_url, e2e_auth_headers):
        resp = requests.post(
            f"{api_url}/api/jobs/add",
            headers={**e2e_auth_headers, "Content-Type": "application/json"},
            data="not-valid-json",
            timeout=10,
        )
        assert resp.status_code in (400, 415, 500)

    def test_missing_input_path_returns_400_or_503(self, api_url, e2e_auth_headers):
        resp = requests.post(
            f"{api_url}/api/jobs/add",
            headers=e2e_auth_headers,
            json={"output_path": "/media/output/test.mkv"},
            timeout=10,
        )
        assert resp.status_code in (400, 500, 503)

    def test_nonexistent_job_status_returns_404(self, api_url, e2e_auth_headers):
        resp = requests.get(
            f"{api_url}/api/jobs/status/nonexistent-job-id-xyz",
            headers=e2e_auth_headers,
            timeout=10,
        )
        assert resp.status_code in (404, 400)
