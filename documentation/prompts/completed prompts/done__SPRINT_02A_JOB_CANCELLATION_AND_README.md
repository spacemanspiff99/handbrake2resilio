# SPRINT_02A — Job Cancellation (WEA-142) + Root README (WEA-143)

💣

## Rules Reference
`.cursor/rules/rules.mdc` — DRY/SRP, no hardcoded secrets, env vars, Python type hints, docstrings.

## Model Recommendation
**Composer 2 / Auto** (no API cost — file edits + docs, no browser testing needed)

## Personas (in sequence)
1. **Backend Engineer** — WEA-142: wire DELETE endpoint, verify subprocess kill
2. **QA Engineer** — WEA-142: verify cancellation acceptance criteria
3. **Engineering Manager** — WEA-143: write root README

---

## Issue: WEA-142 — Implement actual job cancellation

### Context
- `handbrake-service/handbrake_service_simple.py` already has:
  - `active_jobs` dict tracking `{"job": ConversionJob, "process": subprocess.Popen}`
  - `POST /cancel/<job_id>` that kills the process and marks `CANCELLED`
  - `_terminate_process()` and `_cleanup_partial_output()` helpers
- `api-gateway/api_gateway_simple.py` already has:
  - `POST /api/jobs/cancel/<job_id>` that proxies to handbrake service
- `ui-frontend/src/services/api.js` already has:
  - `queueAPI.cancelJob(id)` calling `POST /api/jobs/cancel/<id>`
- `ui-frontend/src/components/QueueView.js` already has:
  - `cancelJobMutation` wired to the cancel button

### Gap Analysis
The existing cancel endpoint in the handbrake service only handles **running** jobs (those in `active_jobs`). It does NOT handle **queued-but-not-started** jobs. The api-gateway also uses `POST` not `DELETE`. WEA-142 asks for `DELETE /jobs/{job_id}` but the existing code uses `POST /cancel/<job_id>` — we should add a `DELETE` alias while keeping the existing `POST` for backward compat.

### Tasks

#### Task 1 — Backend: Add DELETE endpoint alias in handbrake-service
File: `handbrake-service/handbrake_service_simple.py`

Add a `DELETE /jobs/<job_id>` endpoint that:
- If job is in `active_jobs` with status RUNNING → kill process, set `CANCELLED`
- If job is in DB with status `pending` → set `CANCELLED` in DB (no process to kill)
- If job is done/failed/cancelled → return 400

```python
@app.route("/jobs/<job_id>", methods=["DELETE"])
def delete_job(job_id: str):
    """Cancel a job by ID (DELETE alias for /cancel/<job_id>).
    Handles both running and queued-but-not-started jobs.
    """
    # Check active (running) jobs first
    with job_lock:
        if job_id in active_jobs:
            entry = active_jobs[job_id]
            job = entry["job"]
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.CANCELLED
                process_to_kill = entry.get("process")
                output_path = job.output_path
                active_jobs.pop(job_id)
            else:
                return jsonify({"error": "Cannot cancel", "message": f"Job is {job.status.value}"}), 400

        else:
            # Check DB for pending job
            job = get_job_from_db(job_id)
            if not job:
                return jsonify({"error": "Job not found", "message": f"Job {job_id} does not exist"}), 404
            if job.status not in (JobStatus.PENDING,):
                return jsonify({"error": "Cannot cancel", "message": f"Job is already {job.status.value}"}), 400
            job.status = JobStatus.CANCELLED
            process_to_kill = None
            output_path = None

    _terminate_process(process_to_kill, job_id)
    save_job_to_db(job)
    if output_path:
        _cleanup_partial_output(output_path, job_id)

    logger.info(f"Job {job_id} cancelled via DELETE")
    return jsonify({"message": "Job cancelled successfully", "job_id": job_id})
```

#### Task 2 — Backend: Add DELETE proxy in api-gateway
File: `api-gateway/api_gateway_simple.py`

Add `DELETE /api/jobs/<job_id>` that proxies to handbrake service `DELETE /jobs/<job_id>`:

```python
@app.route("/api/jobs/<job_id>", methods=["DELETE"])
@require_auth
def delete_job(job_id: str):
    """Cancel a job via DELETE — proxies to handbrake-service DELETE /jobs/<job_id>."""
    try:
        handbrake_response = forward_to_handbrake_service(
            f"/jobs/{job_id}", method="DELETE"
        )
        if handbrake_response:
            job = get_job_from_db(job_id)
            if job:
                job.status = JobStatus.CANCELLED
                save_job_to_db(job)
            logger.info(f"Job {job_id} cancelled via DELETE")
            return jsonify({"message": "Job cancelled successfully"})
        else:
            return jsonify({"error": "HandBrake service unavailable", "message": "Video conversion service is not responding"}), 503
    except Exception as e:
        logger.error(f"Delete job error: {e}")
        return jsonify({"error": "Failed to cancel job", "message": str(e)}), 500
```

