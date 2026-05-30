"""Complexity analyzer — radon-backed McCabe."""
from auditor.analyzers import complexity_analyzer


SIMPLE = "def f():\n    return 1\n"  # complexity 1

BRANCHY = (
    "def g(x):\n"
    "    if x > 0:\n"
    "        return 1\n"
    "    elif x < 0:\n"
    "        return -1\n"
    "    for i in range(10):\n"
    "        if i == x:\n"
    "            return i\n"
    "    return 0\n"
)  # complexity = 5 per radon


def test_simple_function_is_one(minimal_spec):
    code = {"files": {"a.py": SIMPLE}, "manifest": []}
    score = complexity_analyzer.analyze(code, [], minimal_spec)
    assert score.name == "complexity_mean"
    assert score.unit == "cc"
    assert score.value == 1.0


def test_branchy_function_matches_radon(minimal_spec):
    code = {"files": {"b.py": BRANCHY}, "manifest": []}
    score = complexity_analyzer.analyze(code, [], minimal_spec)
    assert score.value == 5.0


def test_mean_across_files(minimal_spec):
    code = {"files": {"a.py": SIMPLE, "b.py": BRANCHY}, "manifest": []}
    # mean of [1, 5] = 3.0
    assert complexity_analyzer.analyze(code, [], minimal_spec).value == 3.0


def test_non_python_files_skipped(minimal_spec):
    code = {"files": {"a.py": SIMPLE, "x.md": "# notes"}, "manifest": []}
    assert complexity_analyzer.analyze(code, [], minimal_spec).value == 1.0


def test_unparseable_file_is_skipped(minimal_spec):
    code = {"files": {"good.py": SIMPLE, "bad.py": "def broken(:\n"}, "manifest": []}
    # bad.py is logged + skipped, good.py contributes complexity 1
    assert complexity_analyzer.analyze(code, [], minimal_spec).value == 1.0


def test_empty_codebase_returns_zero(minimal_spec):
    score = complexity_analyzer.analyze({"files": {}, "manifest": []}, [], minimal_spec)
    assert score.value == 0.0
