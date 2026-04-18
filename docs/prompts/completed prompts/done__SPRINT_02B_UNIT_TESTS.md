# SPRINT_02B — Comprehensive Unit Tests (WEA-124, WEA-125)

💣

## Rules Reference
`.cursor/rules/rules.mdc` — DRY/SRP, Python type hints, docstrings, no side effects between tests.

## Model Recommendation
**Composer 2 / Auto** (no API cost — Python file edits, no browser testing)

## Personas (in sequence)
1. **Backend Engineer** — understand service interfaces, write test fixtures
2. **QA Engineer** — write comprehensive positive + negative test cases, verify coverage

---

## Context

### Existing test files (to be replaced/expanded)
- `api-gateway/unit-tests/test_auth.py` — auth tests (may be outdated)
- `shared/unit-tests/test_config.py`
- `shared/unit-tests/test_db.py`
- `shared/unit-tests/test_job_queue.py`

### Target: new `testing/` folder at repo root
WEA-124 and WEA-125 both reference `testing/` as the target directory. Create this folder with a flat structure:
```
testing/
  conftest.py          ← shared fixtures
  test_api_gateway.py  ← WEA-124
  test_handbrake_service.py  ← WEA-124
  test_config.py       ← WEA-125
  test_job_queue.py    ← WEA-125
  test_auth.py         ← WEA-125
  test_db.py           ← WEA-125
```

### Key source files
- `api-gateway/api_gateway_simple.py` — Flask app, 1221 lines
- `api-gateway/auth.py` — auth module
- `handbrake-service/handbrake_service_simple.py` — HandBrake Flask service
- `shared/config.py` — config loading
- `shared/job_queue.py` — JobQueue, ConversionJob, ResourceMonitor, JobStatus
- `shared/db.py` — SQLite helpers (get_db_connection, commit_with_retry, execute_with_retry)

---

## Issue: WEA-124 — Backend unit tests (api-gateway + handbrake-service)

### Task 1 — `testing/conftest.py`

Create shared fixtures:
```python
"""Shared pytest fixtures for handbrake2resilio test suite."""
import os
import sys
import pytest
import tempfile

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def tmp_db(tmp_path):
    """Temporary SQLite database path."""
    return str(tmp_path / "test.db")

@pytest.fixture
def api_client(tmp_db, monkeypatch):
    """Flask test client for api-gateway."""
    monkeypatch.setenv("DATABASE_PATH", tmp_db)
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-32chars-minimum!!")
    monkeypatch.setenv("HANDBRAKE_SERVICE_URL", "http://localhost:8081")
    from api_gateway.api_gateway_simple import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def handbrake_client(tmp_db, monkeypatch):
    """Flask test client for handbrake-service."""
    monkeypatch.setenv("DATABASE_PATH", tmp_db)
    from handbrake_service.handbrake_service_simple import app, init_job_database
    init_job_database()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_token(api_client):
    """Get a valid JWT token for admin user."""
    resp = api_client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    return resp.get_json()["token"]
```

### Task 2 — `testing/test_api_gateway.py`

Write tests for all endpoints listed in WEA-124. Key patterns:
- Use `api_client` fixture (Flask test client)
- Use `auth_token` fixture for protected endpoints
- Mock `requests.post/get` for HandBrake service calls using `unittest.mock.patch`
- Use in-memory SQLite (via `tmp_db` fixture)

Required test groups:
1. **Health** — GET /health → 200, has `service`, `timestamp`, `database` keys
2. **Auth login** — valid → 200 + token; invalid → 401
3. **Auth register** — new user → 200; duplicate → 400
4. **Auth verify** — valid token → 200; no token → 401
5. **Jobs** — POST /api/jobs/add → 200 + job_id (mock handbrake); GET /api/jobs/status/:id; GET /api/queue/jobs; POST /api/jobs/cancel/:id; DELETE /api/jobs/:id
6. **Tabs** — GET/POST/PUT/DELETE /api/tabs (all require auth)
7. **Filesystem** — GET /api/filesystem/browse; POST /api/filesystem/scan; GET /api/filesystem/browse?path=/nonexistent → 404
8. **Queue** — GET /api/queue; GET /api/queue/jobs; POST /api/queue/clear

### Task 3 — `testing/test_handbrake_service.py`

Write tests for handbrake-service endpoints. Key patterns:
- Use `handbrake_client` fixture
- Mock `subprocess.Popen` to avoid actual HandBrake calls
- Use `tmp_path` for temp input/output files

