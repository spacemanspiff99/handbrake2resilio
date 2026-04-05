# SPRINT_02D — E2E Integration Tests + Full Stack Verification (WEA-127, WEA-144)

💣

## Rules Reference
`.cursor/rules/rules.mdc` — always test with real data, never claim a feature works without E2E verification.

## Model Recommendation
**Claude 4.6 Sonnet** (Docker stack management + browser testing + cross-service verification)

## Personas (in sequence)
1. **QA Engineer** — design E2E test coverage, define pass/fail criteria
2. **Full Stack Engineer** — implement integration tests, fix any broken endpoints
3. **QA Engineer** — run full verification, document results on Linear issues

---

## Prerequisites

**This prompt requires the full Docker stack to be running.**

```bash
cd /Users/eli/github/handbrake2resilio
docker compose -f deployment/docker-compose.yml up --build -d
# Wait for health checks to pass (~30s)
docker compose -f deployment/docker-compose.yml ps
```

All 3 services must show `healthy`:
- `h2r-api-gateway` → port 8080
- `h2r-handbrake` → port 8081
- `h2r-frontend` → port 7474

---

## Issue: WEA-127 — E2E integration tests across full Docker stack

### Task 1 — Create `testing/conftest_e2e.py`

```python
"""E2E test fixtures — requires full Docker stack running."""
import os
import pytest
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8080")
HB_URL = os.environ.get("HB_URL", "http://localhost:8081")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:7474")


def is_stack_running() -> bool:
    """Check if the Docker stack is reachable."""
    try:
        resp = requests.get(f"{API_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_stack():
    """Skip all E2E tests if Docker stack is not running."""
    if not is_stack_running():
        pytest.skip("Docker stack not running — start with: docker compose -f deployment/docker-compose.yml up -d")
    return {"api_url": API_URL, "hb_url": HB_URL, "frontend_url": FRONTEND_URL}


@pytest.fixture(scope="session")
def api_url(docker_stack):
    return docker_stack["api_url"]


@pytest.fixture(scope="session")
def hb_url(docker_stack):
    return docker_stack["hb_url"]


@pytest.fixture(scope="session")
def frontend_url(docker_stack):
    return docker_stack["frontend_url"]


@pytest.fixture(scope="session")
def auth_token(api_url):
    """Log in as admin and return Bearer token."""
    resp = requests.post(f"{api_url}/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(autouse=False)
def clean_test_jobs(api_url, auth_headers):
    """Clean up test jobs after each test that creates them."""
    yield
    try:
        requests.post(f"{api_url}/api/queue/clear", headers=auth_headers, timeout=5)
    except Exception:
        pass
```

### Task 2 — Create `testing/test_e2e_integration.py`

Full test coverage per WEA-127. Use `@pytest.mark.e2e` on all tests.

#### Service Health Tests (tests 1-6)
```python
import pytest
import requests

pytestmark = pytest.mark.e2e

class TestServiceHealth:
    def test_api_gateway_reachable(self, api_url):
        resp = requests.get(f"{api_url}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_handbrake_service_reachable(self, hb_url):
        resp = requests.get(f"{hb_url}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "system" in data

    def test_frontend_reachable(self, frontend_url):
        resp = requests.get(frontend_url)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    def test_api_gateway_db_healthy(self, api_url):
        resp = requests.get(f"{api_url}/health")
        data = resp.json()
        assert data.get("database") in ("sqlite", "healthy", "ok")
```

#### Authentication Flow (tests 7-10)
```python
class TestAuthFlow:
    def test_login_returns_token(self, api_url):
        resp = requests.post(f"{api_url}/api/auth/login",
                             json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_token_verification(self, api_url, auth_headers):
        resp = requests.get(f"{api_url}/api/auth/verify", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json().get("valid") is True

    def test_protected_endpoint_without_token(self, api_url):
        resp = requests.get(f"{api_url}/api/tabs")
        assert resp.status_code == 401

    def test_protected_endpoint_with_token(self, api_url, auth_headers):
        resp = requests.get(f"{api_url}/api/tabs", headers=auth_headers)
        assert resp.status_code == 200
```

#### Job Submission Pipeline (tests 11-14)
```python
class TestJobPipeline:
    def test_submit_job_returns_job_id(self, api_url, auth_headers, clean_test_jobs):
        resp = requests.post(f"{api_url}/api/jobs/add",
                             headers=auth_headers,
                             json={"input_path": "/media/input/test.mp4",
                                   "output_path": "/media/output/test.mkv"})
        # 200 (accepted) or 503 (handbrake unavailable) are both valid
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            assert "job_id" in resp.json()

    def test_queue_jobs_endpoint(self, api_url, auth_headers):
        resp = requests.get(f"{api_url}/api/queue/jobs", headers=auth_headers)
        assert resp.status_code == 200
        assert "jobs" in resp.json() or isinstance(resp.json(), list)
```

#### File Browser Integration (tests 15-18)
```python
class TestFileBrowser:
    def test_browse_returns_listing(self, api_url, auth_headers):
        resp = requests.get(f"{api_url}/api/filesystem/browse",
                            headers=auth_headers,
                            params={"path": "/media/input"})
        assert resp.status_code in (200, 404)  # 404 if mount not present

    def test_browse_nonexistent_path(self, api_url, auth_headers):
        resp = requests.get(f"{api_url}/api/filesystem/browse",
                            headers=auth_headers,
                            params={"path": "/nonexistent/path/xyz"})
        assert resp.status_code in (404, 400)
```

