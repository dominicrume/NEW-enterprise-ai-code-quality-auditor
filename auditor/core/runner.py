"""Orchestrates one audit run: adapter -> analyzers -> result."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml

from auditor.adapters.base_adapter import BaseAdapter
from auditor.analyzers import (
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
    security_analyzer,
)
from auditor.core.config import settings
from auditor.core.logger import get_logger
from auditor.models.audit_result import AuditResult, MetricScore

log = get_logger("runner")

ANALYZERS = [
    security_analyzer,
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
]


def load_spec(spec_path: str | Path) -> dict:
    with open(spec_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_audit(spec_path: str | Path, adapter: BaseAdapter) -> AuditResult:
    spec = load_spec(spec_path)
    log.info("Running adapter=%s on spec=%s", adapter.name, spec["name"])
    codebase, interaction_log = adapter.generate(spec)

    metrics: list[MetricScore] = []
    for mod in ANALYZERS:
        metrics.append(mod.analyze(codebase, interaction_log, spec))

    return AuditResult(
        run_id=settings.run_id,
        condition=adapter.name,  # type: ignore[arg-type]
        spec_name=spec["name"],
        spec_version=str(spec.get("version", "0")),
        metrics=metrics,
        timestamp=datetime.now(timezone.utc),
    )
