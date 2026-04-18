# Resume handbrake2resilio on a New Machine

Paste the entire contents of this file into Cursor as your first message.

---

## Setup Commands

Run these in order in your terminal:

```bash
# 1. Clone and enter the repo
git clone https://github.com/spacemanspiff99/handbrake2resilio.git
cd handbrake2resilio

# 2. Confirm you're on main and up to date
git checkout main
git pull origin main
git log --oneline -5

# 3. Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt   # for running tests

# 4. Copy env file and fill in values
cp .env.example .env
# Edit .env — key vars listed below

# 5. Open in Cursor
cursor .
```

---

## Key Environment Variables (`.env`)

```bash
# Security
JWT_SECRET_KEY=$(openssl rand -base64 32)
BCRYPT_ROUNDS=12
JWT_EXPIRATION_HOURS=24

# Storage paths (adjust to your machine)
TV_SOURCE=/mnt/tv
MOVIES_SOURCE=/mnt/movies
ARCHIVE_DESTINATION=/mnt/archive

# Network
HOST=0.0.0.0
PORT=8080
CORS_ORIGINS="http://192.168.10.18:3000"

# Resources
MAX_CONCURRENT_JOBS=8
CPU_LIMIT=80
MEMORY_LIMIT=80
MIN_MEMORY_GB=2.0
MIN_DISK_GB=5.0

# Video defaults
DEFAULT_QUALITY=20
DEFAULT_RESOLUTION=1920x1080
DEFAULT_VIDEO_BITRATE=2000
DEFAULT_AUDIO_BITRATE=128
```

---

## Project Structure

```
handbrake2resilio/
├── api-gateway/          # Flask API + auth + job routing
├── handbrake-service/    # HandBrake transcoding worker
├── ui-frontend/          # React frontend
├── shared/               # Shared utilities, config, models
├── testing/              # E2E and integration tests
├── deployment/           # Docker, deploy scripts
├── documentation/
│   └── prompts/          # Sprint prompts (active + completed)
└── data/                 # SQLite DB, logs
```

---

## Current State (as of 2026-04-05)

- **Branch**: `main`
- **Latest commit**: `8ff9b13` — Sprint 2D: E2E integration tests + full stack verification
- **Status**: 5/6 deployment readiness checks passing
  - ✅ Configuration system
  - ✅ Job queue (SQLite-backed, thread-safe)
  - ✅ Authentication (JWT + bcrypt + RBAC)
  - ✅ Docker files (production-hardened)
  - ✅ Dependencies
  - ⚠️ Auth unit tests have minor failures (does not affect runtime)

---

## Active Sprint Prompts

These are in `documentation/prompts/` and have NOT been completed yet:

- `SPRINT_02A_JOB_CANCELLATION_AND_README.md`
- `SPRINT_02B_UNIT_TESTS.md`
- `SPRINT_02C_PLAYWRIGHT_UI_TESTS.md`
- `SPRINT_02D_E2E_INTEGRATION.md`

Completed prompts are in `documentation/prompts/completed prompts/`.

---

## Rules & Agent Config

- Workspace rules: `.cursor/rules/rules.mdc` and `.cursor/rules/agents.mdc`
- Always read these before starting work
- Use **Composer 2 / Auto** model for most tasks (not Claude Opus)
- One agent = one domain; max 3 tasks per agent
- Always have acceptance criteria in prompts
- Move completed prompts to `documentation/prompts/completed prompts/` with `done__` prefix

---

## Recommended First Message to Cursor

> I'm resuming work on the `handbrake2resilio` project. I'm on branch `main`, latest commit `8ff9b13` (Sprint 2D — E2E integration tests). The system is 5/6 deployment-ready; the remaining gap is minor auth test failures. Please read `.cursor/rules/rules.mdc` and `.cursor/rules/agents.mdc` before we begin. What should we work on next based on `documentation/NEXT_STEPS.md`?

---

💥
