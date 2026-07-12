# Resume handbrake2resilio on a New Machine

Short, accurate path to a running stack on a fresh machine. The app is fully Dockerized —
there is no host Python environment to set up.

## Prerequisites

- Docker Engine + Compose v2 (install from Docker's official apt repo, not `docker.io`).
  Add your user to the `docker` group; never run docker as sudo.
- Git access to `https://github.com/spacemanspiff99/handbrake2resilio` (branch `main`).

## Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/spacemanspiff99/handbrake2resilio.git
cd handbrake2resilio
git log --oneline -5   # confirm you're current

# 2. Configure environment (compose v2 reads .env from deployment/)
cp .env.example deployment/.env
# Edit deployment/.env:
#   JWT_SECRET_KEY=$(openssl rand -base64 32)
#   MEDIA_INPUT_PATH=/path/to/media/input
#   MEDIA_OUTPUT_PATH=/path/to/media/output
mkdir -p ~/media/input ~/media/output
# Output dir must be writable by container uid 999:
sudo chown 999:$(id -gn) ~/media/output && chmod 775 ~/media/output

# 3. Build and launch
docker compose -f deployment/docker-compose.yml up --build -d
docker compose -f deployment/docker-compose.yml ps   # all 3 services healthy
```

Open `http://<host>:7474` — default login `admin` / `admin123`.

## Verify

```bash
curl -sf http://localhost:8080/health
curl -sf http://localhost:8081/health
# Playwright smoke suite (browsers run in Docker only, never on the host):
docker build -f ui-frontend/Dockerfile.playwright -t h2r-playwright ui-frontend/ && \
  docker run --rm --network=host -e BASE_URL=http://localhost:7474 -e USE_LIVE_API=true h2r-playwright
```

## Before Working

- Read `CLAUDE.md` (Claude Code entry point) and `.cursor/rules/rules.mdc` +
  `.cursor/rules/agents.mdc` (shared rule set). Codex uses `AGENTS.md`.
- Find the current sprint in `documentation/prompts/` — completed work is in
  `documentation/prompts/completed prompts/` (files prefixed `done__`).
- Hosts: dev VM `192.168.10.39`; production `192.168.10.18` (touch production only when a
  sprint explicitly scopes it).
