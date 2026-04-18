# Database Migrations

This is the **single, central** migrations folder for the project. Per [core.mdc](../.cursor/rules/core.mdc) § File and Folder Organization and [backend.mdc](../.cursor/rules/backend.mdc) § Database Migrations:

- **Store `.sql` files ONLY here** — never create other migration folders.
- **Use versioned, zero-padded file names** (e.g. `001_initial_schema.sql`, `002_add_priority_column.sql`).
- **Test migrations on development data first.** Never apply a migration to a shared/production DB without (1) a verified backup and (2) explicit user approval.
- **No seeding scripts** here — seed data belongs in `shared/` or `scripts/` and is for local development only. Production data changes must go through a numbered migration.

## Current state (as of 2026-04-17)

The legacy services (`api-gateway/`, `handbrake-service/`, `shared/job_queue.py`, `api-gateway/auth.py`) currently create their schemas inline with `CREATE TABLE IF NOT EXISTS` statements embedded in Python code. This is a known tech-debt item.

**Before the next schema change**, consolidate the existing inline `CREATE TABLE` statements into `001_initial_schema.sql` so:
1. There is one canonical source of truth for the schema.
2. New environments bootstrap from a single SQL file.
3. Future changes follow `002_*.sql`, `003_*.sql`, etc. with explicit migration semantics.

## File naming

```
NNN_short_snake_case_description.sql
```

- `NNN` — zero-padded 3-digit sequence starting at `001`.
- Description — lowercase, snake_case, concise (≤ 6 words).

Examples:

```
001_initial_schema.sql
002_add_jobs_priority_column.sql
003_index_jobs_status_created_at.sql
```

## Down migrations

If a migration is non-trivial to reverse, add a sibling file `NNN_short_description.down.sql` with the rollback SQL. Not required for pure `CREATE TABLE` / `CREATE INDEX` statements.

## Checklist before committing a migration

- [ ] File name matches `NNN_snake_case.sql` convention
- [ ] Includes a one-line comment at the top stating purpose and linked issue
- [ ] Tested on a local DB created from the previous schema state
- [ ] If destructive or table-altering: `down.sql` companion file exists
- [ ] Schema change propagated to API serializers (see [backend.mdc](../.cursor/rules/backend.mdc) § API Contract Change Checklist)
- [ ] Schema change propagated to frontend types (`ui-frontend/src/types/`)
- [ ] Documented in the PR description with a `MIGRATION:` prefix in the commit message
