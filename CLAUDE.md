# CLAUDE.md — handbrake2resilio

Convert video files with HandBrakeCLI and sync output to Resilio Sync, managed via a web UI.
This file is the Claude Code entry point. The detailed rule set shared with Cursor lives in
`.cursor/rules/rules.mdc` and `.cursor/rules/agents.mdc` — read both before starting work.
Codex-specific guidance is in `AGENTS.md`.

## Architecture

| Service | Port | Role |
|---------|------|------|
| `api-gateway` | 8080 | Flask REST + WebSocket gateway, auth (JWT), SQLite |
| `handbrake-service` | 8081 | HandBrakeCLI worker, job queue, process management |
| `frontend` | 7474 | React UI served by Nginx |

## Key Commands

```bash
# Stack (compose reads .env from deployment/, which is git-ignored)
docker compose -f deployment/docker-compose.yml up --build -d
docker compose -f deployment/docker-compose.yml ps        # all 3 must be healthy
docker compose -f deployment/docker-compose.yml logs <service>
docker compose -f deployment/docker-compose.yml down

# Health checks
curl -sf http://localhost:8080/health
curl -sf http://localhost:8081/health

# Playwright smoke suite — browsers run in Docker ONLY, never on the host
docker build -f ui-frontend/Dockerfile.playwright -t h2r-playwright ui-frontend/ && \
  docker run --rm --network=host -e BASE_URL=http://localhost:7474 -e USE_LIVE_API=true h2r-playwright
```

Never run docker as sudo. If the shell predates docker-group membership, wrap commands:
`sg docker -c 'docker compose -f deployment/docker-compose.yml ps'`.

## Prompt Lifecycle (canonical)

- All execution prompts live in `documentation/prompts/`.
- Naming: `SPRINT_[NN][letter]_DESCRIPTION.md` (e.g. `SPRINT_06B_RULES_CONSOLIDATION_VIBECODING.md`).
  Legacy `PHASE_[NN]_` files remain as-is in the completed folder.
- Every prompt must include: acceptance criteria, a Verification section with concrete commands,
  a recommended model, and a STOP section naming the next prompt (or `none`).
- Create the prompt file BEFORE executing the work; confirm the running model matches the
  prompt's recommendation and state it in the first message.
- On completion (all acceptance criteria verified): rename with `done__` prefix, move to
  `documentation/prompts/completed prompts/`, commit, and push. On machines without GitHub
  credentials, commit locally and report the exact blocked push command in the final report.

## Model Guidance (Claude Code)

- Main session (orchestration, judgment, debugging): Claude Fable 5, or Opus 4.8 as fallback.
- Subagents for narrow pass/fail work (grep sweeps, link checks, single-endpoint verification):
  Sonnet 5; Haiku 4.5 for trivial mechanical checks. Never burn an expensive model on a check a
  cheap one can grade pass/fail.

## Critical Repo Facts & Traps

- `deployment/.env` is git-ignored; compose v2 reads `.env` from the compose file's directory.
  Required: `JWT_SECRET_KEY`, `MEDIA_INPUT_PATH`, `MEDIA_OUTPUT_PATH` (see `.env.example`).
- The media **output** directory must be writable by container uid 999
  (`chown 999:<group>`, mode 775) or HandBrake fails with `avio_open2 errno -13`.
- `shared/job_queue.py` `_run_conversion()` calls `/app/handbrake2resilio.sh`, which does not
  exist — that is a dead code path. The real worker is
  `handbrake-service/handbrake_service_simple.py`, which runs HandBrakeCLI directly.
  Do not "fix" jobs by creating that script.
- There is no Resilio integration in code: `MEDIA_OUTPUT_PATH` is simply a folder an external
  Resilio Sync instance watches. Resilio setup is out of scope of this codebase.
- Frontend changes require visual verification (browser or Playwright screenshot, including the
  CSS sanity check). "No JS errors" alone is never sufficient.
- Logs first: on any failure, read `docker compose logs <service>` before editing code.
- Never patch a running container — full clean rebuilds only.
- Default login: `admin` / `admin123`. Production host: 192.168.10.18 (touch only when a sprint
  explicitly scopes it). Dev VM: 192.168.10.39.

## Output Signature

Print 💣 at the beginning and 💥 at the end of every issue/prompt output, so the user knows the
rules were read.
