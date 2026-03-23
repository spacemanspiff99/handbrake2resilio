# Sprint 1: Get Handbrake2Resilio Bootable & Functional

> Reference: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`

## Goal
Get the app to build, boot, and serve a functional UI connected to working backend services on Docker.

## Issues (10 total, 4 waves)

### Wave 1 — Parallel (no dependencies)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| [WEA-132](https://linear.app/weather-app-eli/issue/WEA-132) | Delete duplicate and dead files | Urgent | Backend Engineer | Composer 2 / fast |
| [WEA-133](https://linear.app/weather-app-eli/issue/WEA-133) | Align frontend API calls to backend routes | High | Frontend Engineer → Backend Engineer → QA | Composer 2 / fast |

### Wave 2 — Sequential (depends on WEA-132)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| [WEA-134](https://linear.app/weather-app-eli/issue/WEA-134) | Reorganize into rules-compliant folder structure | Urgent | Engineering Manager → Backend Engineer | Composer 2 / fast |

### Wave 3 — Parallel (depends on WEA-134)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| [WEA-135](https://linear.app/weather-app-eli/issue/WEA-135) | Rewrite Dockerfile.api — remove bloat | Urgent | Backend Engineer → QA | Composer 2 / fast |
| [WEA-136](https://linear.app/weather-app-eli/issue/WEA-136) | Rewrite Dockerfile.handbrake — remove bloat | Urgent | Backend Engineer → QA | Composer 2 / fast |
| [WEA-137](https://linear.app/weather-app-eli/issue/WEA-137) | Fix frontend Docker build + nginx proxy | Urgent | Frontend Engineer → Backend Engineer | Composer 2 / fast |
| [WEA-138](https://linear.app/weather-app-eli/issue/WEA-138) | Fix SQLite concurrent access (WAL mode + busy timeout) | Medium | Backend Engineer → QA | Composer 2 / fast |
| [WEA-139](https://linear.app/weather-app-eli/issue/WEA-139) | Fix JWT secret and auth stability | Medium | Backend Engineer → QA | Composer 2 / fast |

### Wave 4 — Sequential (depends on Wave 3 Dockerfiles: WEA-135, WEA-136, WEA-137)
| Issue | Title | Priority | Persona | Model |
|-------|-------|----------|---------|-------|
| [WEA-140](https://linear.app/weather-app-eli/issue/WEA-140) | Create single docker-compose.yml + .env.example | Urgent | Engineering Manager → Backend Engineer | Composer 2 / fast |
| [WEA-141](https://linear.app/weather-app-eli/issue/WEA-141) | Configure read/write volume mounts for media and DB | High | Backend Engineer → QA | Composer 2 / fast |

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
- [WEA-142](https://linear.app/weather-app-eli/issue/WEA-142): Implement actual job cancellation (Medium)
- [WEA-143](https://linear.app/weather-app-eli/issue/WEA-143): Create root README.md (Low)
- [WEA-144](https://linear.app/weather-app-eli/issue/WEA-144): Full E2E verification with Playwright (Low)
- [WEA-123](https://linear.app/weather-app-eli/issue/WEA-123): Comprehensive test suite (High)

## STOP
Next: `SPRINT_02_TESTING_AND_POLISH.md`
