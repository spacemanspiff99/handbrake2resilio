# SPRINT_04A — Fix HandBrake CLI Flags

💣

## Linear Issue
**WEA-262** — Fix HandBrake CLI command flags — invalid -r and -b arguments cause 100% job failure rate
https://linear.app/weather-app-eli/issue/WEA-262

## Recommended Model
**Composer 2 / Auto** — Single-file Python fix. No architectural decisions. Does not require deep reasoning or browser tools.

> Do NOT use Sonnet or Opus for this prompt. This is a straightforward code fix.

## Sprint
Sprint 04 — Real Video Test

## Parallel sibling
**SPRINT_04B_FIX_PROGRESS_MONITORING.md** runs in parallel — different function in the same file. Review the diff before merging to ensure no line conflicts in `handbrake_service_simple.py`.

---

## Context

Load rules: `core.mdc`, `backend.mdc`

`handbrake-service/handbrake_service_simple.py` contains a function `run_handbrake_conversion` that builds and runs the `HandBrakeCLI` subprocess. The command has two fatal bugs that cause 100% of conversion jobs to fail:

1. `-r 720x480` — `-r` is the **frame rate** flag, not resolution. HandBrake rejects a non-numeric framerate value immediately.
2. `-b <video_bitrate>` combined with `-q <quality>` — these are mutually exclusive encoding modes. HandBrake exits with an error when both are present.

Reference: https://handbrake.fr/docs/en/1.7.0/cli/cli-guide.html (consult before writing any flag)

---

## Tasks

### Backend Engineer

**Step 1: Extract `build_handbrake_cmd` into a testable function**

Extract the command-building logic from `run_handbrake_conversion` into a pure function:

```python
def build_handbrake_cmd(job: ConversionJob) -> list[str]:
    """Build the HandBrakeCLI command list for a conversion job."""
```

This enables unit testing without subprocess calls.

**Step 2: Fix the command flags**

The corrected command must:
- Use `-q <quality>` for CRF quality (keep this, it is correct)
- **Remove** `-b <video_bitrate>` entirely (mutually exclusive with `-q`)
- **Remove** `-r <resolution>` entirely
- If `job.resolution` is set and non-empty, parse it as `"WxH"` and add `--width W --height H`
- Add `--encoder x265` explicitly
- **Remove** `--json` flag (HandBrake `--json` does not stream progress; it emits one blob at end — only useful if you process the final summary, which we do not)
- Log the full command list at DEBUG level before `subprocess.Popen`

Example corrected command for a 1920x1080 job at quality 23:
```
HandBrakeCLI -i /media/input/file.mp4 -o /media/output/file.mkv -q 23 --encoder x265 --width 1920 --height 1080
```

If `job.resolution` is empty or None, omit `--width`/`--height` (HandBrake preserves source dimensions by default).

**Step 3: Capture stderr on failure**

After `process.wait()`, if `return_code != 0`, read all remaining stderr and store it in `job.error_message`:

```python
stderr_output = process.stderr.read()
job.error_message = f"HandBrake failed (exit {return_code}): {stderr_output[:2000]}"
```

### QA Engineer

**Step 4: Write unit tests**

Create `handbrake-service/unit-tests/test_build_command.py`:

```python
from handbrake_service_simple import build_handbrake_cmd
from shared.job_queue import ConversionJob, JobStatus
import uuid

def make_job(**kwargs):
    defaults = dict(
        id=str(uuid.uuid4()),
        input_path="/media/input/test.mp4",
        output_path="/media/output/test.mkv",
        quality=23,
        resolution="1920x1080",
        video_bitrate=1000,
        audio_bitrate=96,
        status=JobStatus.PENDING,
    )
    defaults.update(kwargs)
    return ConversionJob(**defaults)

def test_no_r_flag():
    cmd = build_handbrake_cmd(make_job())
    assert "-r" not in cmd

def test_no_b_flag_when_q_present():
    cmd = build_handbrake_cmd(make_job())
    assert "-q" in cmd
    assert "-b" not in cmd

def test_resolution_parsed_correctly():
    cmd = build_handbrake_cmd(make_job(resolution="1920x1080"))
    assert "--width" in cmd
    assert "1920" in cmd
    assert "--height" in cmd
    assert "1080" in cmd

def test_encoder_explicit():
    cmd = build_handbrake_cmd(make_job())
    assert "--encoder" in cmd

def test_no_json_flag():
    cmd = build_handbrake_cmd(make_job())
    assert "--json" not in cmd

def test_empty_resolution_omits_width_height():
    cmd = build_handbrake_cmd(make_job(resolution=""))
    assert "--width" not in cmd
    assert "--height" not in cmd
```

---

## Verification

Run locally (or in container):
```bash
cd /home/akun/handbrake2resilio
python3 -m pytest handbrake-service/unit-tests/test_build_command.py -v
```

All 6 tests must pass.

Optionally, inside the handbrake container, run:
```bash
docker compose -f deployment/docker-compose.yml exec handbrake-service HandBrakeCLI --help
```
to confirm `--encoder`, `--width`, `--height`, `-q` are valid flags in the installed version.

---

## Acceptance Criteria (from WEA-262)

- [ ] `-r <resolution>` flag removed from the CLI command
- [ ] Resolution passed as `--width W --height H` (parsed from `resolution` field), or omitted if empty
- [ ] `-b <video_bitrate>` removed when `-q` is set
- [ ] `--encoder x265` (or `x264`) explicitly set
- [ ] `build_handbrake_cmd()` extracted and unit-tested with 6 passing tests
- [ ] Full HandBrakeCLI command logged at DEBUG level before subprocess launch
- [ ] If `returncode != 0`, stderr captured and stored in `job.error_message`
- [ ] Type hints and docstring on `build_handbrake_cmd` and `run_handbrake_conversion`
- [ ] 📖 `docs/NEXT_STEPS.md` updated to remove stale HandBrake CLI note

## CAT-B1 checklist
- [ ] Full command logged at DEBUG before Popen
- [ ] Stderr captured on non-zero exit and stored in `job.error_message`
- [ ] `/health` endpoint unchanged

---

## STOP

After all tests pass and PR is open:

1. Run `git branch --show-current` — confirm branch is `spcmanspiff/wea-262-*`
2. Open PR against `master`
3. Check if sibling **SPRINT_04B_FIX_PROGRESS_MONITORING.md** has a PR open:
   ```bash
   gh pr list --repo spacemanspiff99/handbrake2resilio --state open --json number,headRefName
   ```
4. If sibling PR is open: both are done — start **SPRINT_04C_E2E_VERIFICATION.md** in a fresh chat using **Claude 4.6 Sonnet**.
5. If sibling has no PR: output "⏸ HOLDING — WEA-262 PR open. Waiting for WEA-263 (progress monitoring) PR before starting E2E."

💥
