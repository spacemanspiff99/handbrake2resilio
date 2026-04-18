# SPRINT_05A — Fix Progress Monitoring (if not already merged in Sprint 04)

💣

## Linear Issue
**WEA-263** — Fix HandBrake progress monitoring — reads wrong pipe, parses wrong format
https://linear.app/weather-app-eli/issue/WEA-263

## Recommended Model
**Composer 2 / Auto** — Single-file Python fix. No architectural decisions.

## Note
This prompt is only needed if WEA-263 was NOT completed in Sprint 04 (it ran in parallel with WEA-262 as SPRINT_04B). Check first:

```bash
gh pr list --repo spacemanspiff99/handbrake2resilio --state merged --json title,headRefName | python3 -c "
import json, sys
prs = json.load(sys.stdin)
print([p['title'] for p in prs if 'WEA-263' in p['title'] or 'progress' in p['title'].lower()])
"
```

If WEA-263 is already merged: **skip this prompt, mark it cancelled, proceed to SPRINT_05B and 05C**.

Otherwise: see **SPRINT_04B_FIX_PROGRESS_MONITORING.md** for the full implementation — the content is identical, just running in Sprint 05 timing.

## Parallel siblings in Sprint 05
- **SPRINT_05B_CPU_LIMITS.md** — runs in parallel (different file: `docker-compose.yml`)
- **SPRINT_05C_MIGRATIONS.md** — runs in parallel (different files: `shared/db.py`, `migrations/`)

---

## STOP

After PR is open, check siblings:
```bash
gh pr list --repo spacemanspiff99/handbrake2resilio --state open --json number,headRefName
```

When all three Sprint 05 PRs are open (or merged): start **SPRINT_06_DOC_HYGIENE.md** in a fresh chat using **Composer 2 / Auto**.

💥
