# SPRINT_04B — Fix HandBrake Progress Monitoring

💣

## Linear Issue
**WEA-263** — Fix HandBrake progress monitoring — reads wrong pipe, parses wrong format
https://linear.app/weather-app-eli/issue/WEA-263

## Recommended Model
**Composer 2 / Auto** — Single-file Python fix around subprocess I/O. No browser tools needed, no architectural decisions.

> Do NOT use Sonnet or Opus for this prompt.

## Sprint
Sprint 04 — Real Video Test (Sprint 05 milestone, but runs in parallel with 04A)

## Parallel sibling
**SPRINT_04A_FIX_HANDBRAKE_CLI_FLAGS.md** runs in parallel. Both touch `handbrake_service_simple.py`. Review diffs before merging to avoid conflicts — they touch different functions/lines.

---

## Context

Load rules: `core.mdc`, `backend.mdc`

`run_handbrake_conversion` in `handbrake-service/handbrake_service_simple.py` has two bugs that cause progress to always show 0%:

**Bug 1 — reads stdout, HandBrake writes to stderr**
The monitoring loop calls `process.stdout.readline()` (line ~364). HandBrakeCLI writes all progress output to **stderr**. Stdout is empty during encoding. Nothing is ever read.

**Bug 2 — --json does not stream; it emits one blob at end**
The code tries to parse per-line JSON as if HandBrake streams progress updates. It does not. `--json` emits one JSON object only when the encode finishes. Progress must be read from stderr text lines.

**HandBrake stderr progress format:**
```
Encoding: task 1 of 1, 47.38 % (89.32 fps, avg 92.14 fps, ETA 00h02m15s)
```

Regex to extract: `r'(\d+\.\d+) %'`

---

## Tasks

### Backend Engineer

**Step 1: Fix the monitoring loop**

In `run_handbrake_conversion`, change the subprocess call and monitoring loop:

```python
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,   # keep but don't iterate during run
    stderr=subprocess.PIPE,
    universal_newlines=True,
)

import re
_PROGRESS_RE = re.compile(r'(\d+\.\d+) %')
_progress_warned = False

for line in process.stderr:
    line = line.rstrip()
    logger.debug("handbrake_stderr", line=line)
    m = _PROGRESS_RE.search(line)
    if m:
        job.progress = float(m.group(1))
        save_job_to_db(job)
    elif not _progress_warned and line:
        # log once if we're getting output but no progress match
        # (e.g. different HandBrake version format)
        logger.warning("handbrake_progress_no_match", line=line[:200])
        _progress_warned = True

process.wait()
return_code = process.returncode
```

Notes:
- `for line in process.stderr` is a blocking readline loop — this is correct and replaces the manual `while True` loop
- `process.stdout` is still `PIPE` but intentionally not read during the run; it can be `.read()` after `process.wait()` if needed for final JSON summary
- `_progress_warned` resets to `False` per job invocation (not a module-level variable — declare it inside the function)
- The `--json` flag removal is handled by SPRINT_04A; if that PR lands first, `--json` will already be gone from the command. If this PR lands first, the `--json` flag will still be present but harmless — it just means stdout has an unread JSON blob after the run.

**Step 2: Add type hints and docstring**

Ensure `run_handbrake_conversion` has:
```python
def run_handbrake_conversion(job: ConversionJob) -> None:
    """
    Run HandBrakeCLI for the given job in the current thread.

    Reads progress from stderr text lines and updates job.progress
    incrementally. Caller is responsible for running this in a thread.
    """
```

### QA Engineer

**Step 3: Write unit tests**

Create `handbrake-service/unit-tests/test_progress_parsing.py`:

```python
import re

PROGRESS_RE = re.compile(r'(\d+\.\d+) %')

def test_extracts_progress_from_encoding_line():
    line = "Encoding: task 1 of 1, 47.38 % (89.32 fps, avg 92.14 fps, ETA 00h02m15s)"
    m = PROGRESS_RE.search(line)
    assert m is not None
    assert float(m.group(1)) == 47.38

def test_extracts_100_percent():
    line = "Encoding: task 1 of 1, 100.00 % (102.11 fps, avg 94.22 fps, ETA 00h00m00s)"
    m = PROGRESS_RE.search(line)
    assert m is not None
    assert float(m.group(1)) == 100.0

def test_no_match_on_non_progress_line():
    line = "Opening /media/input/test.mp4..."
    assert PROGRESS_RE.search(line) is None

def test_no_match_on_empty_line():
    assert PROGRESS_RE.search("") is None
```

---

## Verification

```bash
cd /home/akun/handbrake2resilio
python3 -m pytest handbrake-service/unit-tests/test_progress_parsing.py -v
```

All 4 tests must pass.

---

## Acceptance Criteria (from WEA-263)

- [ ] Progress monitoring loop reads from `process.stderr` (not stdout)
- [ ] `PROGRESS_RE = re.compile(r'(\d+\.\d+) %')` regex applied to each stderr line
- [ ] `job.progress` updated and saved to DB on each matching line
- [ ] All stderr lines logged at DEBUG level
- [ ] If no progress line ever matches, a WARNING is logged once (not on every non-matching line)
- [ ] Unit tests in `test_progress_parsing.py` pass (4 tests)
- [ ] Type hints and docstring on `run_handbrake_conversion`
- [ ] 📖 No documentation changes required

## CAT-B1 checklist
- [ ] All HandBrake stderr output logged at DEBUG level
- [ ] WARNING logged once if regex never matches during a run
- [ ] No change to `/health` endpoint

---

## STOP

After all tests pass and PR is open:

1. Run `git branch --show-current` — confirm branch is `spcmanspiff/wea-263-*`
2. Open PR against `master`
3. Check if sibling **SPRINT_04A_FIX_HANDBRAKE_CLI_FLAGS.md** has a PR open:
   ```bash
   gh pr list --repo spacemanspiff99/handbrake2resilio --state open --json number,headRefName
   ```
4. If sibling PR is open: both are done — start **SPRINT_04C_E2E_VERIFICATION.md** in a fresh chat using **Claude 4.6 Sonnet**.
5. If sibling has no PR: output "⏸ HOLDING — WEA-263 PR open. Waiting for WEA-262 (CLI flags fix) PR before starting E2E."

💥
