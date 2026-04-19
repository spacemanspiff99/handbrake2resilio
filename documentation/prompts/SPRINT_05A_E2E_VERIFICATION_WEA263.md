# SPRINT_05A — E2E Verification: WEA-263 Progress Monitoring Fix

> **Rules reference**: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`
> **Linear issue**: WEA-263 (status: Done — verify prod-readiness before closing release pipeline)
> **Branch**: `main` (post-merge of `spcmanspiff/wea-263-fix-progress-monitoring`)
> **Recommended model**: **Composer 2 / Auto** for build + API steps; **Claude 4.6 Sonnet** for Playwright browser test step (browser MCP needs strong reasoning)

---

## Context

PR #1 was merged to `main`. The unit tests (4/4) passed on the feature branch. However, the following acceptance criteria from WEA-263 were **NOT verified** before merge:

- API polling shows progress between 0–100 during a live HandBrake job
- Playwright UI smoke suite passes with a full-page screenshot
- Docker stack builds cleanly from `main`

This prompt covers the full E2E verification in three sequential micro-tasks (one agent each, fresh sessions).

---

## Personas (iterate in sequence, NOT parallel)

1. **DevOps Engineer** — disk check, clean build, container health
2. **Backend Engineer** — API contract test, progress polling verification
3. **QA Engineer** — Playwright Docker smoke suite, screenshot review

---

## Acceptance Criteria

- [ ] Disk usage < 85% before build
- [ ] `docker compose up --build` completes with all 3 containers healthy (`h2r-api-gateway`, `h2r-handbrake`, `h2r-frontend`)
- [ ] `GET /health` on port 8080 returns `200 OK`
- [ ] `GET /health` on port 8081 returns `200 OK`
- [ ] `POST /api/auth/login` with `admin`/`admin123` returns a JWT token
- [ ] A job submitted via `POST /api/jobs` with a real input file shows `progress` values between 0 and 100 when polled with `GET /api/jobs/<id>` while running (not stuck at 0)
- [ ] Playwright smoke suite runs in Docker (`mcr.microsoft.com/playwright`) and all tests pass
- [ ] Full-page screenshot saved to `ui-frontend/playwright-report/` and visually confirms UI is styled (not raw text)
- [ ] CSS sanity test passes (stylesheet has > 50 rules or CSS bundle > 5 KB)

---

## TASK 1 — DevOps: Disk Check + Clean Build

**Persona**: DevOps Engineer
**Model**: Composer 2 / Auto
**Binary success condition**: All 3 containers report healthy in `docker ps`

### Steps

1. Check disk space — abort if > 85%:
   ```bash
   df -h / | awk 'NR==2 {print $5}' # must be < 85%
   ```

2. Stop and remove any existing project containers and images:
   ```bash
   docker compose -f deployment/docker-compose.yml down --rmi local --volumes --remove-orphans
   docker system prune -f
   ```

3. Kill any lingering processes on ports 7474, 8080, 8081:
   ```bash
   fuser -k 7474/tcp 8080/tcp 8081/tcp 2>/dev/null || true
   ```

4. Set up test media directories and `.env`:
   ```bash
   mkdir -p /tmp/media_input /tmp/media_output
   # Copy a small test video into /tmp/media_input (e.g. any .mkv or .mp4 < 50 MB)
   # Ensure .env exists at project root with JWT_SECRET_KEY set
   cp .env.example .env  # if .env does not exist
   sed -i 's/change-me-to-a-random-string-at-least-16-chars/test-secret-key-for-local-e2e-32x/' .env
   sed -i 's|/mnt/media/input|/tmp/media_input|' .env
   sed -i 's|/mnt/media/output|/tmp/media_output|' .env
   ```

5. Build and start the stack:
   ```bash
   docker compose -f deployment/docker-compose.yml --env-file .env up --build -d
   ```

6. Wait for health checks to pass (up to 60 seconds):
   ```bash
   sleep 15 && docker ps --filter "name=h2r" --format "table {{.Names}}\t{{.Status}}"
   ```

### Verification
```bash
# All three must show "(healthy)" or "Up"
docker ps --filter "name=h2r" --format "{{.Names}}: {{.Status}}"
curl -sf http://localhost:8080/health && echo "API gateway OK"
curl -sf http://localhost:8081/health && echo "Handbrake service OK"
```

---

## TASK 2 — Backend Engineer: API Contract + Progress Polling

**Persona**: Backend Engineer
**Model**: Composer 2 / Auto
**Binary success condition**: `GET /api/jobs/<id>` returns `progress > 0` at least once during an active job

### Steps

1. Log in and capture JWT:
   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
   echo "TOKEN: $TOKEN"
   ```

