# Sprint 1: Get Handbrake2Resilio Bootable & Functional

> Reference: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`

## Goal
Get the app to build, boot, and serve a functional UI connected to working backend services on Docker.

## Issues (10 total, 4 waves)

### Wave 1 — Parallel (no dependencies)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| WEA-109 | Delete duplicate and dead files | Urgent | Backend Engineer | Composer 2 / fast |
| WEA-116 | Align frontend API calls to backend | High | Frontend Engineer → Backend Engineer → QA | Composer 2 / fast |

### Wave 2 — Sequential (depends on WEA-109)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| WEA-110 | Reorganize into rules-compliant folder structure | Urgent | Engineering Manager → Backend Engineer | Composer 2 / fast |

### Wave 3 — Parallel (depends on WEA-110)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| WEA-111 | Rewrite Dockerfile.api — remove bloat | Urgent | Backend Engineer → QA | Composer 2 / fast |
| WEA-112 | Rewrite Dockerfile.handbrake — remove bloat | Urgent | Backend Engineer → QA | Composer 2 / fast |
| WEA-113 | Fix frontend Docker build + nginx proxy | Urgent | Frontend Engineer → Backend Engineer | Composer 2 / fast |
| WEA-118 | Fix SQLite concurrent access | Medium | Backend Engineer → QA | Composer 2 / fast |
| WEA-119 | Fix JWT secret and auth stability | Medium | Backend Engineer → QA | Composer 2 / fast |

### Wave 4 — Sequential (depends on Wave 3 Dockerfiles)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| WEA-114 | Create single docker-compose.yml + .env.example | Urgent | Engineering Manager → Backend Engineer | Composer 2 / fast |
| WEA-115 | Configure read/write volume mounts | High | Backend Engineer → QA | Composer 2 / fast |

### Wave 5 — Verification
- Docker build all services
- Boot stack
- Smoke test: login, dashboard, file browser, queue

## Acceptance Criteria
- [ ] `docker compose up --build` succeeds with no errors
- [ ] All 3 containers healthy (`docker compose ps`)
- [ ] Frontend loads at http://localhost:3000
- [ ] Login works (admin/admin123)
- [ ] Dashboard shows system health
- [ ] File browser navigates directories
- [ ] Job queue page loads
- [ ] No 404 errors in browser Network tab

## Deferred to Sprint 2
- WEA-120: Implement actual job cancellation (Medium)
- WEA-121: Create root README.md (Low)
- WEA-122: Full E2E verification (Low)
- WEA-124-127: Comprehensive test suite (High)

## STOP
Next: `SPRINT_02_TESTING_AND_POLISH.md`
