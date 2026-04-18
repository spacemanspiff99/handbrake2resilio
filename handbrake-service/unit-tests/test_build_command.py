"""Unit tests for build_handbrake_cmd() in handbrake_service_simple."""

import os
import sys
import uuid
from unittest.mock import patch

# Allow importing handbrake_service_simple and shared from the project root
_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, ".."))        # handbrake-service/
sys.path.insert(0, os.path.join(_HERE, "..", ".."))  # repo root (for shared/)

# Patch module-level side-effects so import succeeds without a real DB or OS mounts
with patch("shared.db.get_db_connection"), \
     patch("os.makedirs"), \
     patch("os.path.isdir", return_value=False), \
     patch("os.access", return_value=True):
    from handbrake_service_simple import build_handbrake_cmd  # noqa: E402

from shared.job_queue import ConversionJob, JobStatus  # noqa: E402


def make_job(**kwargs) -> ConversionJob:
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
