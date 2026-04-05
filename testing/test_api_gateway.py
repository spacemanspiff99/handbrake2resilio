"""Unit tests for api-gateway/api_gateway_simple.py."""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api-gateway"
    ),
)


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, api_client) -> None:
        """Health endpoint returns 200."""
        resp = api_client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_key(self, api_client) -> None:
        """Health response contains a 'status' key."""
        resp = api_client.get("/health")
        data = resp.get_json()
        assert "status" in data or "service" in data


class TestAuthEndpoints:
    """Tests for /api/auth/* endpoints."""

    def test_login_valid_credentials(self, api_client) -> None:
        """POST /api/auth/login with valid creds returns 200 and token."""
        resp = api_client.post(
            "/api/auth/login", json={"username": "admin", "password": "admin123"}
        )
        assert resp.status_code == 200
        assert "token" in resp.get_json()

    def test_login_invalid_credentials(self, api_client) -> None:
        """POST /api/auth/login with wrong password returns 401."""
        resp = api_client.post(
            "/api/auth/login", json={"username": "admin", "password": "wrongpass"}
        )
        assert resp.status_code == 401

    def test_login_missing_fields_returns_400(self, api_client) -> None:
        """POST /api/auth/login without credentials returns 400."""
        resp = api_client.post("/api/auth/login", json={})
        assert resp.status_code == 400

    def test_register_new_user(self, api_client) -> None:
        """POST /api/auth/register with new user returns 200."""
        resp = api_client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "newpass123"},
        )
        assert resp.status_code == 200

    def test_register_duplicate_username(self, api_client) -> None:
        """POST /api/auth/register with duplicate username returns 400."""
        api_client.post(
            "/api/auth/register",
            json={"username": "dupuser", "password": "pass123"},
        )
        resp = api_client.post(
            "/api/auth/register",
            json={"username": "dupuser", "password": "pass123"},
        )
        assert resp.status_code == 400

    def test_verify_valid_token(self, api_client, auth_headers) -> None:
        """GET /api/auth/verify with valid token returns 200."""
        resp = api_client.get("/api/auth/verify", headers=auth_headers)
        assert resp.status_code == 200

    def test_verify_no_token_returns_401(self, api_client) -> None:
        """GET /api/auth/verify without token returns 401."""
        resp = api_client.get("/api/auth/verify")
        assert resp.status_code == 401

    def test_verify_invalid_token_returns_401(self, api_client) -> None:
        """GET /api/auth/verify with garbage token returns 401."""
        resp = api_client.get(
            "/api/auth/verify",
            headers={"Authorization": "Bearer not.a.real.token"},
        )
        assert resp.status_code == 401


class TestTabEndpoints:
    """Tests for /api/tabs/* endpoints."""

    def test_get_tabs_requires_auth(self, api_client) -> None:
        """GET /api/tabs without auth returns 401."""
        resp = api_client.get("/api/tabs")
        assert resp.status_code == 401

    def test_get_tabs_with_auth(self, api_client, auth_headers) -> None:
        """GET /api/tabs with valid auth returns 200."""
        resp = api_client.get("/api/tabs", headers=auth_headers)
        assert resp.status_code == 200

    def test_create_tab(self, api_client, auth_headers) -> None:
        """POST /api/tabs creates a tab and returns 200."""
        resp = api_client.post(
            "/api/tabs",
            headers=auth_headers,
            json={
                "name": "Test Tab",
                "source_path": "/in",
                "destination_path": "/out",
            },
        )
        assert resp.status_code == 200

    def test_create_tab_returns_tab_data(self, api_client, auth_headers) -> None:
        """POST /api/tabs returns the created tab with an id."""
        resp = api_client.post(
            "/api/tabs",
            headers=auth_headers,
            json={
                "name": "Data Tab",
                "source_path": "/src",
                "destination_path": "/dst",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get("success") is True
        assert "data" in data

    def test_tab_crud_full(self, api_client, auth_headers) -> None:
        """Full CRUD cycle: create → update → delete."""
        # Create
        resp = api_client.post(
            "/api/tabs",
            headers=auth_headers,
            json={
                "name": "CRUD Tab",
                "source_path": "/in",
                "destination_path": "/out",
            },
        )
        assert resp.status_code == 200
        tab_data = resp.get_json().get("data", {})
        tab_id = tab_data.get("id") or tab_data.get("tab_id")
        assert tab_id is not None

        # Update
        resp = api_client.put(
            f"/api/tabs/{tab_id}",
            headers=auth_headers,
            json={"name": "Updated Tab"},
        )
        assert resp.status_code == 200

        # Delete
        resp = api_client.delete(f"/api/tabs/{tab_id}", headers=auth_headers)
        assert resp.status_code == 200


class TestQueueEndpoints:
    """Tests for /api/queue/* endpoints."""

    def test_get_queue_status(self, api_client, auth_headers) -> None:
        """GET /api/queue returns 200 with queue data."""
        resp = api_client.get("/api/queue", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "success" in data or "data" in data

    def test_get_all_jobs(self, api_client, auth_headers) -> None:
        """GET /api/queue/jobs returns 200 with jobs list."""
        resp = api_client.get("/api/queue/jobs", headers=auth_headers)
        assert resp.status_code == 200

    def test_list_jobs_endpoint(self, api_client) -> None:
        """GET /api/jobs/list returns 200 with jobs and count."""
        resp = api_client.get("/api/jobs/list")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "jobs" in data
        assert "count" in data

    def test_get_nonexistent_job_status(self, api_client) -> None:
        """GET /api/jobs/status/<id> for unknown job returns 404."""
        resp = api_client.get("/api/jobs/status/nonexistent-job-id")
        assert resp.status_code == 404

    def test_clear_completed_jobs(self, api_client) -> None:
        """POST /api/queue/clear returns 200."""
        resp = api_client.post("/api/queue/clear")
        assert resp.status_code == 200

    def test_pause_queue(self, api_client) -> None:
        """POST /api/queue/pause returns 200."""
        resp = api_client.post("/api/queue/pause")
        assert resp.status_code == 200

    def test_resume_queue(self, api_client) -> None:
        """POST /api/queue/resume returns 200."""
        resp = api_client.post("/api/queue/resume")
        assert resp.status_code == 200
