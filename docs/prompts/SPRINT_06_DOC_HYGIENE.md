# SPRINT_06 — Documentation Hygiene & Clean Deploy

💣

## Linear Issue
**WEA-267** — Clean up stale documentation — NEXT_STEPS, MICROSERVICES_ARCHITECTURE, DEPLOYMENT_README drift
https://linear.app/weather-app-eli/issue/WEA-267

## Recommended Model
**Composer 2 / Auto** — Documentation edits only. No code changes, no browser tools.

## Sprint
Sprint 06 — Doc Hygiene & Deploy

## Dependencies
All Sprint 05 PRs must be merged before starting this prompt.

---

## Context

Load rules: `core.mdc`

Several documentation files are stale and will mislead future agents. Specific problems are catalogued below.

---

## Tasks

### Project Manager / Technical Writer

**Step 1: Update `docs/NEXT_STEPS.md`**

Replace the entire file. It currently describes a pre-Sprint-01 state ("5/6 checks passed") and references scripts that do not exist. Write a new version that:

- Describes the current state as of Sprint 04 completion (conversion pipeline working)
- Replaces all references to `deploy_production.sh` → `deploy001.sh` and `deployment_readiness_check.py` → `docker compose ps` + contract check
- Lists what has been done (Sprints 01–05) and what is next (Sprint 06 deploy, future features)
- Does not claim "production ready" — this is a home LAN app

**Step 2: Rewrite `docs/MICROSERVICES_ARCHITECTURE.md`**

The file describes Redis which was never part of this project. Rewrite it to accurately describe the actual stack:

```
┌─────────────────────────────────────────────────────────┐
│  Host Browser                                           │
│  http://HOST_IP:7474                                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
               ┌───────▼────────┐
               │   frontend     │  nginx :80 (host :7474)
               │   (React SPA)  │  /api/* → api-gateway:8080
               └───────┬────────┘
                       │ HTTP proxy_pass
               ┌───────▼────────┐
               │  api-gateway   │  Flask :8080
               │  Auth, Jobs,   │  SQLite /data/handbrake.db
               │  FileBrowser,  │  (shared volume h2r-app-data)
               │  Tabs, WS      │
               └───────┬────────┘
                       │ HTTP /convert
               ┌───────▼────────┐
               │  handbrake-svc │  Flask :8081
               │  HandBrakeCLI  │  SQLite /data/handbrake.db
               │  subprocess    │  (same shared volume)
               └───────┬────────┘
                       │ reads/writes
               ┌───────▼────────┐
               │  Host volumes  │
               │  /media/input  │  (ro)
               │  /media/output │  (rw) → Resilio Sync
               └────────────────┘
```

Remove all Redis references. Confirm frontend port is `:7474` (not `:3000`).

**Step 3: Fix `deployment/DEPLOYMENT_README.md`**

Replace all references to non-existent scripts:
- `deploy_clean.sh` → `deploy001.sh` or the docker compose commands directly
- `verify_clean_deployment.sh` → post-deploy contract check from `devops.mdc`

The README should show the canonical deploy sequence:
```bash
# 1. Stop existing stack
docker compose -f deployment/docker-compose.yml down --remove-orphans

# 2. Clean build cache
docker builder prune -af

# 3. Rebuild and start
docker compose -f deployment/docker-compose.yml up -d --build

# 4. Verify
docker compose -f deployment/docker-compose.yml ps
curl -sf http://localhost:8080/health
```

**Step 4: Handle `docs/README.md`**

Read the file. If it describes a devcontainer for a different project (e.g. "alt-cliff-mass", Terraform, etc.), delete it:

```bash
git rm docs/README.md
```

Then check root `README.md` to ensure it does not reference `docs/README.md`. If it does, remove that reference.

**Step 5: Verify root `README.md` integrity**

1. Read root `README.md`
2. Confirm the quick-start command still works: `docker compose -f deployment/docker-compose.yml up --build`
3. Confirm all docs paths referenced in root `README.md` exist on disk
4. Run: `rg 'deploy_production\.sh|deployment_readiness_check\.py|deploy_clean\.sh|verify_clean_deployment\.sh' docs/`
   - Must return zero results

---

## Verification

```bash
# No stale script references in any doc file
rg 'deploy_production\.sh|deployment_readiness_check\.py|deploy_clean\.sh|verify_clean_deployment\.sh' docs/ deployment/
# Must return: (no output)

# No Redis references in architecture doc
grep -i redis docs/MICROSERVICES_ARCHITECTURE.md
# Must return: (no output)

# Frontend port correct
grep '3000' docs/MICROSERVICES_ARCHITECTURE.md
# Must return: (no output) — 3000 was replaced by 7474
```

---

## Acceptance Criteria (from WEA-267)

- [ ] `docs/NEXT_STEPS.md` contains no references to `deploy_production.sh` or `deployment_readiness_check.py`
- [ ] `docs/MICROSERVICES_ARCHITECTURE.md` shows SQLite (not Redis) and frontend port `:7474`
- [ ] `deployment/DEPLOYMENT_README.md` references only scripts that exist on disk
- [ ] `docs/README.md` either accurately describes the project or is deleted
- [ ] Root `README.md` quick-start section is accurate
- [ ] `rg` for stale script names returns zero results
- [ ] 📖 All changed docs cross-referenced from root `README.md` or a rule file

---

## STOP

After PR is merged:

1. Mark **WEA-267** Done in Linear
2. Rename `docs/prompts/SPRINT_06_DOC_HYGIENE.md` → `done__SPRINT_06_DOC_HYGIENE.md` → move to `docs/prompts/completed prompts/`
3. Do the same for any Sprint 04/05 prompts whose PRs are merged
4. Review if a production deploy to `192.168.10.18` is desired — if so, present a deploy plan to the user and wait for approval before running anything (per `devops.mdc` § Deployment Permission Gate)

💥
