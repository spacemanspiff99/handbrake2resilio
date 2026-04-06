"""Shared pytest fixtures for handbrake2resilio test suite."""
from __future__ import annotations

import os
import sys

import pytest

# Ensure repo root is on sys.path so shared.* imports work.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Add service directories so their local imports (e.g. `from auth import …`) work.
_API_GW_DIR = os.path.join(_REPO_ROOT, "api-gateway")
_HB_DIR = os.path.join(_REPO_ROOT, "handbrake-service")
for _d in (_API_GW_DIR, _HB_DIR):
    if _d not in sys.path:
        sys.path.insert(0, _d)

# ---------------------------------------------------------------------------
# Set environment variables needed by shared.config BEFORE any import of it.
# shared/config.py has a module-level `config = load_config()` that tries to
# create /app/* directories and calls sys.exit(1) on failure.  We redirect
# all paths to /tmp so they can be created without elevated permissions.
# ---------------------------------------------------------------------------
os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32chars-minimum!!"
os.environ["DATABASE_PATH"] = "/tmp/handbrake_test_default.db"
os.environ["LOGS_DIRECTORY"] = "/tmp/hb2r_test_logs"
os.environ["TEMP_DIRECTORY"] = "/tmp/hb2r_test_temp"
os.environ["UPLOAD_DIRECTORY"] = "/tmp/hb2r_test_uploads"
os.environ["BACKUP_DIRECTORY"] = "/tmp/hb2r_test_backups"
# Relax resource thresholds so tests pass on CI/sandbox machines with limited disk/memory.
os.environ["MIN_DISK_GB"] = "0.1"
os.environ["MIN_MEMORY_GB"] = "0.1"

