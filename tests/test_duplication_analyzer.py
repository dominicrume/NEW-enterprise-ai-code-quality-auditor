"""Duplication analyzer — 6-line shingle detector."""
from auditor.analyzers import duplication_analyzer


UNIQUE_BLOCK = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\n"


def test_no_duplication_when_unique(minimal_spec):
    code = {"files": {"a.py": UNIQUE_BLOCK}, "manifest": []}
    score = duplication_analyzer.analyze(code, [], minimal_spec)
    assert score.name == "duplication_pct"
    assert score.unit == "%"
    assert score.value == 0.0


def test_identical_files_are_100pct_duplicated(minimal_spec):
    code = {"files": {"a.py": UNIQUE_BLOCK, "b.py": UNIQUE_BLOCK}, "manifest": []}
    score = duplication_analyzer.analyze(code, [], minimal_spec)
    # All 12 lines participate in a duplicated shingle.
    assert score.value == 100.0


def test_short_files_below_shingle_window_are_not_flagged(minimal_spec):
    short = "x = 1\ny = 2\n"  # only 2 lines, < k=6
    code = {"files": {"a.py": short, "b.py": short}, "manifest": []}
    assert duplication_analyzer.analyze(code, [], minimal_spec).value == 0.0


def test_whitespace_normalisation(minimal_spec):
    a = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\n"
    b = "a   =   1\n  b = 2  \n   c = 3\nd = 4\ne = 5\n\tf = 6\n"
    code = {"files": {"a.py": a, "b.py": b}, "manifest": []}
    # Despite different spacing, the 6-line shingle matches → 100%.
    assert duplication_analyzer.analyze(code, [], minimal_spec).value == 100.0


def test_blank_lines_are_ignored(minimal_spec):
    code = {"files": {"a.py": "\n\n\n", "b.py": "\n"}, "manifest": []}
    assert duplication_analyzer.analyze(code, [], minimal_spec).value == 0.0
