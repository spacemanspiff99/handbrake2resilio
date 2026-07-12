💣

# SPRINT_06B — Rules Consolidation, CLAUDE.md, Stale-Doc Cleanup, Vibecoding Mirror Check

## Recommended Model

- **Primary (main session): Claude Fable 5** (`claude-fable-5`). The hard part of this sprint is judgment — deciding which of three contradictory rules files wins on each point without breaking the user's real workflow — not typing volume.
- **Fallback primary: Claude Opus 4.8** (`claude-opus-4-8`) if Fable is unavailable.
- **Subagents: Sonnet 5** (`claude-sonnet-5`) for narrow pass/fail sweeps (grep checks, link checks, "did any app file change" diffs). **Haiku 4.5** for trivial mechanical checks. Never spawn a Fable/Opus subagent for a check Sonnet can grade pass/fail.
- Per rules: **before starting, confirm the running model matches this recommendation** and state it in the first message.

## Context

- Read `.cursor/rules/rules.mdc`, `.cursor/rules/agents.mdc`, and `AGENTS.md` before starting (this prompt references and follows `rules.mdc`).
- Host: dev VM `dev-handbrake2resilio` (192.168.10.39). The full stack is running and healthy from SPRINT_06A. Production (192.168.10.18) is **out of scope** — do not touch it.
- **This VM has no `gh` CLI and no GitHub credentials.** Commit locally; `git push` is expected to fail. If it does, report the exact blocked command (note: commit `38da4b1` from SPRINT_06A is also still unpushed) and continue. Do NOT create or store credentials.
- Docker group membership may not be active in inherited shells — run docker via `sg docker -c '...'` if needed.

### The problem this sprint fixes

The repo's AI-guidance files were copied from other projects and contradict each other:

1. **Prompt location**: `rules.mdc` says `scripts/weather-app/docs/prompts/` (weather-app import); `agents.mdc` and `AGENTS.md` say `docs/prompts/`; the repo **actually uses `documentation/prompts/`** with completed prompts in `documentation/prompts/completed prompts/`.
2. **Prompt naming**: `rules.mdc` demands 4-digit prefixes (`0001…`) AND `PHASE_[N]_`; `agents.mdc`/`AGENTS.md` say `PHASE_[N]_`; the repo actually uses `SPRINT_[NN][letter]_DESCRIPTION.md` (current era) with legacy `PHASE_[NN]_` files completed.
3. **`agents.mdc` defects**: duplicated YAML frontmatter (two `---` blocks stacked); references to files that don't exist here (`core.mdc`, `devops.mdc`, `docs/guides/MULTI_AGENT_RELEASE_PIPELINE.md`, `README.md` "Branch Strategy" section); a large Cursor/Composer model-pricing table and "two usage pools" guidance that doesn't apply to Claude Code sessions.
4. **Imported rules for absent tech** (verified by grep — none exist in this repo outside `.cursor/rules/` and completed prompts): Terraform, Google Cloud/gcloud, Mailgun, Magic Patterns, `rep-engine-service/` folder pattern, Linear as the issue tracker of record.
5. **No CLAUDE.md exists** — Claude Code sessions have no repo-level entry point.
6. **Stale docs**: `documentation/RESUME_ON_NEW_MACHINE.md` (references root `requirements.txt` that doesn't exist, pre-Docker venv flow, stale "current state" from 2026-04-05) and `documentation/NEXT_STEPS.md` (references `deploy_production.sh` and `deployment_readiness_check.py` that don't exist; falsely claims production-ready). `README.md` links to `NEXT_STEPS.md`.
7. **Mirror**: `.github/workflows/mirror-rules.yml` mirrors guidance to the private `spacemanspiff99/vibecoding` repo on push to `main`. It must still cover every consolidated file (it already lists `CLAUDE.md`, `.cursor/rules/**`, `AGENTS.md` in `on.push.paths` — verify this remains true after edits).