#### Tab Management Integration (tests 19-22)
```python
class TestTabManagement:
    def test_tab_crud(self, api_url, auth_headers):
        # Create
        resp = requests.post(f"{api_url}/api/tabs",
                             headers=auth_headers,
                             json={"name": "E2E Test Tab",
                                   "source_path": "/media/input",
                                   "destination_path": "/media/output"})
        assert resp.status_code == 200
        tab_id = resp.json().get("tab_id") or resp.json().get("id")
        assert tab_id

        # List
        resp = requests.get(f"{api_url}/api/tabs", headers=auth_headers)
        assert resp.status_code == 200

        # Update
        resp = requests.put(f"{api_url}/api/tabs/{tab_id}",
                            headers=auth_headers,
                            json={"name": "E2E Test Tab Updated"})
        assert resp.status_code == 200

        # Delete
        resp = requests.delete(f"{api_url}/api/tabs/{tab_id}", headers=auth_headers)
        assert resp.status_code == 200
```

#### Error Handling (tests 29-31)
```python
class TestErrorHandling:
    def test_invalid_json_returns_400(self, api_url, auth_headers):
        resp = requests.post(f"{api_url}/api/jobs/add",
                             headers={**auth_headers, "Content-Type": "application/json"},
                             data="not-valid-json")
        assert resp.status_code in (400, 415, 500)

    def test_missing_input_path_returns_400(self, api_url, auth_headers):
        resp = requests.post(f"{api_url}/api/jobs/add",
                             headers=auth_headers,
                             json={"output_path": "/media/output/test.mkv"})
        assert resp.status_code in (400, 503)
```

### Task 3 — Create `testing/run_e2e.sh`

```bash
#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Starting Docker stack ==="
docker compose -f "$REPO_ROOT/deployment/docker-compose.yml" up -d --build

echo "=== Waiting for services to be healthy ==="
for i in $(seq 1 30); do
  if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
    echo "API gateway healthy after ${i}s"
    break
  fi
  sleep 2
done

echo "=== Running E2E tests ==="
cd "$REPO_ROOT"
pytest testing/test_e2e_integration.py -v -m e2e --tb=short

echo "=== E2E tests complete ==="
```

Make executable: `chmod +x testing/run_e2e.sh`

---

## Issue: WEA-144 — Full E2E verification with Playwright

### Task 4 — Run Playwright tests against live stack

After Docker stack is confirmed healthy:

```bash
cd /Users/eli/github/handbrake2resilio/ui-frontend
BASE_URL=http://localhost:7474 USE_LIVE_API=true npx playwright test --project=chromium
```

Fix any broken test stubs that fail against the live stack.

### Task 5 — Manual smoke test checklist

Document results as comments on WEA-144 in Linear:

- [ ] Login with `admin/admin123` → dashboard loads
- [ ] Dashboard shows system health data (CPU %, memory %, disk %)
- [ ] File browser navigates `/media/input` (or shows appropriate error if not mounted)
- [ ] Queue view loads without errors
- [ ] Submit a job (if test file available in `/media/input`)
- [ ] Cancel button visible for pending/running jobs
- [ ] No 404 errors for API calls in browser Network tab
- [ ] No 500 errors in browser console

### Task 6 — Update Linear issues

After all tests pass, update each issue status to **Done** in Linear:
- WEA-142 → Done
- WEA-143 → Done
- WEA-144 → Done
- WEA-124 → Done
- WEA-125 → Done
- WEA-126 → Done
- WEA-127 → Done
- WEA-123 (epic) → Done (if all children done)

---

## Acceptance Criteria

### WEA-127
- [ ] `pytest testing/test_e2e_integration.py -v -m e2e` passes all tests against running Docker stack
- [ ] Tests cover all 3 services and their interactions
- [ ] Tab CRUD verified end-to-end
- [ ] Error handling tested for common failure modes
- [ ] `./testing/run_e2e.sh` runs the full suite in one command
- [ ] Total E2E suite runs in under 5 minutes

### WEA-144
- [ ] All Playwright tests pass against live stack
- [ ] Login works end-to-end
- [ ] Dashboard shows system health (not blank)
- [ ] File browser loads without errors
- [ ] Queue view loads without errors
- [ ] Zero 404 errors for API calls
- [ ] Zero 500 errors in browser console

---

## Verification

```bash
# 1. Start stack
docker compose -f deployment/docker-compose.yml up --build -d

# 2. Wait for health
sleep 30
curl -s http://localhost:8080/health | python3 -m json.tool
curl -s http://localhost:8081/health | python3 -m json.tool
curl -sI http://localhost:7474 | head -5

# 3. Run E2E integration tests
pytest testing/test_e2e_integration.py -v -m e2e --tb=short

# 4. Run Playwright against live stack
cd ui-frontend
BASE_URL=http://localhost:7474 USE_LIVE_API=true npx playwright test --project=chromium

# 5. Full E2E via script
./testing/run_e2e.sh
```

---

## Git Operations

```bash
git add testing/conftest_e2e.py testing/test_e2e_integration.py testing/run_e2e.sh
git commit -m "test(WEA-127/144): add E2E integration tests and full stack verification"
git push origin main
```

---

## STOP

Sprint 2 complete. All prompts executed:
- `done__SPRINT_02A_JOB_CANCELLATION_AND_README.md`
- `done__SPRINT_02B_UNIT_TESTS.md`
- `done__SPRINT_02C_PLAYWRIGHT_UI_TESTS.md`
- `done__SPRINT_02D_E2E_INTEGRATION.md`
