"""Each analyzer has a test. Green = experiment trustable.

The security analyzer is now a local Bandit scan over the captured
codebase (see test_security_analyzer.py for full coverage).
"""
from auditor.analyzers import (
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
    security_analyzer,
)


def test_security_signature_unchanged(minimal_spec):
    bad = {"files": {"x.py": "import subprocess\nsubprocess.call('ls', shell=True)\n"},
           "manifest": []}
    score = security_analyzer.analyze(bad, [], minimal_spec)
    assert score.name == "security_density"
    assert score.value > 0


def test_complexity_counts_decisions(codebase_clean, minimal_spec):
    score = complexity_analyzer.analyze(codebase_clean, [], minimal_spec)
    assert score.name == "complexity_mean"


def test_duplication_zero_on_clean(codebase_clean, minimal_spec):
    score = duplication_analyzer.analyze(codebase_clean, [], minimal_spec)
    assert score.value == 0.0


def test_hallucination_detected(codebase_hallucinating, minimal_spec):
    score = hallucination_analyzer.analyze(codebase_hallucinating, [], minimal_spec)
    assert score.value == 2  # face_recognition + admin_backdoor are NOT in spec


def test_keystroke_correction_freq(codebase_clean, minimal_spec, interaction_log_typical):
    score = keystroke_analyzer.analyze(codebase_clean, interaction_log_typical, minimal_spec)
    assert score.name == "correction_freq"
    # 100 corrections / 900 keystrokes = 111.11 per 1000
    assert 100 < score.value < 120