Also verify `forward_to_handbrake_service` supports `method="DELETE"` — if not, add it.

#### Task 3 — Frontend: Update QueueView cancel to use DELETE
File: `ui-frontend/src/services/api.js`

Add a `deleteJob` method using `DELETE`:
```javascript
deleteJob: (id) => api.delete(`/api/jobs/${id}`),
```
Keep `cancelJob` (POST) for backward compat.

File: `ui-frontend/src/components/QueueView.js`

Update `cancelJobMutation` to use `queueAPI.deleteJob` instead of `queueAPI.cancelJob`.

Also ensure the cancel button is shown for **both** `running` AND `pending` jobs (not just running).

#### Task 4 — Frontend: Show cancel button for pending jobs too
In `QueueView.js`, the cancel button should be visible when `job.status === 'running' || job.status === 'pending'`.

---

## Issue: WEA-143 — Create root README.md

### Context
No `README.md` exists at repo root. There is `documentation/README.md` (generic workspace overview) and `ui-frontend/README.md` (frontend-specific).

### Task
Create `/README.md` at repo root (keep under 100 lines):

```markdown
# handbrake2resilio

Convert video files with HandBrakeCLI and sync output to Resilio Sync — managed via a web UI.

## Quick Start

```bash
cp deployment/.env.example deployment/.env
# Edit deployment/.env — set JWT_SECRET_KEY and media paths
docker compose -f deployment/docker-compose.yml up --build
```

Open http://localhost:7474 — login with `admin` / `admin123`.

## Prerequisites

- Docker + Docker Compose v2
- HandBrake input directory (read-only mount)
- Output directory (writable mount)

## Architecture

| Service | Port | Role |
|---------|------|------|
| `api-gateway` | 8080 | Flask REST + WebSocket gateway, auth, SQLite |
| `handbrake-service` | 8081 | HandBrakeCLI worker, job queue, process management |
| `frontend` | 7474 | React UI (Nginx) |

## Environment Variables

See [`deployment/.env.example`](deployment/.env.example) for all variables.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | ✅ | — | Random string ≥16 chars (`openssl rand -base64 32`) |
| `MEDIA_INPUT_PATH` | ✅ | `/tmp/media_input` | Host path for input video files |
| `MEDIA_OUTPUT_PATH` | ✅ | `/tmp/media_output` | Host path for converted output |
| `MAX_CONCURRENT_JOBS` | | `2` | Max parallel HandBrake jobs |
| `API_PORT` | | `8080` | API gateway host port |
| `FRONTEND_PORT` | | `7474` | Frontend host port |

## Documentation

- [Architecture overview](documentation/MICROSERVICES_ARCHITECTURE.md)
- [Deployment guide](documentation/DEPLOYMENT_GUIDE.md)
- [Next steps](documentation/NEXT_STEPS.md)
```

---

## Acceptance Criteria

### WEA-142
- [ ] Running job can be cancelled via the UI (cancel button → DELETE /api/jobs/{id})
- [ ] Cancelled job shows `cancelled` status in queue
- [ ] HandBrake subprocess is terminated on cancel (no zombie processes)
- [ ] Queued-but-not-started (pending) job can also be cancelled
- [ ] Cancel button is visible for both `running` and `pending` jobs

### WEA-143
- [ ] `README.md` exists at repo root
- [ ] Quick start commands are accurate (`docker compose -f deployment/docker-compose.yml up --build`)
- [ ] All env vars documented with Required/Default columns
- [ ] Architecture section describes all 3 services with ports

---

## Verification

```bash
# 1. Verify DELETE endpoint exists in handbrake service
grep -n "DELETE" handbrake-service/handbrake_service_simple.py

# 2. Verify DELETE proxy in api-gateway
grep -n "DELETE" api-gateway/api_gateway_simple.py

# 3. Verify frontend uses deleteJob
grep -n "deleteJob\|deleteJob" ui-frontend/src/services/api.js
grep -n "deleteJob" ui-frontend/src/components/QueueView.js

# 4. Verify README exists
ls -la README.md
wc -l README.md  # should be ≤ 100 lines

# 5. Run existing unit tests to confirm nothing broken
cd /Users/eli/github/handbrake2resilio
python -m pytest api-gateway/unit-tests/ shared/unit-tests/ -v --tb=short
```

---

## Git Operations

```bash
git add handbrake-service/handbrake_service_simple.py \
        api-gateway/api_gateway_simple.py \
        ui-frontend/src/services/api.js \
        ui-frontend/src/components/QueueView.js \
        README.md
git commit -m "feat(WEA-142/143): add DELETE job cancellation endpoint + root README"
git push origin main
```

---

## STOP

Next prompt: `SPRINT_02B_UNIT_TESTS.md` (WEA-124, WEA-125)