Required test groups:
1. **Health** — GET /health → 200, has `system`, `active_jobs` keys
2. **Convert** — POST /convert with valid input_path under /media/input → 200 + job_id (mock Popen); missing input_path → 400; system overloaded (mock can_start_job) → 503
3. **Job management** — GET /job/:id; GET /jobs; POST /cancel/:id; DELETE /jobs/:id
4. **System usage** — `get_system_usage()` returns dict with cpu_percent, memory_percent
5. **Resource gating** — `can_start_job()` returns False when mocked resources exhausted

---

## Issue: WEA-125 — Shared module unit tests

### Task 4 — `testing/test_config.py`

Test `shared/config.py`:
1. Default loading with no env vars → valid defaults
2. `MAX_CONCURRENT_JOBS=10` env var → config value changes
3. Invalid `BCRYPT_ROUNDS=50` → raises ValueError (if validation exists)
4. `to_dict()` → does not include `jwt_secret_key`
5. `validate_system_requirements()` → returns True on test machine

### Task 5 — `testing/test_job_queue.py`

Test `shared/job_queue.py`:
1. `ConversionJob` creation → defaults, `created_at` set
2. `ConversionJob.to_dict()` → serializable, ISO timestamps
3. `JobStatus` enum → all 6 values exist (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, RETRYING)
4. `ResourceMonitor.get_system_usage()` → dict with cpu_percent, memory_percent, disk_free_gb
5. `ResourceMonitor.can_start_job()` → True when resources available
6. `ResourceMonitor.get_optimal_job_count()` → positive integer

Note: `JobQueue` requires a `config` object — mock it or create a minimal config stub.

### Task 6 — `testing/test_auth.py`

Test `api-gateway/auth.py`:
1. DB init → creates users, sessions, tabs tables
2. Default admin → created with correct credentials
3. Register user → new user with hashed password
4. Register duplicate → returns False
5. Authenticate valid → returns user info dict
6. Authenticate invalid password → returns None
7. Authenticate inactive user → returns None
8. Create token → returns valid JWT string
9. Verify token → decodes to correct user info
10. Verify expired token → returns None
11. Change password → updates hash, old password no longer works
12. Tab CRUD → create_tab, get_tabs, update_tab, delete_tab
13. `require_auth` decorator → rejects without token, allows with valid token

### Task 7 — `testing/test_db.py`

Test `shared/db.py`:
1. `get_db_connection()` → returns connection with WAL mode enabled
2. `get_db_connection()` → sets busy_timeout to 5000ms
3. Concurrent writes → two threads writing simultaneously don't deadlock
4. Context manager → closes connection properly

---

## Test Infrastructure

### `testing/pytest.ini` or `setup.cfg` section
```ini
[pytest]
testpaths = testing
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests (no external dependencies)
    e2e: End-to-end tests (requires Docker stack)
```

### Requirements
Add to `deployment/requirements.simple.txt` (or create `testing/requirements-test.txt`):
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
```

---

## Acceptance Criteria

- [ ] `pytest testing/test_api_gateway.py -v` passes with >80% coverage of `api-gateway/api_gateway_simple.py`
- [ ] `pytest testing/test_handbrake_service.py -v` passes with >80% coverage of `handbrake-service/handbrake_service_simple.py`
- [ ] `pytest testing/test_config.py -v` passes with >90% coverage of `shared/config.py`
- [ ] `pytest testing/test_job_queue.py -v` passes with >80% coverage of `shared/job_queue.py`
- [ ] `pytest testing/test_auth.py -v` passes with >90% coverage of `api-gateway/auth.py`
- [ ] `pytest testing/test_db.py -v` passes with 100% coverage of `shared/db.py`
- [ ] All tests use temp directories (no side effects, no state leakage)
- [ ] `pytest testing/ -v --tb=short` runs all unit tests in under 30 seconds
- [ ] Tests use in-memory SQLite (no Docker required)

---

## Verification

```bash
cd /Users/eli/github/handbrake2resilio

# Install test deps
pip install pytest pytest-cov pytest-mock

# Run all unit tests with coverage
pytest testing/ -v --tb=short \
  --cov=api-gateway \
  --cov=handbrake-service \
  --cov=shared \
  --cov-report=term-missing

# Run individual test files
pytest testing/test_api_gateway.py -v
pytest testing/test_handbrake_service.py -v
pytest testing/test_auth.py -v
pytest testing/test_config.py -v
pytest testing/test_job_queue.py -v
pytest testing/test_db.py -v

# Confirm no test takes >30s total
time pytest testing/ -v -m "not e2e"
```

---

## Git Operations

```bash
git add testing/
git commit -m "test(WEA-124/125): add comprehensive unit tests for all backend services and shared modules"
git push origin main
```

---

## STOP

Next prompt: `SPRINT_02C_PLAYWRIGHT_UI_TESTS.md` (WEA-126)
