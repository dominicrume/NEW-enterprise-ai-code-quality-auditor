"""Cyclomatic complexity — radon-backed McCabe per function.

See docs/METRICS.md. Scope: Python only (.py). Other languages are skipped
and logged; if the codebase has zero scorable functions the metric is 0.0.
"""
from __future__ import annotations

from radon.complexity import cc_visit

from auditor.core.logger import get_logger
from auditor.models.audit_result import MetricScore

log = get_logger("complexity_analyzer")


def _function_complexities(files: dict[str, str]) -> list[int]:
    scores: list[int] = []
    for path, content in files.items():
        if not path.endswith(".py"):
            continue
        try:
            blocks = cc_visit(content)
        except (SyntaxError, ValueError) as e:
            log.warning("complexity: skipped %s (%s)", path, e)
            continue
        scores.extend(b.complexity for b in blocks)
    return scores


def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore:
    files = codebase.get("files", {})
    scores = _function_complexities(files)
    mean = sum(scores) / len(scores) if scores else 0.0
    return MetricScore(name="complexity_mean", value=mean, unit="cc")
