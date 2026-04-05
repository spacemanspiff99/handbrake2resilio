"""E2E test fixtures — requires full Docker stack running.

Usage:
    pytest testing/test_e2e_integration.py -v -m e2e

Skip automatically if Docker stack is not running.
"""
import os
import pytest
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8080")
HB_URL = os.environ.get("HB_URL", "http://localhost:8081")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:7474")


def is_stack_running() -> bool:
    """Check if the Docker stack API gateway is reachable."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_stack():
    """Skip all E2E tests if Docker stack is not running."""
    if not is_stack_running():
        pytest.skip(
            "Docker stack not running — start with: "
            "docker compose -f deployment/docker-compose.yml up -d"
        )
    return {"api_url": API_URL, "hb_url": HB_URL, "frontend_url": FRONTEND_URL}


@pytest.fixture(scope="session")
def api_url(docker_stack):
    """Return the API gateway base URL."""
    return docker_stack["api_url"]


@pytest.fixture(scope="session")
def hb_url(docker_stack):
    """Return the HandBrake service base URL."""
    return docker_stack["hb_url"]


@pytest.fixture(scope="session")
def frontend_url(docker_stack):
    """Return the frontend base URL."""
    return docker_stack["frontend_url"]


@pytest.fixture(scope="session")
def auth_token(api_url):
    """Log in as admin and return a Bearer token for the session."""
    resp = requests.post(
        f"{api_url}/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10,
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Return Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(autouse=False)
def clean_test_jobs(api_url, auth_headers):
    """Clean up test jobs created during a test."""
    yield
    try:
        requests.post(
            f"{api_url}/api/queue/clear",
            headers=auth_headers,
            timeout=5,
        )
    except Exception:
        pass
