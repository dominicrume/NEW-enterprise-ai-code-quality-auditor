"""Tests for continuous auditing.

The loop itself sleeps, so the logic it depends on is factored into pure
functions and tested directly: change detection, and the delta between two
audits. A short live-loop test covers the wiring.
"""
import threading
import time
from pathlib import Path

import pytest

from auditor.core.scan import scan_directory
from auditor.core.watch import (
    changed_files,
    diff_results,
    fingerprint,
    watch_directory,
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "main.py").write_text("def f():\n    return 1\n")
    return tmp_path


def _delta(deltas, name):
    return next((d for d in deltas if d.name == name), None)


# ---------------------------------------------------------------- fingerprint

def test_fingerprint_sees_new_modified_and_deleted_files(project):
    before = fingerprint(project)

    (project / "added.py").write_text("x = 1\n")
    assert changed_files(before, fingerprint(project)) == ["added.py"]

    after_add = fingerprint(project)
    (project / "main.py").write_text("def f():\n    return 2\n\n# changed\n")
    assert "main.py" in changed_files(after_add, fingerprint(project))

    after_edit = fingerprint(project)
    (project / "added.py").unlink()
    assert changed_files(after_edit, fingerprint(project)) == ["added.py"]


def test_fingerprint_ignores_dependency_directories(project):
    vendored = project / "node_modules" / "left-pad"
    vendored.mkdir(parents=True)
    (vendored / "index.js").write_text("module.exports = 1;\n")
    assert not any("node_modules" in k for k in fingerprint(project))


def test_identical_tree_produces_no_changes(project):
    assert changed_files(fingerprint(project), fingerprint(project)) == []


# ------------------------------------------------------------------- deltas

def test_no_deltas_when_metrics_are_unchanged(project):
    result = scan_directory(project)
    assert diff_results(result, result) == []


def test_duplication_regression_is_reported_as_worse(project):
    before = scan_directory(project)
    block = "def helper(x):\n    a = x + 1\n    b = a * 2\n    c = b - 3\n    d = c / 4\n    return d\n"
    (project / "one.py").write_text(block)
    (project / "two.py").write_text(block)

    delta = _delta(diff_results(before, scan_directory(project)), "duplication_pct")
    assert delta is not None
    assert delta.after > delta.before
    assert delta.direction == "worse"


def test_metric_coming_online_is_flagged(tmp_path):
    """The first Python file brings the Python-only analysers into scope."""
    (tmp_path / "ui.ts").write_text("export const a = 1;\n")
    before = scan_directory(tmp_path)
    assert _delta(before.outcomes, "security_density") is not None

    (tmp_path / "main.py").write_text("def f():\n    return 1\n")
    deltas = diff_results(before, scan_directory(tmp_path))

    security = _delta(deltas, "security_density")
    assert security is not None
    assert security.became_measurable
    assert not security.became_unmeasurable


def test_band_crossing_is_detected(project):
    before = scan_directory(project)
    block = "def helper(x):\n    a = x + 1\n    b = a * 2\n    c = b - 3\n    d = c / 4\n    return d\n"
    (project / "one.py").write_text(block)
    (project / "two.py").write_text(block)

    delta = _delta(diff_results(before, scan_directory(project)), "duplication_pct")
    assert delta.changed_band
    assert delta.after_band == "critical"


def test_scope_drift_needs_a_spec_to_move(project):
    """Off-spec routes are only detectable when a spec says what was asked for."""
    spec = {"name": "demo", "features": [{"id": "auth.register"}]}
    before = scan_directory(project, spec)
    (project / "api.py").write_text(
        'from fastapi import FastAPI\n'
        'app = FastAPI()\n\n'
        '@app.get("/health")\n'
        'def health():\n    return {}\n'
    )
    delta = _delta(diff_results(before, scan_directory(project, spec)), "hallucinations")
    assert delta is not None
    assert delta.after > (delta.before or 0)


# --------------------------------------------------------------- live loop

def test_watch_loop_emits_an_event_for_a_real_edit(project):
    events = []
    stop = threading.Event()

    def consume():
        for event in watch_directory(project, interval=0.1, settle=0.1,
                                     stop=stop.is_set):
            events.append(event)
            break

    worker = threading.Thread(target=consume, daemon=True)
    worker.start()
    time.sleep(0.3)
    (project / "late.py").write_text("def g():\n    return 2\n")
    worker.join(timeout=5)
    stop.set()

    assert events, "watch produced no event for a new file"
    assert "late.py" in events[0].changed_files
