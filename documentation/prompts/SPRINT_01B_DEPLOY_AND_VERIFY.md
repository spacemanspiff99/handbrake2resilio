# SPRINT_01B: Deploy and Verify on 192.168.10.18

> **Reference:** `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`
> **Recommended model:** Composer 2 / Auto (shell + monitoring — no API cost)
> **Personas:** Backend Engineer → QA Engineer
> **Max 3 tasks per agent. One binary success condition.**

---

## Context

Sprint 1 code is complete and pushed to `main` on GitHub. This prompt covers getting the app running on the home server (`192.168.10.18`) and verifying it works end-to-end.

**What was built in Sprint 1:**
- Clean 3-service Docker stack: api-gateway (:8080), handbrake-service (:8081), frontend (:7474)
- nginx reverse proxy on frontend (no CORS, no hardcoded IPs)
- SQLite with WAL mode, JWT auth, shared/ modules
- All 4 boot-time blockers fixed (CORS, uuid job ID, quality type, job_id mismatch)

**Login credentials:** `admin` / `admin123`

---

## Acceptance Criteria

All of the following must be true before this prompt is marked `done__`:

- [ ] `docker compose ps` shows all 3 containers with status `healthy`
- [ ] `http://192.168.10.18:7474` loads the login page in a browser
- [ ] Login with `admin` / `admin123` redirects to dashboard with no JS errors
- [ ] Dashboard shows system health (CPU, memory, HandBrake status)
- [ ] File browser navigates into at least one media directory (`/mnt/tv` or `/mnt/movies`)
- [ ] `http://192.168.10.18:8080/health` returns `{"status":"healthy"}` with `"handbrake_service":true`
- [ ] No `[FAIL]` lines in deploy script output

---

## Step 1 — Server Setup

On `192.168.10.18`, run:

```bash
# If not already cloned:
git clone https://github.com/spacemanspiff99/handbrake2resilio.git
cd handbrake2resilio

# If already cloned:
cd handbrake2resilio
git pull origin main
```

---

## Step 2 — Configure .env

```bash
cp deployment/.env.example .env
```

Edit `.env` — fill in ALL of these:

```bash
# Generate and set a real key (REQUIRED — app will refuse to start without it)
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Set to your actual media paths on the host
INPUT_TV_PATH=/your/actual/tv/path
INPUT_MOVIES_PATH=/your/actual/movies/path
OUTPUT_PATH=/your/actual/resilio/sync/path

# Ports — 7474 for frontend, 8080 for API (leave defaults unless conflicts)
FRONTEND_PORT=7474
API_PORT=8080
HANDBRAKE_PORT=8081

# Leave these as defaults
CORS_ORIGINS=*
MAX_CONCURRENT_JOBS=2
LOG_LEVEL=INFO
```

**Verify .env before proceeding:**
```bash
grep JWT_SECRET_KEY .env  # Must NOT say "change-me-to-a-random-string"
grep INPUT_TV_PATH .env   # Must be a real path that exists
ls $(grep INPUT_TV_PATH .env | cut -d= -f2)  # Must list files
```

---

## Step 3 — Run the Deploy Script

```bash
# From project root
chmod +x deployment/deploy_h2r.sh
bash deployment/deploy_h2r.sh
```

**Expected output:** All steps pass with `[OK]`, final summary shows URLs.

**If Step 4/6 (build) fails:**
```bash
# Check disk space
df -h /
# Clean if needed
docker system prune -f
```

**If Step 5/6 (health timeout) fails:**
```bash
# Check which container is unhealthy
docker compose -f deployment/docker-compose.yml ps

# View logs for the failing service
docker compose -f deployment/docker-compose.yml logs api-gateway --tail=50
docker compose -f deployment/docker-compose.yml logs handbrake-service --tail=50
docker compose -f deployment/docker-compose.yml logs frontend --tail=50
```

---

## Step 4 — Manual Smoke Tests

Run each in order, stop if one fails:

### 4a. API Health
```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```
**Expected:** `"status": "healthy"`, `"handbrake_service": true`, `"database": "healthy"`

### 4b. Login
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "Token: ${TOKEN:0:20}..."
```
**Expected:** Token printed (not empty, not error)

### 4c. File Browser (verify mounts)
```bash
# Replace /mnt/tv with your actual INPUT_TV_PATH value
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/filesystem/browse?path=/mnt/tv" | python3 -m json.tool | head -30
```
**Expected:** JSON with file listing from your TV directory

### 4d. Frontend in Browser
Open `http://192.168.10.18:7474` — verify:
1. Login page loads (no blank page, no 502)
2. Login with `admin` / `admin123` → Dashboard
3. Open browser DevTools → Console — zero red errors
4. Navigate to Queue tab — loads without errors
5. Navigate to System tab — shows health data

### 4e. Verify HandBrake is inside the container
```bash
docker exec h2r-handbrake HandBrakeCLI --version
```
**Expected:** HandBrake version string printed

---

## Step 5 — If Everything Passes

```bash
# Commit any .env changes you want tracked (NEVER commit secrets — .env is gitignored)
git status  # Should show clean working tree

# Rename this prompt
mv documentation/prompts/SPRINT_01B_DEPLOY_AND_VERIFY.md \
   documentation/prompts/done__SPRINT_01B_DEPLOY_AND_VERIFY.md

git add documentation/prompts/
git commit -m "Sprint 01B complete: app deployed and verified on 192.168.10.18"
git push origin main
```

---

## Troubleshooting Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Container refuses to start` | Bad JWT_SECRET_KEY | Run `openssl rand -base64 32` and set in .env |
| `502 Bad Gateway` on frontend | api-gateway not yet healthy | Wait 30s, check `docker compose ps` |
| `handbrake_service: false` in health | handbrake container unhealthy | Check `docker logs h2r-handbrake` |
| File browser returns empty | Mount path wrong or doesn't exist | Verify `INPUT_TV_PATH` in .env matches actual host path |
| CORS errors in browser console | Old cached config | Hard refresh (Cmd+Shift+R / Ctrl+Shift+R) |
| `database is locked` in logs | WAL not active on first init | Restart containers: `docker compose restart` |

---

## STOP

This completes Sprint 1 deployment. Next prompt in sequence:

**`SPRINT_02_TESTING_AND_POLISH.md`**

Tasks for Sprint 2:
- WEA-120: Implement actual job cancellation (kill HandBrakeCLI subprocess)
- WEA-117: Playwright smoke tests against running stack
- WEA-121: Root README.md
- WEA-124–127: Comprehensive test suite

> ⚠️ Per agents.mdc rule 8: **Start a fresh Cursor chat** to run Sprint 02. Do not continue in this session.
