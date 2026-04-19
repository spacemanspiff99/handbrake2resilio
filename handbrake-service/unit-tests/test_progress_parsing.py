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
