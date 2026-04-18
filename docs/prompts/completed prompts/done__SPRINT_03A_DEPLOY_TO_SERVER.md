# SPRINT_03A — Deploy to 192.168.10.18 for E2E Testing with Real Video Files

> Reference: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`
> **Recommended model: Composer 2 / Auto**
> **Personas: Backend Engineer → QA Engineer**
> **Max 3 tasks. One binary success condition.**

💣

---

## Context

The app is fully built, tested (52/52 Playwright tests passing), and the CSS regression is fixed. This prompt deploys the stack to the home server at `192.168.10.18` and verifies it works end-to-end with real video files.

**What's ready:**
- Clean Docker stack: api-gateway (:8080), handbrake-service (:8081), frontend (:7474)
- CSS pipeline fixed (`tailwind.config.js` + `postcss.config.js` in Dockerfile)
- `.env` at project root with real JWT key
- `deployment/deploy001.sh` — full deploy script with health checks and smoke tests
- 52/52 Playwright tests pass locally

**What's needed on the server:**
- Docker + Docker Compose v2 installed
- SSH access configured (see Step 0 below)
- Real media paths set in `.env`

---

## Pre-flight: SSH Setup (do this once from dev machine)

```bash
# From your dev machine — copy SSH key to server
ssh-copy-id akun@192.168.10.18

# Verify it works (should NOT prompt for password)
ssh akun@192.168.10.18 "echo SSH OK"
```

If `ssh-copy-id` fails (no key exists yet):
```bash
ssh-keygen -t ed25519 -C "h2r-deploy"
ssh-copy-id akun@192.168.10.18
```

---

## Step 1 — Server Prerequisites Check

SSH into the server and verify:

```bash
ssh akun@192.168.10.18

# Docker available
docker --version          # must be 20+
docker compose version    # must be v2 (not docker-compose v1)

# Disk space
df -h /                   # must be < 80% used

# Git
git --version

# Check real media paths exist
ls /mnt/tv 2>/dev/null || echo "TV path missing"
ls /mnt/movies 2>/dev/null || echo "Movies path missing"
# Note the actual paths — you'll need them for .env
```

If Docker is missing:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker akun
# Log out and back in
```

---

## Step 2 — Clone / Pull Repo on Server

```bash
ssh akun@192.168.10.18

# If first time:
git clone https://github.com/spacemanspiff99/handbrake2resilio.git
cd handbrake2resilio

# If already cloned:
cd handbrake2resilio
git pull origin main
git log --oneline -3   # confirm ea00a98 or later is HEAD
```

---

## Step 3 — Configure .env on Server

```bash
# On the server, in ~/handbrake2resilio/
cp .env.example .env
```

Edit `.env` — fill in ALL values:

```bash
# Generate a real key (REQUIRED — app refuses to start without it)
JWT_SECRET_KEY=$(openssl rand -base64 32)
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> /tmp/key.txt  # save it

# Set to your ACTUAL media paths on this server
MEDIA_INPUT_PATH=/mnt/tv          # or wherever your source video files are
MEDIA_OUTPUT_PATH=/mnt/resilio    # or wherever Resilio Sync watches

# Ports — leave defaults unless conflicts
API_PORT=8080
HANDBRAKE_PORT=8081
FRONTEND_PORT=7474

MAX_CONCURRENT_JOBS=2
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

Verify before proceeding:
```bash
grep JWT_SECRET_KEY .env | grep -v "change-me" && echo "JWT OK"
ls $(grep MEDIA_INPUT_PATH .env | cut -d= -f2) | head -5  # must list real files
ls $(grep MEDIA_OUTPUT_PATH .env | cut -d= -f2) && echo "Output path OK"
```

---

## Step 4 — Deploy

```bash
# From project root on the server
cd ~/handbrake2resilio
bash deployment/deploy001.sh
```

**Expected output:** All 6 steps pass with `[OK]`, final summary shows URLs.

**If build fails (disk space):**
```bash
docker system prune -af
bash deployment/deploy001.sh
```

**If health timeout (Step 5 fails):**
```bash
docker compose -f deployment/docker-compose.yml logs --tail=50
```

---

## Step 5 — Manual Smoke Tests

### 5a. API health
```bash
curl -s http://localhost:8080/health | python3 -m json.tool
```
**Expected:** `"status": "healthy"`, `"handbrake_service": true`, `"database": "healthy"`

### 5b. Login
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "Token: ${TOKEN:0:20}..."
```
**Expected:** Token printed (not empty)

