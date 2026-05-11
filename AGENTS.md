# Codex Project Instructions

These instructions apply to the whole repository. They are for OpenAI Codex only. Keep Cursor guidance in `.cursor/rules/`; put Codex command approval policy only in `.codex/rules/*.rules`.

## Project Shape

- This project automates HandBrake-to-Resilio workflows. Keep changes scoped to that domain.
- Do not import weather-app, issue-tracker, or other project-specific tracker paths, host tables, branch flows, category taxonomies, or deployment assumptions.
- Use the repository's normal branch and PR flow. Confirm the current branch before staging or committing.

## Prompt And Issue Workflow

- Execution prompts live in `docs/prompts/`.
- New phase prompts follow `PHASE_[N]_[DESCRIPTION].md` unless an existing local convention is more specific.
- Completed prompts are renamed with a `done__` prefix and moved to `docs/prompts/completed prompts/` after all tasks are implemented and verified.
- Every prompt needs context, target files, acceptance criteria, verification steps, and a STOP section naming the next prompt or `none`.
- Keep tasks small enough to verify independently. Do not mix prompt/rules updates with unrelated feature work.

## Engineering Rules

- Prefer existing scripts, compose files, and project conventions.
- Debug from evidence first: inspect logs and runtime output before changing logic. Add logging when the missing evidence is the root blocker.
- Verify API contracts or CLI behavior with real inputs when the change touches request/response formats, file movement, HandBrake flags, or Resilio handoff.
- Never hardcode secrets, host names, or environment-specific values.

## Verification

- Run the smallest relevant check for the files changed.
- For container or deployment work, verify container creation date versus code change date and confirm the running artifact is fresh.
- For frontend or UI-facing changes, verify styling/rendering with a browser or Playwright screenshot when applicable; "no JS errors" is not enough.
- If a relevant check cannot run, report the exact command and blocker.

## Model And Evidence

- Prefer GPT-5.5 for Codex work when available; use GPT-5.4 as fallback and GPT-5.4-mini for narrow subagent work.
- Follow any model recommendation in the active prompt or issue when the environment supports it.
- Final reports should include changed files, verification commands, blocked checks, and the next STOP handoff.
