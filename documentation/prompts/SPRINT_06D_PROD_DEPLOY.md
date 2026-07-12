💣

# SPRINT_06D — Production Deploy to 192.168.10.18

> **⛔ GATED: DO NOT EXECUTE WITHOUT THE USER'S EXPLICIT GO-AHEAD.**
> The user must say, in their own words in a live session, to deploy to production.
> Authoring this prompt is NOT authorization. No autonomous session may start it.

## Recommended Model

- **Primary: Claude Fable 5** (`claude-fable-5`); fallback **Opus 4.8**. Subagents: Sonnet 5 / Haiku 4.5 for pass/fail checks.
- Confirm the running model matches and state it in the first message.

## Context

- Read `CLAUDE.md`, `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc` first (this prompt follows `rules.mdc`).
- SPRINT_06C verified the full stack locally (114 unit + 22 e2e pytest + 52 Playwright tests green) and produced `deployment/deploy003.sh`, which supersedes the dead deploy002.sh. Review findings from 06C's report must be applied before running it.
- Production: `akun@192.168.10.18` over SSH. Requires a machine with SSH access to prod (the dev VM has it).
- `deployment/.cursor-rules` governs prod deploys: clean rebuild, no incremental updates, disk check first.

## Tasks

1. **Preflight**: confirm user go-ahead is on record in the current session; `ssh akun@192.168.10.18 'df -h /; docker --version'`; verify what is currently running on prod and report it BEFORE touching anything.
2. **Deploy**: run `bash deployment/deploy003.sh` from the repo root. Logs first on any failure; full clean rebuild only.
3. **Verify end-to-end on prod with real data**: all 3 containers healthy; both health endpoints 200; login works; a real ~30s test video converts through the UI at `http://192.168.10.18:7474`; output probes as valid video; cancellation works; Playwright smoke suite from the dev VM with `BASE_URL=http://192.168.10.18:7474` passes incl. CSS sanity + screenshot.
4. **Harden**: change the default admin password (or document it as an explicit accepted risk with the user).
5. **Survivability**: `docker compose restart` on prod; all healthy; data intact.
6. Close out: `done__` rename + move, commit, push, final report with verification outputs.

## Acceptance Criteria

1. User go-ahead quoted in the report.
2. Prod: 3 containers healthy; both /health 200; UI conversion of a real video completes; output valid via ffprobe; cancel works; Playwright (incl. CSS sanity) passes against prod; restart survivability with data intact.
3. Container creation timestamps postdate the deployed code (fresh artifact check).
4. Default-password decision recorded.
5. Prompt completed per lifecycle (done__, moved, committed, pushed).

## Verification

```bash
ssh akun@192.168.10.18 'docker compose -f ~/h2r-deploy/deployment/docker-compose.yml ps'
ssh akun@192.168.10.18 'curl -sf http://localhost:8080/health | head -c 300'
ssh akun@192.168.10.18 'curl -sf http://localhost:8081/health | head -c 300'
curl -sf http://192.168.10.18:7474 >/dev/null && echo FRONTEND_OK
# + UI conversion evidence, ffprobe output, Playwright results, restart check
```

## STOP

Next prompt: `none` — after production is verified, the sprint queue is empty. Future work (e.g. Resilio Sync integration, admin-password management, prod monitoring) should be scoped as new sprints with the user.

💥
