"""Hallucination analyzer — set-difference manifest \\ spec."""
from auditor.analyzers import hallucination_analyzer


SPEC = {
    "name": "s", "version": "1",
    "features": [
        {"id": "auth.login", "description": "x"},
        {"id": "auth.register", "description": "y"},
    ],
}


def test_no_hallucinations_when_manifest_matches_spec():
    code = {"files": {}, "manifest": ["auth.login", "auth.register"]}
    assert hallucination_analyzer.analyze(code, [], SPEC).value == 0.0


def test_counts_extras_only():
    code = {"files": {}, "manifest": ["auth.login", "auth.face_recognition",
                                       "auth.admin_backdoor"]}
    assert hallucination_analyzer.analyze(code, [], SPEC).value == 2.0


def test_missing_spec_features_not_counted_as_hallucination():
    # auth.register is in spec but not shipped — that's incompleteness,
    # not hallucination. Metric must be 0.
    code = {"files": {}, "manifest": ["auth.login"]}
    assert hallucination_analyzer.analyze(code, [], SPEC).value == 0.0


def test_empty_manifest_yields_zero():
    code = {"files": {}, "manifest": []}
    assert hallucination_analyzer.analyze(code, [], SPEC).value == 0.0
