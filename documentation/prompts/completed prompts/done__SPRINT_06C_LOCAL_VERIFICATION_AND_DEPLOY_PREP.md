💣

# SPRINT_06C — Full Local Verification + Production Deploy Prep (No Prod Contact)

## Recommended Model

- **Primary (main session): Claude Fable 5** (`claude-fable-5`); fallback **Opus 4.8**.
- **Subagents: Sonnet 5** for narrow pass/fail checks (log scans, script review sweeps); **Haiku 4.5** for trivial mechanical checks.
- Per rules: confirm the running model matches this recommendation and state it in the first message.

## Context

- Read `CLAUDE.md`, `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc` before starting (this prompt references and follows `rules.mdc`).
- Dev VM 192.168.10.39; stack running since SPRINT_06A; rules consolidated in SPRINT_06B (main @ `c6dcbf6`, pushed; mirror verified).
- **HARD CONSTRAINT: zero contact with production 192.168.10.18 — no SSH, no curl, no deploy. Prod deploy is SPRINT_06D and requires the user's explicit go-ahead.**
- Docker via `sg docker -c '...'` where the shell predates docker-group membership.
- Test video from 06A should exist at `~/media/input/testsrc_30s.mp4`; regenerate with ffmpeg if missing.

## Goal

Prove the local stack end-to-end again (fresh evidence, not 06A's), run the unit suites, and make the production deploy tooling truthful — without executing it. Everything verified by command output.

## Tasks

### T1 — Local E2E re-verification (evidence-fresh)
1. `sg docker -c 'docker compose -f deployment/docker-compose.yml ps'` → all 3 healthy.
2. `curl -sf localhost:8080/health` and `curl -sf localhost:8081/health` → 200, healthy JSON.
3. API login as `admin`/`admin123` → JWT issued.
4. Submit a conversion of the real test video via the API; poll to completion; output exists in `~/media/output`, non-trivially sized, `ffprobe` confirms a valid video stream.
5. Cancellation: submit a second job, cancel mid-run; status becomes `cancelled`; no orphan `HandBrakeCLI` process (`pgrep -a HandBrakeCLI` empty inside/outside container).
6. Playwright smoke suite in Docker (covers the UI path incl. CSS sanity): standard command from `CLAUDE.md`; full-page screenshot saved to `~/sprint06c-artifacts/`.
7. Survivability: `docker compose restart`; all 3 healthy again; the completed job from step 4 still visible via API (SQLite persistence).

### T2 — Unit test suites (in Docker only, nothing installed on the host)
- Discover and run the repo's unit suites (e.g. under `testing/`, `api-gateway/`, `handbrake-service/`, `ui-frontend/tests/`) inside containers or throwaway Docker images. Report pass/fail counts per suite.
- Fix only genuine test-vs-code drift (test expects old behavior that legitimately changed); smallest change, noted in the report. Do NOT rewrite app logic overnight. Pre-existing failures that indicate real app bugs get documented, not papered over.

### T3 — Deploy prep (files only — NEVER execute against prod)
- Fix stale references in `deployment/.cursor-rules` and `deployment/deploy002.sh`: container names `handbrake2resilio-*` → actual `h2r-*`; frontend port 3000 → actual 7474; any referenced paths that no longer exist.
- Review `deploy002.sh` line-by-line (subagent sweep + main-session judgment) for anything that would fail or damage prod when eventually run; document findings in the report. Verification is `bash -n` + review, not execution.

### T4 — Close out
- Guard: `git diff --name-only` touches only `deployment/.cursor-rules`, `deployment/deploy002.sh`, `documentation/prompts/**`, test files (if T2 drift fixes), and artifacts/docs — no app-logic changes unless a T2-documented smallest-fix.
- Stack healthy at end (criterion 1 re-run).
- Author `documentation/prompts/SPRINT_06D_PROD_DEPLOY.md` (next sprint, NOT executed — first line must state it requires the user's explicit go-ahead).
- Rename this prompt `done__`, move to completed prompts, commit, push.

## Acceptance Criteria

1. All 3 containers healthy at start AND end; both health endpoints return 200.
2. Fresh end-to-end conversion of a real video completes via API; output probes valid (`ffprobe` shows video stream, size > 1 MB).
3. Cancellation verified: status `cancelled`, no orphan HandBrakeCLI process.
4. Playwright smoke suite passes in Docker incl. CSS sanity; screenshot saved under `~/sprint06c-artifacts/`.
5. Stack survives `docker compose restart`; pre-restart completed job still queryable.
6. Unit suites executed in Docker with reported pass/fail counts; any failure either fixed (test-drift, smallest change) or documented as a real-bug finding.
7. `grep -n "handbrake2resilio-\|:3000\|port 3000" deployment/.cursor-rules deployment/deploy002.sh` → no stale matches remain (allowing legitimate uses if any are proven correct); `bash -n deployment/deploy002.sh` passes.
8. Zero contact with 192.168.10.18 (no command in the transcript targets it).
9. `SPRINT_06D_PROD_DEPLOY.md` exists in `documentation/prompts/`, marked as gated on user go-ahead.
10. This prompt renamed `done__`, moved, committed, pushed successfully.

## Verification (paste outputs in final report)

```bash
sg docker -c 'docker compose -f deployment/docker-compose.yml ps'
curl -sf http://localhost:8080/health | head -c 400; curl -sf http://localhost:8081/health | head -c 400
ls -lh ~/media/output/ | tail -5
ffprobe -v error -show_entries format=duration,size ~/media/output/<newest output>
pgrep -a HandBrakeCLI; echo "exit=$?"   # expect exit=1 after cancel test
ls ~/sprint06c-artifacts/
bash -n deployment/deploy002.sh && echo SYNTAX_OK
grep -n "handbrake2resilio-\|port 3000\|:3000" deployment/.cursor-rules deployment/deploy002.sh; echo "exit=$?"
git status --short
git log --oneline -2
```

## STOP

Next prompt: `SPRINT_06D_PROD_DEPLOY.md` — **requires the user's explicit go-ahead before execution; do not start it autonomously.**

💥
