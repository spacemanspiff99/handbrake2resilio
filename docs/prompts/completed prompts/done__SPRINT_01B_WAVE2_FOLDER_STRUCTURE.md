# done__SPRINT_01B — Wave 2: Rules-Compliant Folder Structure (WEA-134)

> Reference: `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`
> Linear issue: WEA-134
> Model: Composer 2 / Auto (fast)
> Personas: Engineering Manager → Backend Engineer

💣

## Context

Wave 1 (WEA-132, WEA-133) removed dead files and verified API alignment. Wave 2 reorganizes the `testing/` folder into rules-compliant service subfolders per the `[service-name]/[function-name]/` pattern in `rules.mdc`.

## Tasks Completed

### Engineering Manager — Audit & Plan
- Identified `testing/` as a flat folder violating `rules.mdc` pattern
- Mapped each test file to its owning service:
  - `test_auth.py` → `api-gateway/` (tests `auth.py`)
  - `test_config.py` → `shared/` (tests `shared/config.py`)
  - `test_job_queue.py` → `shared/` (tests `shared/job_queue.py`)
  - `test_config_simple.py` → DELETE (stub, no real assertions, duplicate of test_config.py)

### Backend Engineer — Execute
1. Created `api-gateway/unit-tests/` and `shared/unit-tests/` subfolders
2. `git mv testing/test_auth.py api-gateway/unit-tests/test_auth.py`
3. `git mv testing/test_config.py shared/unit-tests/test_config.py`
4. `git mv testing/test_job_queue.py shared/unit-tests/test_job_queue.py`
5. `git rm testing/test_config_simple.py` (stub deleted)
6. Removed empty `testing/` folder
7. Fixed `sys.path` in all 3 moved tests: added one extra `os.path.dirname()` level to correctly resolve repo root from new depth
8. Added `__init__.py` to both `unit-tests/` folders for Python discovery

## Final Structure

```
api-gateway/
├── api_gateway_simple.py
├── auth.py
└── unit-tests/
    ├── __init__.py
    └── test_auth.py

shared/
├── __init__.py
├── config.py
├── db.py
├── job_queue.py
└── unit-tests/
    ├── __init__.py
    ├── test_config.py
    └── test_job_queue.py
```

## Acceptance Criteria — WEA-134 ✅

- [x] `testing/` folder is gone
- [x] Tests live under their owning service in `unit-tests/` subfolder
- [x] `sys.path` in all tests resolves to repo root correctly
- [x] `auth.py` is importable from `test_auth.py` new location
- [x] `shared.config` and `shared.job_queue` importable from new locations
- [x] No Dockerfiles or docker-compose paths needed updating (no test paths referenced there)
- [x] Committed and pushed: `1f68008`

## Git

```
git commit: WEA-134: Reorganize into rules-compliant folder structure
git push origin HEAD → main (1f68008)
```

## STOP

Next prompt: `SPRINT_01C_WAVE3_DOCKERFILES.md` (WEA-135, WEA-136, WEA-137 — parallel)
