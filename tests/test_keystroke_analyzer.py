"""Keystroke analyzer — corrections per 1000 keystrokes."""
from auditor.analyzers import keystroke_analyzer


def test_balanced_corrections():
    log = [{"type": "keystroke"}] * 1000 + [{"type": "backspace"}] * 100
    score = keystroke_analyzer.analyze({"files": {}, "manifest": []}, log, {})
    assert score.name == "correction_freq"
    assert score.unit == "per_kkey"
    assert score.value == 100.0


def test_delete_and_backspace_both_count():
    log = ([{"type": "keystroke"}] * 1000
           + [{"type": "backspace"}] * 30
           + [{"type": "delete"}] * 20)
    assert keystroke_analyzer.analyze({"files": {}}, log, {}).value == 50.0


def test_agent_only_log_returns_zero():
    # Pure agent conditions have no keystrokes → metric is 0 by construction.
    log = [{"type": "agent_action"}] * 50
    assert keystroke_analyzer.analyze({"files": {}}, log, {}).value == 0.0


def test_empty_log_returns_zero():
    assert keystroke_analyzer.analyze({"files": {}}, [], {}).value == 0.0
