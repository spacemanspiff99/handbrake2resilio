# SPRINT_04C — E2E Verification with Real Video File

💣

## Linear Issue
**WEA-264** — E2E manual + automated verification with a real video file
https://linear.app/weather-app-eli/issue/WEA-264

## Recommended Model
**Claude 4.6 Sonnet** — This prompt requires browser MCP tools (Playwright), Docker orchestration, shell assertions, and cross-domain reasoning across three service boundaries. Sonnet is the minimum viable model here.

> Use **Opus** ONLY if Sonnet fails the same Playwright or Docker step three times with no progress. Opus costs 5× more — exhaust Sonnet first.
> Do NOT use Composer 2 / Auto for this prompt — it does not have browser MCP tools.

## Sprint
Sprint 04 — Real Video Test

## Pre-conditions (HARD GATE — do not proceed until all pass)

- [ ] WEA-262 (CLI flags fix) PR merged to `master`
- [ ] WEA-263 (progress monitoring fix) PR merged to `master` (optional — 264 can run without it, but progress will show 0%)
- [ ] `.env` file exists at repo root with:
  - `JWT_SECRET_KEY` set to a real secret (not the placeholder)
  - `MEDIA_INPUT_PATH` pointing to a host directory containing `test_clip.mp4`
  - `MEDIA_OUTPUT_PATH` pointing to a host directory writable by the container
- [ ] `test_clip.mp4` (~5MB, <60 seconds) exists at `$MEDIA_INPUT_PATH/test_clip.mp4`

**If any pre-condition fails, stop and report. Do not attempt workarounds.**

---

## Context

Load rules: `core.mdc`, `backend.mdc`, `devops.mdc`, `frontend.mdc`

This is the gate issue for Sprint 04. The goal is a verified end-to-end conversion: video file in → `.mkv` file out, with the UI working and Playwright smoke passing.

---

## Tasks

### Session A — Clean Rebuild (DevOps)

```bash
# 1. Check disk space
df -h /

# 2. Stop existing stack
docker compose -f deployment/docker-compose.yml down --remove-orphans

# 3. Remove old project images
docker rmi $(docker images 'h2r-*' -q) 2>/dev/null || true

# 4. Prune build cache
docker builder prune -af

# 5. Rebuild from scratch
docker compose -f deployment/docker-compose.yml up -d --build

# 6. Verify all 3 containers are healthy (wait up to 60s)
docker compose -f deployment/docker-compose.yml ps

# 7. Verify container creation time is newer than the last git commit
docker inspect h2r-handbrake --format='{{.Created}}'
git log -1 --format='%ci'
# Container created-at must be AFTER the git commit timestamp
```

### Session B — API Contract Verification (Backend)

```bash
BASE_URL="http://localhost:7474"

# Liveness
curl -sf "$BASE_URL/api/v1/health" > /dev/null \
  || (echo "FAIL: /health unreachable" && exit 1)

# Contract — response body shape (not just 200)
curl -sf "$BASE_URL/health" | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert d.get('status') == 'healthy', f'bad status: {d}'
print('health contract OK')
"

# Jobs list shape
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

curl -sf -H "Authorization: Bearer $TOKEN" http://localhost:8080/api/jobs | python3 -c "
import json, sys
d = json.load(sys.stdin)
assert 'jobs' in d, f'missing key jobs: {list(d)[:5]}'
assert isinstance(d['jobs'], list), 'jobs must be a list'
print(f'jobs contract OK: {len(d[\"jobs\"])} jobs')
"
```

### Session C — Submit Real Conversion Job (Backend)

```bash
# Submit job with real input path (as seen inside the container)
JOB=$(curl -s -X POST http://localhost:8080/api/jobs/add \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"input_path": "/media/input/test_clip.mp4"}')

echo "Job submitted: $JOB"
JOB_ID=$(echo $JOB | python3 -c "import json,sys; print(json.load(sys.stdin)['job_id'])")

# Poll until completed or failed (timeout 10 minutes)
for i in $(seq 1 120); do
  STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8080/api/jobs/$JOB_ID" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(d.get('status','unknown'), d.get('progress',0))
")
  echo "[$i] $STATUS"
  echo "$STATUS" | grep -q "completed" && break
  echo "$STATUS" | grep -q "failed" && (echo "CONVERSION FAILED"; exit 1)
  sleep 5
done

# Assert output file exists on host
OUTPUT_FILE="${MEDIA_OUTPUT_PATH}/test_clip.mkv"
test -f "$OUTPUT_FILE" && echo "OUTPUT FILE EXISTS: $OUTPUT_FILE" \
  || (echo "FAIL: output file not found at $OUTPUT_FILE" && exit 1)
```

### Session D — Playwright Smoke (Browser/Frontend)

Run Playwright **inside Docker** per `frontend.mdc` § Playwright Containerization:

```bash
cd /home/akun/handbrake2resilio
docker run --rm \
  --network=host \
  -v "$(pwd)/ui-frontend:/work" \
  -w /work \
  -e USE_LIVE_API=true \
  -e BASE_URL=http://localhost:7474 \
  mcr.microsoft.com/playwright:v1.52.0-jammy \
  npx playwright test tests/smoke.spec.js --project=chromium
```

Screenshots will be saved to `ui-frontend/test-results/`. Review the screenshot manually to confirm the UI is visually styled (not raw HTML).

---

## Verification Checklist

```bash
# All 3 containers healthy
docker compose -f deployment/docker-compose.yml ps | grep -c "healthy"
# Expected: 3

# Output file exists
ls -lh "$MEDIA_OUTPUT_PATH/test_clip.mkv"

# Playwright screenshots exist
ls ui-frontend/test-results/
```

---

## Acceptance Criteria (from WEA-264)

- [ ] All 3 Docker containers report `healthy` in `docker compose ps`
- [ ] `GET /health` returns `{"status": "healthy"}` with correct data shape
- [ ] Conversion job submitted via API reaches `status: completed`
- [ ] Converted `.mkv` output file exists in `MEDIA_OUTPUT_PATH` on the host
- [ ] Playwright smoke passes (CSS sanity + screenshot) in Docker
- [ ] UI is visually styled — Playwright screenshot reviewed and confirmed
- [ ] Full-page screenshot saved to `ui-frontend/test-results/`
- [ ] 📖 `docs/NEXT_STEPS.md` updated with verified status of each check

## Deployment checklist (CAT-D1)
- [ ] `docker compose down --remove-orphans` run before rebuild
- [ ] `docker builder prune -af` run before rebuild
- [ ] Container creation timestamp newer than latest source commit
- [ ] Post-deploy API contract check passes

## CSS sanity checklist (CAT-F1/P1)
- [ ] Playwright smoke assertion `cssRules.length > 50` passes
- [ ] Built CSS bundle >5 KB (check: `du -sh ui-frontend/dist/assets/*.css`)
- [ ] Full-page screenshot captured and reviewed

---

## STOP

After all AC pass:

1. Mark **WEA-264** Done in Linear
2. Rename this prompt: `done__SPRINT_04C_E2E_VERIFICATION.md` → move to `docs/prompts/completed prompts/`
3. Also rename and move SPRINT_04A and SPRINT_04B if their PRs are merged
4. Next sprint: start **SPRINT_05A_PROGRESS_MONITORING** and **SPRINT_05B_CPU_LIMITS** in parallel using **Composer 2 / Auto**, then **SPRINT_05C_MIGRATIONS** also with **Composer 2 / Auto**

💥