# Pre-import shared.config so the module-level load_config() runs NOW (with
# the env vars above) and is cached in sys.modules for all subsequent imports.
import shared.config as _shared_config  # noqa: F401, E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_config(db_path: str):
    """Build a minimal Config object pointing at *db_path* for tests."""
    # Import after env vars are set by the caller.
    from shared.config import (
        Config,
        MonitoringConfig,
        NetworkConfig,
        ResourceConfig,
        SecurityConfig,
        StorageConfig,
        VideoConfig,
    )

    security = SecurityConfig(
        jwt_secret_key="test-secret-key-32chars-minimum!!",
        bcrypt_rounds=10,
    )
    resources = ResourceConfig()
    storage = StorageConfig(
        database_path=db_path,
        logs_directory="/tmp/test_logs",
        temp_directory="/tmp/test_temp",
        upload_directory="/tmp/test_uploads",
        backup_directory="/tmp/test_backups",
    )
    network = NetworkConfig()
    video = VideoConfig()
    monitoring = MonitoringConfig()
    return Config(
        security=security,
        resources=resources,
        storage=storage,
        network=network,
        video=video,
        monitoring=monitoring,
        environment="development",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fast_psutil_cpu_percent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid blocking ``psutil.cpu_percent(interval=1)`` (~1s) in unit tests."""
    import psutil

    monkeypatch.setattr(
        psutil,
        "cpu_percent",
        lambda *args, **kwargs: 25.0,
    )


@pytest.fixture
def tmp_db(tmp_path) -> str:
    """Temporary SQLite database path — isolated per test."""
    return str(tmp_path / "test.db")


@pytest.fixture
def api_client(tmp_db: str, monkeypatch: pytest.MonkeyPatch):
    """Flask test client for api-gateway with an isolated temp DB.

    Reloads the module each time so module-level side-effects (DB init,
    auth service init) run against the per-test temp database.
    """
    # Set env vars BEFORE any import of the gateway module.
    monkeypatch.setenv("DATABASE_PATH", tmp_db)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32chars-minimum!!")
    monkeypatch.setenv("HANDBRAKE_SERVICE_URL", "http://localhost:8081")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("LOGS_DIRECTORY", "/tmp/hb2r_test_logs")
    monkeypatch.setenv("TEMP_DIRECTORY", "/tmp/hb2r_test_temp")
    monkeypatch.setenv("UPLOAD_DIRECTORY", "/tmp/hb2r_test_uploads")
    monkeypatch.setenv("BACKUP_DIRECTORY", "/tmp/hb2r_test_backups")

    # Remove cached modules so the reload picks up fresh env vars.
    for mod_name in list(sys.modules.keys()):
        if "api_gateway_simple" in mod_name or mod_name == "shared.config":
            del sys.modules[mod_name]

    import api_gateway_simple as gw_module  # type: ignore[import]

    # Re-init the job database against the temp path.
    gw_module.init_job_database()
    gw_module.app.config["TESTING"] = True

    with gw_module.app.test_client() as client:
        yield client


@pytest.fixture
def handbrake_client(tmp_db: str, monkeypatch: pytest.MonkeyPatch):
    """Flask test client for handbrake-service with an isolated temp DB."""
    monkeypatch.setenv("DATABASE_PATH", tmp_db)
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32chars-minimum!!")
    monkeypatch.setenv("LOGS_DIRECTORY", "/tmp/hb2r_test_logs")
    monkeypatch.setenv("TEMP_DIRECTORY", "/tmp/hb2r_test_temp")
    monkeypatch.setenv("UPLOAD_DIRECTORY", "/tmp/hb2r_test_uploads")
    monkeypatch.setenv("BACKUP_DIRECTORY", "/tmp/hb2r_test_backups")

    for mod_name in list(sys.modules.keys()):
        if "handbrake_service_simple" in mod_name or mod_name == "shared.config":
            del sys.modules[mod_name]

    import handbrake_service_simple as hb_module  # type: ignore[import]

    hb_module.init_job_database()
    hb_module.app.config["TESTING"] = True

    with hb_module.app.test_client() as client:
        yield client


@pytest.fixture
def auth_token(api_client) -> str:
    """Return a valid JWT token for the default admin user."""
    resp = api_client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200, f"Login failed: {resp.get_json()}"
    return resp.get_json()["token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Authorization header dict with Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# E2E fixtures — require full Docker stack running on configured ports.
# Tests using these fixtures are marked with @pytest.mark.e2e and skip
# automatically when the stack is not reachable.
# ---------------------------------------------------------------------------

import requests as _requests


def _is_stack_running(url: str) -> bool:
    try:
        return _requests.get(f"{url}/health", timeout=5).status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_stack():
    """Skip all E2E tests if Docker stack is not running."""
    api_url = os.environ.get("API_URL", "http://localhost:9080")
    hb_url = os.environ.get("HB_URL", "http://localhost:9081")
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:9474")
    if not _is_stack_running(api_url):
        pytest.skip(
            f"Docker stack not running at {api_url} — "
            "start with: docker compose -f deployment/docker-compose.yml up -d"
        )
    return {"api_url": api_url, "hb_url": hb_url, "frontend_url": frontend_url}


@pytest.fixture(scope="session")
def api_url(docker_stack) -> str:
    """E2E: API gateway base URL."""
    return docker_stack["api_url"]


@pytest.fixture(scope="session")
def hb_url(docker_stack) -> str:
    """E2E: HandBrake service base URL."""
    return docker_stack["hb_url"]


@pytest.fixture(scope="session")
def frontend_url(docker_stack) -> str:
    """E2E: Frontend base URL."""
    return docker_stack["frontend_url"]


@pytest.fixture(scope="session")
def e2e_token(api_url) -> str:
    """E2E: Login as admin and return a Bearer token."""
    resp = _requests.post(
        f"{api_url}/api/auth/login",
        json={"username": "admin", "password": "admin123"},
        timeout=10,
    )
    assert resp.status_code == 200, f"E2E login failed: {resp.text}"
    return resp.json()["token"]


@pytest.fixture(scope="session")
def e2e_auth_headers(e2e_token) -> dict:
    """E2E: Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {e2e_token}"}


@pytest.fixture(autouse=False)
def clean_test_jobs(api_url, e2e_auth_headers):
    """E2E: Clean up test jobs after a test."""
    yield
    try:
        _requests.post(
            f"{api_url}/api/queue/clear",
            headers=e2e_auth_headers,
            timeout=5,
        )
    except Exception:
        pass