### 5c. File browser — verify media mount
```bash
MEDIA_IN=$(grep MEDIA_INPUT_PATH .env | cut -d= -f2)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/filesystem/browse?path=${MEDIA_IN}" \
  | python3 -m json.tool | head -20
```
**Expected:** JSON listing with real video files

### 5d. HandBrake CLI inside container
```bash
docker exec h2r-handbrake HandBrakeCLI --version
```
**Expected:** HandBrake version string

### 5e. Frontend in browser
Open `http://192.168.10.18:7474` and verify:
1. Login page loads **with styling** (not raw text — buttons are blue, background is grey)
2. Login with `admin` / `admin123` → Dashboard
3. DevTools Console → zero red errors
4. File browser opens and shows real video files from `MEDIA_INPUT_PATH`

---

## Step 6 — E2E Test: Submit a Real Transcoding Job

1. Open `http://192.168.10.18:7474`
2. Login → Dashboard
3. Click **New Job**
4. Browse to a small test video file (< 500 MB recommended for first test)
5. Select output preset (default is fine)
6. Submit job
7. Navigate to **Queue** tab — verify job appears with status `pending` then `running`
8. Wait for completion — verify:
   - Job status changes to `completed`
   - Output file appears in `MEDIA_OUTPUT_PATH`
   - File is a valid video: `ffprobe /path/to/output/file.mkv`

---

## Acceptance Criteria

- [ ] `docker compose ps` shows all 3 containers `healthy`
- [ ] `http://192.168.10.18:7474` loads with **full Tailwind styling** (not raw text)
- [ ] Login works with `admin` / `admin123`
- [ ] File browser shows real video files from `MEDIA_INPUT_PATH`
- [ ] A real transcoding job completes successfully
- [ ] Output file exists in `MEDIA_OUTPUT_PATH` and is a valid video
- [ ] No red errors in browser DevTools console

---

## Troubleshooting Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| UI is raw text / unstyled | Old cached image | `docker compose down && docker rmi deployment-frontend && bash deployment/deploy001.sh` |
| `502 Bad Gateway` on frontend | api-gateway not yet healthy | Wait 30s, check `docker compose ps` |
| `handbrake_service: false` in health | handbrake container unhealthy | `docker logs h2r-handbrake` |
| File browser empty | Mount path wrong | Verify `MEDIA_INPUT_PATH` in `.env` matches actual host path |
| Job stuck in `pending` | handbrake-service not healthy | `docker compose restart handbrake-service` |
| `database is locked` | WAL not active | `docker compose restart` |

---

## CSS Verification (mandatory before declaring success)

Run this after deploy to confirm the CSS fix is in the deployed image:

```bash
docker run --rm deployment-frontend \
  find /usr/share/nginx/html/static/css -name "*.css" -exec wc -c {} +
# FAIL if < 5000 bytes
```

---

## Git Operations (after successful deploy)

```bash
# On dev machine — rename prompt to done__
mv documentation/prompts/SPRINT_03A_DEPLOY_TO_SERVER.md \
   "documentation/prompts/completed prompts/done__SPRINT_03A_DEPLOY_TO_SERVER.md"

git add documentation/prompts/
git commit -m "docs: mark SPRINT_03A complete — deployed and verified on 192.168.10.18"
git push origin main
```

---

## STOP

Next prompt: `SPRINT_03B_SERVER_HARDENING.md` (change default password, set up log rotation, configure Resilio Sync output path)

> ⚠️ Per agents.mdc rule 8: **Start a fresh Cursor chat** to run this prompt.
