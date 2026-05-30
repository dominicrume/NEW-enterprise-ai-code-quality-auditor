"""KYA compliance checker — per-guardrail and aggregate verdict."""
import json
from pathlib import Path

import pytest

from auditor.governance import compliance_checker as cc


GUARDRAILS_SPEC = Path(__file__).parent.parent / "specs" / "governance_guardrails.yaml"


CLEAN_FILES = {
    "app/api.py": (
        "from pydantic import BaseModel\n"
        "from fastapi import Depends\n"
        "\n"
        "class LoginIn(BaseModel):\n"
        "    email: str\n"
        "    password: str\n"
        "\n"
        "def login(body: LoginIn, user=Depends(get_current_user)):\n"
        "    return {'ok': True}\n"
    ),
}


DIRTY_FILES = {
    "app/api.py": (
        "API_KEY = 'sk-ABCDEFGHIJKLMNOPQRSTUV1234567890'\n"
        "def login(email, password):\n"
        "    eval(email)\n"
        "    return True\n"
    ),
}


def test_no_eval_passes_on_clean():
    ok, ev = cc.check_no_eval({"files": CLEAN_FILES})
    assert ok is True
    assert "no eval" in ev


def test_no_eval_fails_on_dirty():
    ok, ev = cc.check_no_eval({"files": DIRTY_FILES})
    assert ok is False
    assert "eval(" in ev


def test_secrets_detector_catches_openai_key():
    ok, ev = cc.check_secrets_not_in_code({"files": DIRTY_FILES})
    assert ok is False
    assert "matched" in ev


def test_secrets_detector_clean():
    assert cc.check_secrets_not_in_code({"files": CLEAN_FILES})[0] is True


def test_input_validation_detects_pydantic():
    assert cc.check_input_validation({"files": CLEAN_FILES})[0] is True


def test_input_validation_fails_without_library():
    assert cc.check_input_validation({"files": DIRTY_FILES})[0] is False


def test_auth_required_detects_depends():
    assert cc.check_auth_required({"files": CLEAN_FILES})[0] is True


def test_auth_required_fails_without_markers():
    assert cc.check_auth_required({"files": DIRTY_FILES})[0] is False


def test_aggregate_verdict_pass_on_clean():
    verdict = cc.evaluate_from_spec({"files": CLEAN_FILES}, GUARDRAILS_SPEC)
    assert verdict.score == 1.0
    assert verdict.verdict == "PASS"
    assert {r.id for r in verdict.results} == {
        "no_eval", "secrets_not_in_code", "input_validation", "auth_required",
    }


def test_aggregate_verdict_fail_on_dirty():
    verdict = cc.evaluate_from_spec({"files": DIRTY_FILES}, GUARDRAILS_SPEC)
    assert verdict.score < 1.0
    assert verdict.verdict == "FAIL"
    # The two universally-violated guardrails:
    failed = {r.id for r in verdict.results if not r.passed}
    assert "no_eval" in failed
    assert "secrets_not_in_code" in failed


def test_unknown_guardrail_is_skipped_not_crash(caplog):
    guardrails = [{"id": "no_eval", "description": "x"},
                  {"id": "made_up_rule", "description": "y"}]
    verdict = cc.evaluate({"files": CLEAN_FILES}, guardrails)
    assert {r.id for r in verdict.results} == {"no_eval"}


def test_verdict_is_json_serialisable():
    verdict = cc.evaluate_from_spec({"files": CLEAN_FILES}, GUARDRAILS_SPEC)
    payload = json.loads(verdict.to_json())
    assert payload["verdict"] == "PASS"
    assert len(payload["results"]) == 4


def test_custom_threshold():
    # Mixed codebase: clean validation/auth file + a separate eval call.
    mixed = {"files": {**CLEAN_FILES, "app/bad.py": "eval(x)\n"}}
    verdict = cc.evaluate_from_spec({"files": mixed["files"]}, GUARDRAILS_SPEC,
                                    threshold=0.75)
    # 3 of 4 pass (no_eval fails) -> 0.75 meets threshold
    assert verdict.score == 0.75
    assert verdict.verdict == "PASS"
