# Issue Log — Recurring Bug Categories

This log tracks **recurring** failure patterns. When a bug appears with a known root cause, it gets categorized (`CAT-*`) and a prevention rule lives in the relevant `.cursor/rules/*.mdc` file.

See [core.mdc](../../.cursor/rules/core.mdc) § Issue Log for the mandatory agent actions when closing a bug.

---

## How this log is used

1. **On closing any bug**: check whether the root cause matches an existing category below. If yes, add a row. If no, add to § Open Items.
2. **On pattern recurrence** (same root cause, 2+ issues): create a new `## CAT-N` section, back-fill matching issues, add a prevention rule to the relevant `.mdc` file **in the same PR**.
3. **On adding a prevention rule**: record the rule reference (file + section) in the `Prevention Added` column of every affected row.

### Row format for each CAT

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| WEA-xxx | YYYY-MM-DD | Short title | One-line root cause | `frontend.mdc` § Section Name |

---

## CAT-F1 — Frontend CSS / Build Bugs

Symptoms: unstyled UI, blank page with no JS errors, Tailwind classes not rendered, CSS bundle suspiciously small.

**Prevention rule**: [frontend.mdc](../../.cursor/rules/frontend.mdc) § CSS Sanity, § Frontend Dockerfile

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| [WEA-188](https://linear.app/weather-app-eli/issue/WEA-188) | 2026-04-07 | Rebuild frontend Docker image and verify CSS bundle fix | Commit `7a0641e` rewrote `ui-frontend/Dockerfile` from `COPY . .` to explicit copies but omitted `tailwind.config.js` and `postcss.config.js`. Tailwind/PostCSS produced an empty CSS bundle; UI rendered as raw unstyled HTML. No JS errors, so "app works" checks passed. | `frontend.mdc` § Frontend Dockerfile (explicit COPY + post-build `stat -c%s dist/assets/*.css -gt 5000`); `frontend.mdc` § CSS Sanity (3-check hard gate) |
| [WEA-189](https://linear.app/weather-app-eli/issue/WEA-189) | 2026-04-07 | Add CSS sanity test to Playwright smoke suite | Prevention enablement for WEA-188. No existing smoke test would have caught the empty CSS bundle. | `frontend.mdc` § CSS Sanity (assertion: `cssRules.length > 50` OR bundle >5 KB) |
| [WEA-190](https://linear.app/weather-app-eli/issue/WEA-190) | 2026-04-07 | Add full-page screenshot capture to Playwright smoke tests | Prevention enablement for WEA-188. Screenshot on every run gives humans a visual confirmation the CSS sanity assertion corresponds to a correctly-rendered UI. | `frontend.mdc` § CSS Sanity (third check: full-page screenshot on every run) |

---

## CAT-F2 — Frontend Dockerfile Build Bugs

Symptoms: missing config files in built image, `COPY . .` hiding misconfigured layers, build succeeds but runtime assets are incomplete.

**Prevention rule**: [frontend.mdc](../../.cursor/rules/frontend.mdc) § Frontend Dockerfile, [devops.mdc](../../.cursor/rules/devops.mdc) § Clean Deployment

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| [WEA-137](https://linear.app/weather-app-eli/issue/WEA-137) | 2026-03-24 | Fix frontend Docker build and nginx proxy | First-pass frontend Docker build failing (pre-WEA-188). Build produced a partial image; nginx `proxy_pass` not configured for `/api/*`. | `devops.mdc` § Post-deploy API Contract Verification (verify through nginx, not only container port); `frontend.mdc` § Frontend Dockerfile |
| [WEA-188](https://linear.app/weather-app-eli/issue/WEA-188) | 2026-04-07 | Rebuild frontend Docker image and verify CSS bundle fix | `COPY . .` rewrite silently dropped `*.config.js` files; empty CSS bundle shipped without the build failing. | `frontend.mdc` § Frontend Dockerfile (explicit COPY rule; copy every `*.config.js` before `npm run build`; fail image if `dist/assets/*.css` <5 KB) |

---

## CAT-P1 — Playwright / Browser Test Gaps

Symptoms: smoke tests pass while the UI is visibly broken; objective checks missing; host dependency drift between environments.

**Prevention rule**: [frontend.mdc](../../.cursor/rules/frontend.mdc) § Playwright Containerization, § Selector Stability, § CSS Sanity

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| [WEA-189](https://linear.app/weather-app-eli/issue/WEA-189) | 2026-04-07 | Add CSS sanity test to Playwright smoke suite | Smoke tests only checked DOM presence and HTTP 200; could not detect empty CSS bundle. | `frontend.mdc` § CSS Sanity (HARD GATE: assertion must run on every smoke suite) |
| [WEA-190](https://linear.app/weather-app-eli/issue/WEA-190) | 2026-04-07 | Add full-page screenshot capture to Playwright smoke tests | No visual artefact produced per run — humans could not retroactively verify rendering quality. | `frontend.mdc` § CSS Sanity (screenshot on every run as third required check) |

---

## CAT-A1 — API Contract Breaks (frontend ↔ backend route drift)

Symptoms: frontend calls endpoints that don't exist on the backend; 404 storms in the Network tab; same bug re-emerges after refactors.

**Prevention rule**: [backend.mdc](../../.cursor/rules/backend.mdc) § API Contract Change Checklist, [devops.mdc](../../.cursor/rules/devops.mdc) § Post-deploy API Contract Verification

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| [WEA-116](https://linear.app/weather-app-eli/issue/WEA-116) | 2026-03-22 | Align frontend API calls to existing backend endpoints | First-pass mismatch: `GET /api/system/health` vs `GET /health`; `POST /api/queue` vs `POST /api/jobs/add`; `DELETE /api/queue/jobs/:id` vs `POST /api/jobs/cancel`. Frontend `api.js` had been written speculatively against a non-existent backend shape. | (partial — no post-deploy contract check yet) |
| [WEA-133](https://linear.app/weather-app-eli/issue/WEA-133) | 2026-03-24 | Align frontend API calls to backend routes | **Recurrence of WEA-116 after Sprint 01 folder reorg.** Same root cause: no post-deploy contract check, no TypeScript types shared between frontend and backend, no single source of truth for route names. | `backend.mdc` § API Contract Change Checklist (serializer + consumer propagation + type update in same PR); `devops.mdc` § Post-deploy API Contract Verification (canonical `curl` + `python3` assertion script as mandatory post-deploy step) |

---

## CAT-B1 — Backend Stability / Runtime State Bugs

Symptoms: race conditions on SQLite writes; JWT secret mis-read at service startup; containers alive but functionally broken.

**Prevention rule**: [backend.mdc](../../.cursor/rules/backend.mdc) § Python Standards, § Debugging (logs-first); [devops.mdc](../../.cursor/rules/devops.mdc) § Post-deploy API Contract Verification (must assert data shape, not only `200 OK`)

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| [WEA-138](https://linear.app/weather-app-eli/issue/WEA-138) | 2026-03-24 | Fix SQLite concurrent access (WAL mode + busy timeout) | SQLite does not support true concurrent writes. API gateway + handbrake service writing to the same DB caused `database is locked` errors that crashed jobs silently. No retry logic, no WAL mode, no busy_timeout. Service appeared healthy via `/health` while jobs failed. | `backend.mdc` § Debugging (logs-first — silent failures must add logging before code fixes); `backend.mdc` § API Contract Change Checklist (health endpoints must verify DB connectivity + retries, not just process liveness) |
| [WEA-139](https://linear.app/weather-app-eli/issue/WEA-139) | 2026-03-24 | Fix JWT secret and auth stability | JWT secret hardcoded / empty / inconsistently applied between api-gateway and handbrake service → auth silently failed on protected endpoints. Secret lookup path differed between the two services. | `core.mdc` § Code Quality (environment variables — never hardcode secrets; fail-loud missing-var checks); `backend.mdc` § API Design (consistent env var access via shared helper) |

---

## CAT-D1 — Deploy / Host Topology Confusion

Symptoms: deploy succeeds but serves stale code; nginx proxy returns 404 for `/api/v1/*` while SPA root returns 200; containers run from wrong directory; Dockerfile bloat / unused layers.

**Prevention rule**: [devops.mdc](../../.cursor/rules/devops.mdc) § Clean Deployment, § Post-deploy API Contract Verification, § Disk Space Management, § Deployment Permission Gate

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| [WEA-135](https://linear.app/weather-app-eli/issue/WEA-135) | 2026-03-23 | Rewrite Dockerfile.api — remove bloat | Dockerfile.api carried unused build tooling, dev dependencies, and legacy layers → large image, slow deploys, and hidden risk of stale state at runtime. | `devops.mdc` § Docker Best Practices (multi-stage builds, specific image tags, run as non-root) |
| [WEA-136](https://linear.app/weather-app-eli/issue/WEA-136) | 2026-03-23 | Rewrite Dockerfile.handbrake — remove bloat | Same pattern as WEA-135 for the handbrake container. | `devops.mdc` § Docker Best Practices |
| [WEA-137](https://linear.app/weather-app-eli/issue/WEA-137) | 2026-03-24 | Fix frontend Docker build and nginx proxy | Frontend Docker build incomplete; nginx `proxy_pass` not forwarding `/api/*` to api-gateway. A broken `proxy_pass` returned HTTP 200 for the SPA while all API calls returned 404 — "deploy healthy, app broken". | `devops.mdc` § Post-deploy API Contract Verification (explicit rule: verify through the public/nginx endpoint, not only the internal container port) |
| [WEA-140](https://linear.app/weather-app-eli/issue/WEA-140) | 2026-03-23 | Create single docker-compose.yml and .env.example | Multiple ad-hoc compose files existed; `.env.example` was missing → every new environment reinvented configuration and drifted. | `core.mdc` § File and Folder Organization (no duplicate folders / files; one compose file per environment); `core.mdc` § Code Quality (env vars for all secrets/hosts/ports) |
| [WEA-141](https://linear.app/weather-app-eli/issue/WEA-141) | 2026-03-23 | Configure read/write volume mounts for media and DB | Volume mounts were read-only or pointed at wrong paths → jobs "succeeded" in the container but no output was written to the host. | `devops.mdc` § Clean Deployment (verify container creation time vs. source commit time; verify output paths post-deploy as part of the API contract check) |

---

## CAT-M1 — Magic Patterns Drift

Symptoms: Magic Patterns component re-implemented from scratch instead of imported; immutable marker removed; MP instructions silently dropped from the phase prompt.

**Prevention rule**: [frontend.mdc](../../.cursor/rules/frontend.mdc) § Magic Patterns

| Issue | Date | Title | Root Cause | Prevention Added |
|-------|------|-------|------------|------------------|
| _(none yet in this project — CAT seeded from weather-app retrospective WEA-157)_ | | | | |

---

## Open Items

Bugs that don't yet fit a category. When a pattern emerges (same root cause, 2+ issues), promote it to a new `## CAT-N` section above and add a prevention rule.

### Observation: duplicate issue creation (process, not runtime bug)

During Sprint 01 (Mar 2026) the project had two parallel Epic trees: `WEA-103–WEA-120` (Epic 1) and `WEA-132–WEA-144` (Sprint 01 re-filing). Several bugs were filed twice under different IDs:

| Pair | Topic |
|------|-------|
| WEA-109 / WEA-132 | Delete duplicate and dead files |
| WEA-110 / WEA-134 | Reorganize into rules-compliant folder structure |
| WEA-111 / WEA-135 | Rewrite Dockerfile.api — remove bloat |
| WEA-112 / WEA-136 | Rewrite Dockerfile.handbrake — remove bloat |
| WEA-113 / WEA-137 | Fix frontend Docker build and nginx proxy |
| WEA-114 / WEA-140 | Create single docker-compose.yml and .env.example |
| WEA-115 / WEA-141 | Configure read/write volume mounts |
| WEA-116 / WEA-133 | Align frontend API calls to backend routes |
| WEA-118 / WEA-138 | Fix SQLite concurrent access |
| WEA-119 / WEA-139 | Fix JWT secret and auth stability |
| WEA-120 / WEA-142 | Implement actual job cancellation |

This is a **Linear hygiene issue**, not a runtime bug category. Prevention: before creating a new Epic, search existing Done/Cancelled issues in the project for matching titles and link-reuse rather than re-file. See [core.mdc](../../.cursor/rules/core.mdc) § Linear Project Management.

---

## Trigger phrases for log check

Any of these in a user message should prompt the agent to check this log before acting:

- "same issue", "again", "regression", "still broken", "also broken", "duplicate"
