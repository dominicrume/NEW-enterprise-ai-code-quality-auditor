"""KYA (Know-Your-Agent) governance compliance scoring.

Scores a captured codebase against the cross-cutting guardrails declared in
``specs/governance_guardrails.yaml``. Each guardrail has a *checker* — a
small function that returns True/False for a given codebase. The aggregate
verdict is the fraction of guardrails that passed.

This is the layer §4 of the proposal calls out as the governance
contribution; Stage 3 (chain attestation via Vorem) is out of scope for the
MSc and is not implemented here, but the verdict object is JSON-serialisable
and stable so a future stage can persist it without re-shaping data.

Adding a guardrail = adding (a) an entry to the YAML spec, and (b) a
checker function in ``CHECKERS``. Unknown guardrails are skipped + logged.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import yaml
from pydantic import BaseModel

from auditor.core.logger import get_logger

log = get_logger("compliance_checker")


class GuardrailResult(BaseModel):
    id: str
    description: str
    passed: bool
    evidence: str = ""


class ComplianceVerdict(BaseModel):
    score: float            # 0.0 — 1.0, fraction of guardrails passed
    verdict: str            # "PASS" if score >= threshold else "FAIL"
    threshold: float = 1.0  # default: zero-tolerance
    results: list[GuardrailResult]

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


CheckerFn = Callable[[dict], tuple[bool, str]]
"""Signature: (codebase) -> (passed, human-readable evidence)."""


# ---------------------------------------------------------------------------
# Individual checkers
# ---------------------------------------------------------------------------

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),                  # OpenAI-style keys
    re.compile(r"AKIA[0-9A-Z]{16}"),                     # AWS access key id
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),                 # GitHub PAT
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),         # Slack token
    re.compile(r"(?i)(password|passwd|api[_-]?key|secret)\s*=\s*['\"][^'\"]{4,}['\"]"),
]

_AUTH_MARKERS = (
    "@login_required", "@requires_auth", "@authenticated", "@require_auth",
    "Depends(get_current_user", "current_user", "verify_token(",
    "is_authenticated", "@jwt_required", "session.user",
)

_PYDANTIC_MARKERS = (
    "BaseModel", "pydantic", "validator(", "field_validator", "TypeAdapter",
    "marshmallow", "Schema",
)


def _scan_python_files(codebase: dict) -> dict[str, str]:
    return {p: c for p, c in codebase.get("files", {}).items() if p.endswith(".py")}


def check_no_eval(codebase: dict) -> tuple[bool, str]:
    hits = []
    for path, content in _scan_python_files(codebase).items():
        for marker in ("eval(", "exec("):
            if marker in content:
                hits.append(f"{path}: {marker}")
    return (not hits, "; ".join(hits) if hits else "no eval/exec found")


def check_secrets_not_in_code(codebase: dict) -> tuple[bool, str]:
    hits = []
    for path, content in codebase.get("files", {}).items():
        for pat in _SECRET_PATTERNS:
            m = pat.search(content)
            if m:
                hits.append(f"{path}: matched {pat.pattern!r}")
                break
    return (not hits, "; ".join(hits) if hits else "no secret patterns matched")


def check_input_validation(codebase: dict) -> tuple[bool, str]:
    files = _scan_python_files(codebase)
    if not files:
        return False, "no Python source to inspect"
    for path, content in files.items():
        if any(marker in content for marker in _PYDANTIC_MARKERS):
            return True, f"validation library detected in {path}"
    return False, f"no validation library in {list(files)}"


def check_auth_required(codebase: dict) -> tuple[bool, str]:
    files = _scan_python_files(codebase)
    if not files:
        return False, "no Python source to inspect"
    for path, content in files.items():
        if any(marker in content for marker in _AUTH_MARKERS):
            return True, f"auth marker detected in {path}"
    return False, "no auth markers found in any file"


CHECKERS: dict[str, CheckerFn] = {
    "no_eval": check_no_eval,
    "secrets_not_in_code": check_secrets_not_in_code,
    "input_validation": check_input_validation,
    "auth_required": check_auth_required,
}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def load_guardrails(path: str | Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("guardrails", [])


def evaluate(codebase: dict, guardrails: list[dict],
             threshold: float = 1.0) -> ComplianceVerdict:
    """Run every guardrail's checker against the codebase."""
    results: list[GuardrailResult] = []
    for g in guardrails:
        gid = g["id"]
        checker = CHECKERS.get(gid)
        if checker is None:
            log.warning("compliance: no checker registered for guardrail %r — skipped", gid)
            continue
        passed, evidence = checker(codebase)
        results.append(GuardrailResult(
            id=gid, description=g.get("description", ""),
            passed=passed, evidence=evidence,
        ))
    if not results:
        score = 0.0
    else:
        score = sum(1 for r in results if r.passed) / len(results)
    return ComplianceVerdict(
        score=score,
        verdict="PASS" if score >= threshold else "FAIL",
        threshold=threshold,
        results=results,
    )


def evaluate_from_spec(codebase: dict, guardrails_path: str | Path,
                       threshold: float = 1.0) -> ComplianceVerdict:
    """Convenience: load the YAML guardrails spec and run ``evaluate``."""
    return evaluate(codebase, load_guardrails(guardrails_path), threshold)
