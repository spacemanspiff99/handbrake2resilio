# SPRINT_04C — E2E Verification: WEA-263 HandBrake Progress Monitoring Fix

> Reference: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`
> **Recommended model: Composer 2 / Auto**
> **Personas: Backend Engineer → QA Engineer**
> **Max 3 tasks. One binary success condition.**

💣

---

## Context

WEA-263 fixed a critical bug: `HandBrakeCLI` writes all progress output to **stderr**, not stdout.
The old implementation read from stdout (always empty during encoding) and tried to parse per-line
JSON (`--json` emits one blob only at encode end).

**The fix** replaces the stdout/JSON loop with a stderr line iterator using a compiled regex
`(\d+\.\d+) %` that matches HandBrake's text format:
```
Encoding: task 1 of 1, 47.38 % (89.32 fps, avg 92.14 fps, ETA 00h02m15s)
```

**Branch:** `spcmanspiff/wea-263-fix-progress-monitoring`
**PR #1** on GitHub — OPEN, targeting `main`

**Changed files:**
- `handbrake-service/handbrake_service_simple.py` — stderr reader + `_PROGRESS_RE`
- `handbrake-service/unit-tests/test_progress_parsing.py` — 4 new unit tests

---

## Acceptance Criteria

- [ ] 4/4 unit tests pass: `python3 -m pytest handbrake-service/unit-tests/test_progress_parsing.py -v`
- [ ] 136/136 integration tests pass: `python3 -m pytest testing/ -v`
- [ ] 52/52 Playwright tests pass in Docker
- [ ] `_PROGRESS_RE` regex confirmed in live container
- [ ] All 3 Docker containers healthy after rebuild
- [ ] PR #1 remains open for review/merge via standard pipeline

---

## Task 1 — Unit Tests

```bash
python3 -m pytest handbrake-service/unit-tests/test_progress_parsing.py -v
# PASS: 4/4
```

Tests cover:
- `test_extracts_progress_from_encoding_line` — 47.38% extracted correctly
- `test_extracts_100_percent` — 100.00% at encode end
- `test_no_match_on_non_progress_line` — opening lines ignored
- `test_no_match_on_empty_line` — empty string ignored

---

## Task 2 — Rebuild and Integration Test

Rebuild handbrake-service container to pick up the fix:

```bash
cd /home/akun/handbrake2resilio
docker compose -f deployment/docker-compose.yml build --no-cache handbrake-service
docker compose -f deployment/docker-compose.yml up -d handbrake-service
sleep 10

# Verify new code is live
docker exec h2r-handbrake python3 -c "import handbrake_service_simple; print('_PROGRESS_RE:', handbrake_service_simple._PROGRESS_RE.pattern)"
# Expected: _PROGRESS_RE: (\d+\.\d+) %

# Health check
curl -s http://localhost:8080/health | python3 -m json.tool
# Expected: "status": "healthy", "handbrake_service": true

# Integration tests
python3 -m pytest testing/ -v
# PASS: 136/136
```

---

## Task 3 — Playwright E2E Tests

```bash
docker build -f ui-frontend/Dockerfile.playwright -t h2r-playwright ui-frontend/
docker run --rm --network=host -e BASE_URL=http://localhost:7474 -e USE_LIVE_API=true h2r-playwright
# PASS: 52/52
```

---

## Verification Results (Executed 2026-04-18)

| Check | Result |
|-------|--------|
| Unit tests (progress parsing) | ✅ 4/4 |
| Integration tests | ✅ 136/136 |
| Playwright UI tests | ✅ 52/52 |
| `_PROGRESS_RE` in live container | ✅ Confirmed |
| All 3 containers healthy | ✅ |
| PR open for review | ✅ PR #1 |

---

## Git Operations (after successful verification)

```bash
# Rename prompt to done__
mv documentation/prompts/SPRINT_04C_E2E_VERIFICATION.md \
   "documentation/prompts/completed prompts/done__SPRINT_04C_E2E_VERIFICATION.md"

git add documentation/prompts/
git commit -m "docs: mark SPRINT_04C complete — WEA-263 progress monitoring fix verified"
git push origin spcmanspiff/wea-263-fix-progress-monitoring
```

---

## STOP

Next: Per `agents.mdc` rule 7 — **do NOT merge or deploy in this session**.
Use the multi-agent release pipeline:
- **Session B**: Merge `spcmanspiff/wea-263-fix-progress-monitoring` → `main` (or `dev`) and verify
- **Session C**: Deploy + production verification

> ⚠️ Per `agents.mdc` rule 8: **Start a fresh Cursor chat** for Session B.