## Goal

One coherent, non-contradictory set of AI-guidance files that matches actual repo practice; a new root `CLAUDE.md`; stale docs fixed or removed; mirror coverage verified locally. **Zero changes to application code or the running stack** — all three containers still healthy at the end.

## Tasks

### T1 — Create `CLAUDE.md` (repo root)

New file, concise (aim ≤ ~120 lines), containing:
- Project one-liner + architecture table (3 services/ports, from README).
- Key commands: compose up/down/ps/logs (via `deployment/docker-compose.yml`), Playwright-in-Docker test command, health-check curls.
- Prompt lifecycle (the canonical version, see T2): location `documentation/prompts/`, naming `SPRINT_[NN][letter]_DESCRIPTION.md`, `done__` prefix + move to `documentation/prompts/completed prompts/` on completion, STOP section, commit after completion, push (report exact command if blocked).
- Model guidance for Claude Code: Fable 5 / Opus 4.8 for orchestration and judgment; Sonnet 5 / Haiku 4.5 subagents for narrow pass/fail checks.
- Critical repo facts / traps: `deployment/.env` is git-ignored and read from the compose file's dir; output dir must be writable by container uid 999; `shared/job_queue.py` `_run_conversion()` → `/app/handbrake2resilio.sh` is a dead code path (real worker: `handbrake-service/handbrake_service_simple.py`); no Resilio integration in code (output folder is externally synced); never run docker as sudo (use `sg docker -c '...'` in stale shells); browsers/Playwright run in Docker only, never on the host.
- The 💣 / 💥 output-signature convention.
- Pointer to `.cursor/rules/rules.mdc` + `agents.mdc` as the detailed rule set shared with Cursor.

### T2 — De-conflict and clean `.cursor/rules/rules.mdc`

