"""Keystroke dynamics: backspace/delete frequency per 1000 keystrokes."""
from auditor.models.audit_result import MetricScore


def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore:
    total = sum(1 for e in interaction_log if e.get("type") == "keystroke") or 1
    corrections = sum(
        1 for e in interaction_log if e.get("type") in {"backspace", "delete"}
    )
    return MetricScore(
        name="correction_freq", value=(corrections / total) * 1000, unit="per_kkey"
    )