2. List available input files:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/files | python3 -m json.tool
   ```

3. Submit a conversion job using a real input file from the list:
   ```bash
   JOB_ID=$(curl -s -X POST http://localhost:8080/api/jobs \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"input_file": "<filename from step 2>", "preset": "Fast 1080p30"}' \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
   echo "JOB_ID: $JOB_ID"
   ```

4. Poll progress for 60 seconds, logging each response:
   ```bash
   for i in $(seq 1 12); do
     curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/jobs/$JOB_ID \
       | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'progress={d[\"progress\"]} status={d[\"status\"]}')"
     sleep 5
   done
   ```

5. Check handbrake-service logs for DEBUG-level stderr lines and progress regex matches:
   ```bash
   docker logs h2r-handbrake 2>&1 | grep -E "progress|stderr|Encoding|%" | tail -30
   ```

### Verification
- At least one poll in step 4 must show `progress > 0`
- `docker logs h2r-handbrake` must contain lines matching `Encoding: task` (confirms stderr is being read)
- No `ERROR` or `Exception` lines in `docker logs h2r-handbrake` related to progress parsing

---

## TASK 3 — QA Engineer: Playwright Docker Smoke Suite

**Persona**: QA Engineer
**Model**: Claude 4.6 Sonnet (browser test needs strong reasoning)
**Binary success condition**: All Playwright tests pass; full-page screenshot saved and UI is visually styled

### Steps

1. Build the Playwright Docker image:
   ```bash
   docker build -f ui-frontend/Dockerfile.playwright -t h2r-playwright ui-frontend/
   ```

2. Run the full smoke suite against the live stack:
   ```bash
   docker run --rm --network=host \
     -e BASE_URL=http://localhost:7474 \
     -e USE_LIVE_API=true \
     -v $(pwd)/ui-frontend/playwright-report:/app/playwright-report \
     -v $(pwd)/ui-frontend/test-results:/app/test-results \
     h2r-playwright
   ```

3. Review screenshot saved to `ui-frontend/playwright-report/` — confirm:
   - UI is visually styled (not raw text/unstyled HTML)
   - Login page renders with form fields
   - No visual regressions vs. previous passing state

4. CSS sanity check (if not already in smoke suite):
   ```bash
   # Verify CSS bundle size > 5 KB in the frontend container
   docker exec h2r-frontend find /usr/share/nginx/html/assets -name "*.css" -exec ls -lh {} \;
   ```

### Verification
```bash
# All tests green
docker run --rm --network=host -e BASE_URL=http://localhost:7474 -e USE_LIVE_API=true h2r-playwright
# Exit code must be 0
echo "Exit code: $?"
# Screenshot must exist
ls -lh ui-frontend/playwright-report/*.png 2>/dev/null || ls -lh ui-frontend/test-results/**/*.png 2>/dev/null
```

---

## Post-Verification

Once all 3 tasks pass:

1. Commit the playwright-report screenshots to the repo (as evidence):
   ```bash
   git add ui-frontend/playwright-report/ ui-frontend/test-results/
   git commit -m "test(WEA-263): E2E verification screenshots — progress monitoring fix confirmed"
   git push origin main
   ```

2. Update Linear WEA-263 with a comment confirming E2E pass (if not already Done).

3. Rename this prompt to `done__SPRINT_05A_E2E_VERIFICATION_WEA263.md` and move to `documentation/prompts/completed prompts/`.

4. Commit the rename:
   ```bash
   git add documentation/prompts/
   git commit -m "docs: mark SPRINT_05A complete — WEA-263 E2E verified"
   git push origin main
   ```

---

## STOP

This is the end of SPRINT_05A. Next prompt in sequence (if deploy to server `192.168.10.18` is required):
**`SPRINT_03A_DEPLOY_TO_SERVER.md`** (already exists — review and execute after local E2E passes).