Canonical decisions (apply consistently here and in T3/T4):
- **Prompt location**: `documentation/prompts/` (completed → `documentation/prompts/completed prompts/`). Remove the `scripts/weather-app/docs/prompts/` line.
- **Prompt naming**: `SPRINT_[NN][letter]_DESCRIPTION.md` for new work (legacy `PHASE_[NN]_` files stay as-is in completed). **Drop** the 4-digit-prefix rule.
- **Remove absent-tech sections**: Terraform Safety Rules; Google Cloud Authentication; Mailgun/GCP mentions in "Official Documentation" examples; `rep-engine-service/...` folder pattern (replace with this repo's actual top-level layout); "rely more on lienar issues" / Linear-issue lines — replace with one line: issue tracking, if used, stays within the handbrake2resilio project only.
- **Keep** (they reflect real practice here): personas guidance, cheap-subagent rule (update model names to current: Sonnet 5 / Haiku 4.5), acceptance-criteria + recommended-model requirements, docker-not-as-sudo, logs-first debugging, clean-rebuild rule, Playwright-in-Docker section, frontend Dockerfile/CSS rules, git security limits, disk-space checks, prompt content requirements, 💣/💥 markers.
- **Push rule**: keep "commit and push after completing a prompt" but add: on machines without GitHub credentials, commit locally and report the exact blocked push command in the final report.
- Update the "Always use .cursor/rules/agent.mdc" line (typo: file is `agents.mdc`).

### T3 — De-conflict and clean `.cursor/rules/agents.mdc`

- Fix the duplicated frontmatter (single YAML block).
- Fix prompt location/naming to the T2 canon.
- Remove references to non-existent files (`core.mdc`, `devops.mdc`, `docs/guides/MULTI_AGENT_RELEASE_PIPELINE.md`) and the Linear/fix-branch release-pipeline item that depends on them.
- Replace the Cursor/Composer model tables ("two usage pools", per-token pricing tables, Composer 2 defaults) with tool-agnostic guidance: expensive model (Fable 5 / Opus 4.8 in Claude Code) for orchestration/judgment; cheap subagents (Sonnet 5 / Haiku 4.5) for narrow verifiable tasks; keep the cost-discipline principle and the micro-task/parallelism sections (they're sound and tool-agnostic).
- Keep: micro-task principle, task sizing, parallelism/dependency ordering, `done__` lifecycle, STOP-section requirement, 💥 completion emoji.

### T4 — Align `AGENTS.md` (Codex)

- Fix `docs/prompts/` → `documentation/prompts/` (both occurrences) and completed-prompts path.
- Align naming to `SPRINT_[NN][letter]_DESCRIPTION.md` (keep the "unless an existing local convention is more specific" escape hatch).
- Leave the Codex model recommendations (GPT-5.5 etc.) — that file is Codex-scoped by design.

### T5 — Fix or delete stale docs

- **Delete** `documentation/NEXT_STEPS.md` (wholly stale, falsely claims production readiness, references scripts that don't exist). Update `README.md` to drop/replace the link (point to `documentation/prompts/` sprint history instead).
- **Rewrite** `documentation/RESUME_ON_NEW_MACHINE.md` as a short, accurate Docker-based resume guide: clone, `cp .env.example .env` (JWT secret + media paths), compose up via `deployment/docker-compose.yml`, read `CLAUDE.md` / `.cursor/rules/`, find current sprint in `documentation/prompts/`. No venv/`requirements.txt` flow, no hardcoded stale commit/status, no stale "active prompts" list.
- Check `documentation/README.md` for the same class of staleness (it mentions Terraform/Google Cloud); fix in place if trivially wrong, otherwise note in report.

### T6 — Verify vibecoding mirror coverage (local only)

- Confirm `.github/workflows/mirror-rules.yml` `on.push.paths` covers: `.cursor/rules/**`, `AGENTS.md`, `CLAUDE.md` (it should already — verify, don't assume), and that the copy steps handle `CLAUDE.md` → `claude-memory/`.
- Validate the workflow YAML parses (e.g. `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/mirror-rules.yml'))"`).
- The on-GitHub run cannot be verified from this VM (push blocked) — list it as a **blocked check** with the exact command that would verify it.

### T7 — Guard rails, commit, close out

- Verify **no application code changed**: `git diff --name-only` (staged+unstaged) must touch only: `CLAUDE.md`, `.cursor/rules/*.mdc`, `AGENTS.md`, `README.md`, `documentation/*.md`, `documentation/prompts/**`. Use a cheap subagent for this check.
- `sg docker -c 'docker compose -f deployment/docker-compose.yml ps'` → all 3 containers still healthy (this sprint must not have touched them).
- Rename this prompt `done__SPRINT_06B_RULES_CONSOLIDATION_VIBECODING.md`, move to `documentation/prompts/completed prompts/`, commit everything with a clear message, attempt `git push origin main` and report the exact command + error if blocked.

## Acceptance Criteria

1. `CLAUDE.md` exists at repo root, ≤ ~120 lines, and states the canonical prompt lifecycle (location `documentation/prompts/`, `SPRINT_[NN][letter]_` naming, `done__` + move on completion).
2. `grep -rn "weather-app" CLAUDE.md AGENTS.md .cursor/rules/` → **no matches**.
3. `grep -rn "docs/prompts" CLAUDE.md AGENTS.md .cursor/rules/` → **no matches** (all say `documentation/prompts`).
4. `grep -n "core.mdc\|devops.mdc\|MULTI_AGENT_RELEASE_PIPELINE" .cursor/rules/agents.mdc` → **no matches**; `agents.mdc` has exactly one frontmatter block (exactly two `---` fence lines at head of file).
5. `grep -in "terraform\|gcloud\|mailgun\|magic patterns\|composer 2\|rep-engine-service" .cursor/rules/rules.mdc .cursor/rules/agents.mdc CLAUDE.md` → **no matches**.
6. No contradictions remain on prompt location or naming across `CLAUDE.md`, `rules.mdc`, `agents.mdc`, `AGENTS.md` (single canon: `documentation/prompts/` + `SPRINT_[NN][letter]_`).
7. `documentation/NEXT_STEPS.md` is deleted; `README.md` no longer links to it; `documentation/RESUME_ON_NEW_MACHINE.md` contains no references to `requirements.txt`, `deploy_production.sh`, or `deployment_readiness_check.py`, and every file path it mentions exists.
8. All relative markdown links/file references in the edited guidance files resolve to existing files (subagent link check).
9. `.github/workflows/mirror-rules.yml` parses as valid YAML and its `on.push.paths` + copy steps cover `.cursor/rules/**`, `AGENTS.md`, and `CLAUDE.md`. On-GitHub run verification explicitly listed as blocked.
10. `git diff` for the sprint touches **only** guidance/docs/prompt files (list in criterion T7) — zero app-code changes.
11. `sg docker -c 'docker compose -f deployment/docker-compose.yml ps'` shows `api-gateway`, `handbrake-service`, `frontend` all healthy at sprint end.
12. Prompt renamed with `done__` prefix, moved to `documentation/prompts/completed prompts/`, work committed; push attempted and, if blocked, the exact command and error reported.

## Verification (run all, paste output in final report)

```bash
test -f CLAUDE.md && wc -l CLAUDE.md
grep -rn "weather-app" CLAUDE.md AGENTS.md .cursor/rules/ ; echo "exit=$?"   # expect exit=1
grep -rn "docs/prompts" CLAUDE.md AGENTS.md .cursor/rules/ ; echo "exit=$?"  # expect exit=1
grep -n "core.mdc\|devops.mdc\|MULTI_AGENT_RELEASE_PIPELINE" .cursor/rules/agents.mdc ; echo "exit=$?"  # expect exit=1
grep -in "terraform\|gcloud\|mailgun\|magic patterns\|composer 2\|rep-engine-service" .cursor/rules/rules.mdc .cursor/rules/agents.mdc CLAUDE.md ; echo "exit=$?"  # expect exit=1
ls documentation/NEXT_STEPS.md 2>&1        # expect: No such file
grep -n "NEXT_STEPS" README.md ; echo "exit=$?"  # expect exit=1
grep -n "requirements.txt\|deploy_production.sh\|deployment_readiness_check" documentation/RESUME_ON_NEW_MACHINE.md ; echo "exit=$?"  # expect exit=1
python3 -c "import yaml; d=yaml.safe_load(open('.github/workflows/mirror-rules.yml')); p=d[True]['push']['paths'] if True in d else d['on']['push']['paths']; print(p); assert 'CLAUDE.md' in p and '.cursor/rules/**' in p and 'AGENTS.md' in p"
git status --short
sg docker -c 'docker compose -f deployment/docker-compose.yml ps'
```

## Working Rules for This Sprint

- Rules/docs only — **no changes** under `api-gateway/`, `handbrake-service/`, `ui-frontend/`, `shared/`, `deployment/`, `testing/`, `data/`.
- `deployment/.cursor-rules` is production-deploy guidance outside this sprint's scope — leave it; note any observed staleness in the report.
- Do not touch production (192.168.10.18). Do not begin any sprint beyond 06B.
- Evidence first: every acceptance criterion is graded by command output, not by assertion.

## Final Report Must Include

Changed files, verification command outputs, blocked checks with exact blocking commands (expected: `git push origin main`, and on-GitHub mirror-run verification), and the STOP handoff.

## STOP

Next prompt: `SPRINT_06C_PUSH_AND_PROD_DEPLOY.md` (restore GitHub push access from a credentialed machine, push `main` — which triggers the vibecoding mirror; verify the mirror run on GitHub — then deploy the verified stack to production 192.168.10.18 per `deployment/` scripts). Do not begin it in this session.

💥
