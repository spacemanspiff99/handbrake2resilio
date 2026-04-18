# SPRINT_05C — Create 001_initial_schema.sql Migration

💣

## Linear Issue
**WEA-266** — Create 001_initial_schema.sql — consolidate inline CREATE TABLE statements
https://linear.app/weather-app-eli/issue/WEA-266

## Recommended Model
**Composer 2 / Auto** — SQL extraction and file creation. No architectural decisions, no browser tools.

## Sprint
Sprint 05 — Stability & Observability

## Parallel siblings
- **SPRINT_05A_PROGRESS_MONITORING.md** — different files, runs in parallel
- **SPRINT_05B_CPU_LIMITS.md** — different files, runs in parallel

---

## Context

Load rules: `core.mdc`, `backend.mdc`

The database schema is defined inline in two Python files:
- `handbrake-service/handbrake_service_simple.py` → `init_job_database()`
- `api-gateway/api_gateway_simple.py` → table creation at startup

`migrations/README.md` explicitly flags this as acknowledged debt. This prompt extracts the DDL into a proper migration file and wires it through a shared runner.

**Do not change any column names or types.** This is extraction only.

---

## Tasks

### Backend Engineer

**Step 1: Read both inline CREATE TABLE statements**

Read the following files in full before writing anything:
- `handbrake-service/handbrake_service_simple.py` (search for `CREATE TABLE`)
- `api-gateway/api_gateway_simple.py` (search for `CREATE TABLE`)

**Step 2: Create `migrations/001_initial_schema.sql`**

Write a single SQL file containing all `CREATE TABLE IF NOT EXISTS` statements from both files, verbatim (same columns, same types, same constraints). Use `CREATE TABLE IF NOT EXISTS` for idempotency.

Format:
```sql
-- 001_initial_schema.sql
-- Initial schema extracted from Python startup DDL.
-- Idempotent: safe to run on empty or existing databases.

CREATE TABLE IF NOT EXISTS jobs (
    -- columns verbatim from handbrake_service_simple.py
    ...
);

CREATE TABLE IF NOT EXISTS users (
    -- columns verbatim from api_gateway_simple.py
    ...
);

-- ... other tables
```

**Step 3: Add `run_migrations(db_path)` to `shared/db.py`**

```python
import os
import glob

def run_migrations(db_path: str) -> None:
    """
    Execute all .sql files in the migrations/ folder in lexicographic order.

    Idempotent: safe to call on startup whether the DB is empty or pre-existing.
    All statements use CREATE TABLE IF NOT EXISTS.
    """
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "migrations",
    )
    sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))

    with get_db_connection(db_path) as conn:
        for sql_file in sql_files:
            logger.info("running_migration", file=os.path.basename(sql_file))
            with open(sql_file) as f:
                conn.executescript(f.read())
        conn.commit()
```

**Step 4: Replace inline DDL in both Python files**

In `handbrake-service/handbrake_service_simple.py`:
- Remove `init_job_database()` function body (keep the function call location)
- Replace with:
  ```python
  from shared.db import run_migrations

  def init_job_database() -> None:
      """Initialize database schema via versioned SQL migrations."""
      db_path = os.getenv("DATABASE_PATH", "/data/handbrake.db")
      run_migrations(db_path)
      logger.info("Job database initialized via migrations")
  ```

In `api-gateway/api_gateway_simple.py`:
- Do the same for whichever startup function contains the inline DDL.

**Step 5: Update `migrations/README.md`**

Remove the "acknowledged debt" paragraph. Add:
```markdown
## Current migrations

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Full initial schema extracted from Python startup DDL (Sprint 05) |

To add a new migration: create `002_<description>.sql` and run the stack.
`run_migrations()` in `shared/db.py` applies all `.sql` files in order at startup.
```

### QA Engineer

**Step 6: Add unit test for idempotency**

In `shared/unit-tests/test_db.py`, add:

```python
import tempfile, os
from shared.db import run_migrations

def test_run_migrations_idempotent():
    """run_migrations must be safe to call twice on the same database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        run_migrations(db_path)   # first run — creates tables
        run_migrations(db_path)   # second run — must not error (IF NOT EXISTS)
    finally:
        os.unlink(db_path)

def test_run_migrations_on_empty_db():
    """run_migrations must succeed on a brand-new empty database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        run_migrations(db_path)
        # Check that expected tables exist
        from shared.db import get_db_connection
        with get_db_connection(db_path) as conn:
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        assert "jobs" in tables, f"jobs table missing, got: {tables}"
    finally:
        os.unlink(db_path)
```

---

## Verification

```bash
# Unit tests
cd /home/akun/handbrake2resilio
python3 -m pytest shared/unit-tests/test_db.py -v

# Full stack smoke test
docker compose -f deployment/docker-compose.yml down --remove-orphans
docker compose -f deployment/docker-compose.yml up -d --build
docker compose -f deployment/docker-compose.yml ps
# All 3 containers must reach "healthy"
```

---

## Acceptance Criteria (from WEA-266)

- [ ] `migrations/001_initial_schema.sql` exists with all `CREATE TABLE IF NOT EXISTS` statements
- [ ] Inline `CREATE TABLE` DDL removed from both Python startup functions
- [ ] `run_migrations()` in `shared/db.py` with type hints and docstring
- [ ] Unit tests: idempotent call passes, empty DB creation passes
- [ ] Fresh `docker compose up --build` starts all 3 containers healthy
- [ ] 📖 `migrations/README.md` updated — "acknowledged debt" removed

## Database Migration checklist (backend.mdc § Database Migrations)
- [ ] SQL file is in `migrations/` only
- [ ] File name is zero-padded: `001_initial_schema.sql`
- [ ] Migration tested on fresh (empty) DB and existing DB with data
- [ ] No migration applied to shared environment without backup

---

## STOP

After PR is open:
```bash
gh pr list --repo spacemanspiff99/handbrake2resilio --state open --json number,headRefName
```

When all three Sprint 05 PRs are open (05A, 05B, 05C): start **SPRINT_06_DOC_HYGIENE.md** in a fresh chat using **Composer 2 / Auto**.

💥
