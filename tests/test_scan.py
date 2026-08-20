"""Tests for the zero-ceremony directory scan.

The behaviour under test that matters most: a metric that cannot be
computed must be reported as inapplicable, never as 0.00. Silently
scoring an unscanned codebase as perfect is the exact failure mode the
instrument exists to expose.
"""
from pathlib import Path

import pytest

from auditor.core.calibration import band_for
from auditor.core.scan import scan_directory


@pytest.fixture
def ts_project(tmp_path: Path) -> Path:
    (tmp_path / "app.ts").write_text("export const x = 1;\n" * 5)
    (tmp_path / "ui.tsx").write_text("export const C = () => null;\n")
    return tmp_path


@pytest.fixture
def py_project(tmp_path: Path) -> Path:
    (tmp_path / "main.py").write_text(
        "def handler(flag):\n"
        "    if flag:\n"
        "        return 1\n"
        "    return 0\n"
    )
    return tmp_path


def _outcome(result, name):
    return next(o for o in result.outcomes if o.name == name)


def test_python_only_metrics_are_skipped_not_zeroed(ts_project):
    """A TypeScript project must not be scored 0.00 on Python-only checks."""
    result = scan_directory(ts_project)

    for metric in ("security_density", "complexity_mean"):
        outcome = _outcome(result, metric)
        assert not outcome.applicable, f"{metric} should be inapplicable"
        assert outcome.value is None, f"{metric} must not report a number"
        assert "Python" in outcome.skipped_reason

    assert result.coverage_note is not None
    assert "not a clean result" in result.coverage_note


def test_language_agnostic_metric_still_runs_on_typescript(ts_project):
    duplication = _outcome(scan_directory(ts_project), "duplication_pct")
    assert duplication.applicable
    assert duplication.value is not None


def test_python_project_reports_all_static_metrics(py_project):
    result = scan_directory(py_project)
    assert result.python_files == 1
    for metric in ("security_density", "complexity_mean", "duplication_pct"):
        assert _outcome(result, metric).applicable
    assert result.coverage_note is None


def test_scope_drift_requires_a_spec(py_project):
    without = _outcome(scan_directory(py_project), "hallucinations")
    assert not without.applicable
    assert "--spec" in without.skipped_reason

    spec = {"name": "demo", "features": [{"id": "a.b"}]}
    with_spec = _outcome(scan_directory(py_project, spec), "hallucinations")
    assert with_spec.applicable


def test_rework_always_needs_a_recorded_session(py_project):
    rework = _outcome(scan_directory(py_project), "correction_freq")
    assert not rework.applicable
    assert "session" in rework.skipped_reason


def test_empty_directory_skips_everything(tmp_path):
    result = scan_directory(tmp_path)
    assert result.file_count == 0
    assert all(not o.applicable for o in result.outcomes)


def test_dependencies_are_excluded_from_the_scan(tmp_path):
    (tmp_path / "main.py").write_text("x = 1\n")
    vendored = tmp_path / "node_modules" / "pkg"
    vendored.mkdir(parents=True)
    (vendored / "index.js").write_text("module.exports = 1;\n" * 50)

    assert scan_directory(tmp_path).file_count == 1


def test_worst_band_drives_the_ci_verdict(py_project):
    result = scan_directory(py_project)
    assert result.worst_band in {"good", "warn", "critical"}


@pytest.mark.parametrize("value,expected", [
    (0.0, "good"), (4.9, "good"), (5.0, "warn"), (9.9, "warn"), (10.0, "critical"),
])
def test_duplication_bands(value, expected):
    assert band_for("duplication_pct", value) == expected


# ------------------------------------------------- test-assert noise

def test_asserts_in_test_files_are_not_security_findings(tmp_path):
    """B101 fires on every assert. In a test file the assert IS the test —
    counting it would score a well-tested codebase worse than an untested one."""
    (tmp_path / "app.py").write_text("def add(a, b):\n    return a + b\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "from app import add\n\n"
        "def test_add():\n"
        + "".join(f"    assert add({i}, 1) == {i + 1}\n" for i in range(40))
    )
    security = next(o for o in scan_directory(tmp_path).outcomes
                    if o.name == "security_density")
    assert security.applicable
    assert security.value == 0.0, "test assertions were counted as vulnerabilities"


def test_asserts_in_production_code_are_still_findings(tmp_path):
    """The rule exists for a reason: -O strips asserts from shipped code."""
    (tmp_path / "auth.py").write_text(
        "def check(user):\n"
        "    assert user.is_admin, 'not an admin'\n"
        "    return True\n"
    )
    security = next(o for o in scan_directory(tmp_path).outcomes
                    if o.name == "security_density")
    assert security.value > 0, "an assert used as a production check must still count"
