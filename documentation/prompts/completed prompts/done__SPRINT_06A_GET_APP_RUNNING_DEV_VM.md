💣

# SPRINT_06A — Get the Full Stack Running on the Dev VM (Do Not Stop Until Working)

## Recommended Model

- **Primary (main session): Claude Fable 5** (`claude-fable-5`). This sprint is a long autonomous run whose hard part is judgment — diagnosing whatever the Docker build, compose networking, or HandBrake runtime throws up — not typing volume. Fable's stronger debugging pays for itself here in fewer wasted rebuild cycles.
- **Fallback primary: Claude Opus 4.8** (`claude-opus-4-8`, fast mode on) if Fable is unavailable or budget-constrained.
- **Subagents: Sonnet 5** (`claude-sonnet-5`) for narrow parallel work — log scanning, grepping the codebase, verifying one endpoint. **Haiku 4.5** for trivial mechanical checks. Never spawn a Fable/Opus subagent for work a Sonnet can verify pass/fail.
- Per rules: **before starting, confirm the running model matches this recommendation** and state it in the first message.

## Context

- Read `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`, and `AGENTS.md` before starting.
- Host: dev VM `dev-handbrake2resilio` (192.168.10.39, Ubuntu, 10 CPU / 15 GB RAM / 27 GB disk). Production (192.168.10.18) is **out of scope** for this sprint.
- Repo is checked out at `/home/akun/handbrake2resilio` on `main`.
- Known host gaps: **Docker is not installed**; `gh` CLI and GitHub credentials are absent.
- Known repo traps (do NOT get misled):
  - `documentation/RESUME_ON_NEW_MACHINE.md` and `documentation/NEXT_STEPS.md` are stale — they reference `requirements.txt`, `deploy_production.sh`, and `deployment_readiness_check.py`, none of which exist. **The README quick start is the accurate entry point.**
  - `shared/job_queue.py` `_run_conversion()` calls `/app/handbrake2resilio.sh`, which does not exist. This is a dead code path — the real worker is `handbrake-service/handbrake_service_simple.py`, which runs HandBrakeCLI directly. Do not "fix" jobs by creating that script.
  - There is no Resilio integration in code; `MEDIA_OUTPUT_PATH` is simply a folder Resilio Sync would watch. Resilio setup is out of scope.

## Goal

A fully working application on this dev VM: all three containers healthy, login works, a **real video file converts end-to-end through the UI**, and the Playwright smoke suite passes. **Do not stop, summarize, or declare partial success until every acceptance criterion below passes.** If a build or test fails, debug logs-first and iterate. The only permitted stops are hard external blockers (sudo password prompt, network outage) — and then report the exact command and blocker, per `AGENTS.md`.

## Tasks

### T1 — Install Docker Engine + Compose v2
- Install from Docker's official apt repo (not `docker.io`), add `akun` to the `docker` group, verify `docker run hello-world` works **without sudo** (rules: never run docker as sudo). `newgrp docker` or re-login as needed.

### T2 — Configure environment
- `cp .env.example .env`; set `JWT_SECRET_KEY=$(openssl rand -base64 32)`.
- Create `~/media/input` and `~/media/output`; set `MEDIA_INPUT_PATH`/`MEDIA_OUTPUT_PATH` to them.
- Generate a real test video into the input dir (e.g. `ffmpeg -f lavfi -i testsrc=duration=30:size=1280x720:rate=25 -f lavfi -i sine -c:v libx264 -c:a aac -shortest ~/media/input/testsrc_30s.mp4` — install ffmpeg or generate inside a container if the host lacks it). A synthetic file is fine; a zero-byte or fake file is not.

### T3 — Build and launch the stack
- Disk check first (rules: fail if >90% used): `df -h /`.
- `docker compose -f deployment/docker-compose.yml up --build -d`.
- All three containers must reach `healthy` (`docker compose ps`). If a build fails: read the full build log before touching code. Full clean rebuilds only — never patch a running container.

### T4 — Verify end-to-end with real data
- `curl -f http://localhost:8080/health` and `curl -f http://localhost:8081/health` return 200 with healthy status JSON.
- Log in via the API as `admin`/`admin123`, obtain a JWT.
- Through the API (and confirm the same flow works in the UI at `http://192.168.10.39:7474`): browse the file browser to the test video, submit a conversion job, watch progress to completion.
- Confirm the output file exists in `~/media/output`, is non-trivially sized, and `ffprobe` (or HandBrakeCLI --scan) confirms a valid video stream.
- Cancel-job path: submit a second job and cancel it mid-run; confirm status becomes cancelled and the HandBrakeCLI process is gone.

### T5 — Playwright smoke suite in Docker
- Per rules, browsers run in Docker only, never on the host:
  `docker build -f ui-frontend/Dockerfile.playwright -t h2r-playwright ui-frontend/ && docker run --rm --network=host -e BASE_URL=http://localhost:7474 -e USE_LIVE_API=true h2r-playwright`
- Smoke must pass including the CSS sanity test; save the full-page screenshot for human review.

### T6 — Survivability check
- `docker compose restart`; confirm all containers return to healthy and a previously created job is still visible (SQLite persistence via the `app-data` volume).

## Acceptance Criteria

1. `docker compose ps` shows `api-gateway`, `handbrake-service`, and `frontend` all **healthy**, running as non-root user without sudo.
2. Both `/health` endpoints return HTTP 200.
3. A real ~30s test video submitted **through the UI** converts to completion; output file plays/probes as valid video.
4. Job cancellation works (status `cancelled`, no orphan HandBrakeCLI process).
5. Playwright smoke suite passes in Docker, including CSS sanity; screenshot artifact saved. "No JS errors" alone does NOT satisfy this — the UI must be visually styled.
6. Stack survives `docker compose restart` with data intact.
7. No secrets committed; `.env` stays untracked (verify `git status` is clean of it).

## Verification (run all, paste output in final report)

```bash
docker compose -f deployment/docker-compose.yml ps
curl -sf http://localhost:8080/health | head -c 400
curl -sf http://localhost:8081/health | head -c 400
ls -lh ~/media/output/
ffprobe -v error -show_entries format=duration,size ~/media/output/*
git status --short
```

## Working Rules for This Sprint

- Logs first: on any failure, read `docker compose logs <service>` before editing code.
- If code changes are genuinely required to pass (e.g. a real bug surfaces), make the smallest fix, note it in the report, and commit it with a clear message — but do not push until the sprint report is done.
- Do not mix in documentation cleanup, rules changes, or production deploy — those are the next sprints.

## Final Report Must Include

Changed files (if any), verification command outputs, screenshot path, any blocked checks with the exact blocking command, and the STOP handoff.

## STOP

Next prompt: `SPRINT_06B_RULES_CONSOLIDATION_VIBECODING.md` (consolidate CLAUDE.md/.cursor rules/AGENTS.md, de-conflict them, verify mirror to the vibecoding repo). Do not begin it in this session.

💥
