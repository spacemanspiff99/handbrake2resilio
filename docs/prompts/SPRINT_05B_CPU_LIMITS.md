# SPRINT_05B — Raise HandBrake Service CPU Limits

💣

## Linear Issue
**WEA-265** — Raise handbrake-service CPU limit — 2.0 cpus is insufficient for H.265 transcoding
https://linear.app/weather-app-eli/issue/WEA-265

## Recommended Model
**Composer 2 / Auto** — Single-file change to `docker-compose.yml`. Straightforward, no deep reasoning required.

## Sprint
Sprint 05 — Stability & Observability

## Parallel siblings
- **SPRINT_05A_PROGRESS_MONITORING.md** — different file, runs in parallel
- **SPRINT_05C_MIGRATIONS.md** — different files, runs in parallel

---

## Context

Load rules: `core.mdc`, `devops.mdc`

`deployment/docker-compose.yml` currently limits `handbrake-service` to `cpus: "2.0"` and `memory: 2g`. HandBrakeCLI's x265 encoder is highly parallel and benefits from all available cores. At 2.0 CPUs, a 1080p H.265 encode that should take 3 minutes on a modern 8-core machine takes 12+ minutes.

---

## Tasks

### DevOps Engineer

**Step 1: Update `deployment/docker-compose.yml`**

Change `handbrake-service` resource limits:

```yaml
  handbrake-service:
    ...
    deploy:
      resources:
        limits:
          cpus: "0"        # no limit — HandBrake uses what the host provides
          memory: 4g
```

If you prefer a soft cap instead of removing the limit entirely, use `cpus: "4.0"` — but `"0"` (no limit) is recommended for a home LAN server with dedicated hardware.

Keep other services unchanged:
- `api-gateway`: `cpus: "0.5"`, `memory: 512m`
- `frontend`: `cpus: "0.5"`, `memory: 512m`

**Step 2: Update `.env.example`**

Add a comment near the `MAX_CONCURRENT_JOBS` line:

```ini
# HandBrake transcoding is CPU-intensive. The handbrake-service container
# has no CPU cap by default (see deployment/docker-compose.yml).
# On a shared machine, set MAX_CONCURRENT_JOBS=1 to avoid contention.
MAX_CONCURRENT_JOBS=2
```

### QA Engineer

**Step 3: Verify CPU usage during conversion**

After rebuilding the stack, submit a conversion job and monitor CPU:

```bash
# In one terminal: watch stats
docker stats h2r-handbrake --no-stream

# In another: submit a job (replace token/path as needed)
curl -s -X POST http://localhost:8080/api/jobs/add \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"input_path": "/media/input/test_clip.mp4"}'

# Re-run stats a few seconds after job starts
docker stats h2r-handbrake --no-stream
# CPU% should be >100% (using more than 1 core)
```

---

## Verification

```bash
# Confirm the limit is gone or raised in the running container
docker inspect h2r-handbrake | python3 -c "
import json, sys
d = json.load(sys.stdin)[0]
cpu = d['HostConfig']['NanoCpus']
mem = d['HostConfig']['Memory']
print(f'CPU NanoCpus: {cpu} (0 = no limit)')
print(f'Memory: {mem / 1e9:.1f} GB')
assert mem >= 4e9, f'Memory too low: {mem}'
print('PASS')
"
```

---

## Acceptance Criteria (from WEA-265)

- [ ] `handbrake-service` CPU limit raised to ≥ 4.0 cpus or removed (`cpus: "0"`)
- [ ] `handbrake-service` memory limit raised to ≥ 4g
- [ ] `docker stats h2r-handbrake` during a conversion shows CPU% > 100%
- [ ] 📖 `.env.example` comment added noting CPU-intensive nature of transcoding

## CAT-D1 deployment checklist
- [ ] `docker compose down --remove-orphans` before rebuild
- [ ] Full clean rebuild: `docker compose -f deployment/docker-compose.yml up -d --build`
- [ ] Post-deploy API contract check passes

---

## STOP

After PR is open:
```bash
gh pr list --repo spacemanspiff99/handbrake2resilio --state open --json number,headRefName
```

When all three Sprint 05 PRs are open: start **SPRINT_06_DOC_HYGIENE.md** using **Composer 2 / Auto**.

💥
