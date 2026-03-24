# SPRINT_01A — Wave 1: Dead File Cleanup & API Alignment

> Reference: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`
> Linear issues: WEA-132, WEA-133
> Model: Composer 2 / Auto (fast)

💣

## Context

The handbrake2resilio repo has been through several cleanup passes (WEA-103, WEA-104, WEA-107, WEA-110 all Done). The current folder structure is:

```
/Users/eli/github/handbrake2resilio/
├── api-gateway/
│   ├── api_gateway_simple.py   ← main API gateway (Flask, ~1240 lines)
│   └── auth.py
├── deployment/
│   ├── Dockerfile.api
│   ├── Dockerfile.handbrake
│   ├── docker-compose.yml      ← canonical compose file (in deployment/)
│   ├── .env.example
│   ├── requirements.simple.txt
│   ├── deploy_h2r.sh
│   ├── deploy_simple.sh
│   ├── deployment_readiness_check.py
│   ├── DEPLOYMENT_README.md
│   └── QUICK_DEPLOY.md
├── handbrake-service/
│   └── handbrake_service_simple.py
├── shared/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   └── job_queue.py
├── ui-frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json / package-lock.json
│   ├── src/
│   │   ├── App.js
│   │   ├── components/  (Dashboard, Header, Login, NewJobModal, QueueView, Register, Sidebar, SystemView)
│   │   ├── components/common/FileBrowser.js
│   │   ├── context/AuthContext.js
│   │   ├── services/api.js
│   │   └── utils/status.js
│   ├── tests/  (auth.spec.js, smoke.spec.js, workflows.spec.js)
│   └── ui-frontend/tests/  ← DUPLICATE nested folder — investigate
├── testing/
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_config_simple.py
│   ├── test_job_queue.py
│   └── test_simple.py
├── data/  (.gitkeep)
├── logs/  (.gitkeep)
├── scripts/  (empty)
└── documentation/
```

## Wave 1 Issues

### WEA-132 — Delete duplicate and dead files
**Persona: Backend Engineer**

#### Tasks

1. **Audit `deployment/` for dead scripts**
   - `deploy_h2r.sh` and `deploy_simple.sh` — check if either is referenced anywhere; if both do the same thing, keep only the most recent/complete one (rename to `deploy001.sh` and `deploy002.sh` if both are needed, or delete the dead one)
   - `deployment_readiness_check.py` — check if it's referenced or used; if it's a one-off script with no callers, delete it
   - `DEPLOYMENT_README.md` and `QUICK_DEPLOY.md` — check for duplication; if both cover the same content, consolidate into one

2. **Audit `ui-frontend/ui-frontend/tests/` nested duplicate**
   - `ui-frontend/ui-frontend/` is a nested duplicate folder — delete it entirely
   - Verify `ui-frontend/tests/` (the correct location) still has all 3 spec files intact

3. **Audit `testing/` Python tests**
   - `test_config.py` and `test_config_simple.py` — check for duplication; if `test_config_simple.py` is a subset of `test_config.py`, delete the simpler one
   - `test_simple.py` — check if it's a stub/placeholder with no real assertions; if so, delete it
   - Keep `test_auth.py` and `test_job_queue.py` (these are real tests)

4. **Check `scripts/` folder**
   - If empty, delete it (no empty folders in root per rules.mdc)
   - If it has content, verify it belongs there

5. **Check root for any stray files**
   - No files should be in the repo root except `.gitignore`, `.env` (if present), and `.cursor/`
   - Report any violations

#### Acceptance Criteria — WEA-132
- [ ] No duplicate files exist (verified by listing all files)
- [ ] `ui-frontend/ui-frontend/` nested folder is gone
- [ ] `deployment/` has ≤5 files (scripts consolidated if needed)
- [ ] `scripts/` folder either has content or is deleted
- [ ] `testing/` has no duplicate test files
- [ ] `git status` shows only deletions (no new files created)
- [ ] All remaining files still import/reference correctly (no broken imports)

---

### WEA-133 — Align frontend API calls to backend routes
**Personas: Frontend Engineer → Backend Engineer → QA**

#### Current API contract (verified from source)

**Frontend `ui-frontend/src/services/api.js` calls:**
```
POST  /api/auth/login
POST  /api/auth/register
GET   /api/auth/verify
GET   /api/tabs
POST  /api/tabs
PUT   /api/tabs/:id
DELETE /api/tabs/:id
GET   /api/tabs/:id/settings
GET   /api/queue
POST  /api/jobs/add
GET   /api/queue/jobs
GET   /api/jobs/status/:id
POST  /api/jobs/cancel/:id
POST  /api/queue/clear
POST  /api/queue/pause
POST  /api/queue/resume
GET   /health
GET   /api/system/load
GET   /api/filesystem/browse
POST  /api/filesystem/scan
POST  /api/filesystem/mkdir
GET   /api/filesystem/cache
```

**Backend `api-gateway/api_gateway_simple.py` routes:**
```
GET   /health                    ✅ exists
GET   /api/auth/login → POST     ✅ exists (POST)
POST  /api/auth/register         ✅ exists
GET   /api/auth/verify           ✅ exists
GET   /api/tabs                  ✅ exists
POST  /api/tabs                  ✅ exists
PUT   /api/tabs/<int:tab_id>     ✅ exists
DELETE /api/tabs/<int:tab_id>    ✅ exists
GET   /api/tabs/<tab_id>/settings ✅ exists
GET   /api/queue                 ✅ exists
POST  /api/jobs/add              ✅ exists
GET   /api/queue/jobs            ✅ exists
GET   /api/jobs/status/<job_id>  ✅ exists
POST  /api/jobs/cancel/<job_id>  ✅ exists
POST  /api/queue/clear           ✅ exists
POST  /api/queue/pause           ✅ exists
POST  /api/queue/resume          ✅ exists
GET/POST /api/system/load        ✅ exists (dual route with /api/system/status)
GET   /api/filesystem/browse     ✅ exists
POST  /api/filesystem/scan       ✅ exists
POST  /api/filesystem/mkdir      ✅ exists
GET   /api/filesystem/cache      ✅ exists
```

**Known mismatches to investigate:**
1. `tabsAPI.updateTab` sends `PUT /api/tabs/${id}` — backend route is `PUT /api/tabs/<int:tab_id>`. If `id` from frontend is a string (e.g. UUID), this will 404. Verify the `id` type returned by `GET /api/tabs` and ensure it's an integer.
2. `systemAPI.getHealth` calls `GET /health` — this is NOT proxied through nginx `/api/` prefix. Verify `nginx.conf` has a `/health` proxy block (it does — confirm it works).
3. `queueAPI.cancelJob` calls `POST /api/jobs/cancel/${id}` — backend has `POST /api/jobs/cancel/<job_id>`. Confirm match.
4. Frontend `Dashboard.js` and `SystemView.js` — audit what API calls they make directly (not through `api.js`) and verify each one exists on the backend.
5. Frontend `QueueView.js` — audit what API calls it makes and verify each one exists.

#### Tasks

**Frontend Engineer:**
1. Open `ui-frontend/src/services/api.js` — document every endpoint called
2. Open `ui-frontend/src/components/Dashboard.js`, `SystemView.js`, `QueueView.js`, `FileBrowser.js`, `NewJobModal.js` — find any direct `api.*` calls not in the central `api.js` service layer
3. Verify `tabsAPI` tab `id` type: check what `GET /api/tabs` returns and whether `PUT/DELETE /api/tabs/:id` receives an integer or string

**Backend Engineer:**
4. Open `api-gateway/api_gateway_simple.py` — list every `@app.route`
5. Cross-reference frontend calls vs backend routes — produce a mismatch list
6. Fix any mismatches:
   - If backend route is missing: add it
   - If frontend is calling wrong path: fix `api.js`
   - If type mismatch (int vs string): fix the backend route to accept both or fix the frontend to send the right type

**QA:**
7. After fixes, produce a final verified mapping table showing every frontend call → backend route → HTTP status expected
8. Verify `nginx.conf` proxies all necessary paths (`/api/`, `/health`, `/socket.io/`)

#### Acceptance Criteria — WEA-133
- [ ] Every frontend API call in `api.js` has a matching backend route
- [ ] Every component's direct API calls are verified
- [ ] Tab `id` type is consistent (int or string) across frontend and backend
- [ ] `/health` is proxied by nginx
- [ ] No 404 errors expected from any page load (Dashboard, Queue, FileBrowser)
- [ ] Final mapping table is documented in a comment block at the top of `api.js`

---

## Verification

After both WEA-132 and WEA-133 are complete, run:

```bash
# 1. Verify no nested duplicate folders
ls ui-frontend/ui-frontend/ 2>&1 | grep "No such file" && echo "✅ Nested duplicate removed"

# 2. Verify no stray files in root
ls -la /Users/eli/github/handbrake2resilio/ | grep -v "^d" | grep -v "^\." | grep -v "total"

# 3. Verify frontend builds without errors
cd ui-frontend && npm run build 2>&1 | tail -5

# 4. Verify backend imports work
cd /Users/eli/github/handbrake2resilio && python3 -c "import api-gateway.api_gateway_simple" 2>&1 || echo "check import paths"

# 5. Git status — should show only deletions
git status --short
```

## Git Operations

After completing all tasks:
```bash
git add -A
git commit -m "WEA-132/WEA-133: Remove dead files, verify API contract alignment"
git push origin HEAD
```

Then update Linear issues WEA-132 and WEA-133 to **Done**.

## STOP

Next prompt: `SPRINT_01B_WAVE2_FOLDER_STRUCTURE.md` (WEA-134)
This wave must complete before Wave 2 begins.
