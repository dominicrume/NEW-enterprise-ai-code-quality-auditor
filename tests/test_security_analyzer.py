"""Security analyzer — local Bandit scan of the captured codebase."""
import pytest

from auditor.analyzers import security_analyzer


def test_returns_metric_score_per_kloc():
    """A clean codebase yields zero density; the contract shape is fixed."""
    codebase = {"files": {"safe.py": "def add(a, b):\n    return a + b\n"},
                "manifest": []}
    score = security_analyzer.analyze(codebase, [], {"name": "x"})
    assert score.name == "security_density"
    assert score.unit == "per_kloc"
    assert score.value == pytest.approx(0.0)


def test_detects_known_cwe_pattern():
    """A trivial CWE pattern (use of `assert` in non-test code = B101)
    should be flagged by Bandit and reflected in density > 0."""
    codebase = {"files": {"bad.py": "import subprocess\nsubprocess.call('ls', shell=True)\n"},
                "manifest": []}
    score = security_analyzer.analyze(codebase, [], {"name": "x"})
    assert score.value > 0, "expected Bandit to flag shell=True (CWE-78)"


def test_empty_codebase_yields_zero():
    score = security_analyzer.analyze({"files": {}, "manifest": []}, [], {"name": "x"})
    assert score.value == 0.0


def test_non_python_files_are_ignored():
    """Bandit only scans Python; YAML/MD should not throw."""
    codebase = {"files": {"README.md": "# title\n", "spec.yaml": "name: x\n"},
                "manifest": []}
    score = security_analyzer.analyze(codebase, [], {"name": "x"})
    assert score.value == 0.0
