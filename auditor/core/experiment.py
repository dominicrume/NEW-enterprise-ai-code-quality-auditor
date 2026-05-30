"""Run the five-condition experiment end-to-end and emit one combined CSV.

For one run_id and one spec, this drives every adapter sequentially, scores
each captured codebase with every analyzer, and writes a single immutable
CSV report ready for the statistical comparison notebook.

The function is split into a programmable core (`run_experiment`) used by
the CLI and the integration test, and a CLI-side helper that constructs
the default adapters from a captures directory.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from auditor.adapters.antigravity_adapter import AntigravityAdapter
from auditor.adapters.base_adapter import BaseAdapter
from auditor.adapters.claude_code_adapter import ClaudeCodeAdapter
from auditor.adapters.cursor_agent_adapter import CursorAgentAdapter
from auditor.adapters.human_control_adapter import HumanControlAdapter
from auditor.adapters.replit_agent_adapter import ReplitAgentAdapter
from auditor.analyzers import (
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
    security_analyzer,
)
from auditor.core.logger import get_logger
from auditor.core.runner import load_spec
from auditor.models.audit_result import AuditResult, MetricScore

log = get_logger("experiment")

ANALYZERS = [
    security_analyzer,
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
]

CSV_HEADER = [
    "run_id", "condition", "spec_name", "spec_version",
    "metric", "value", "unit", "timestamp",
]


def _score_one(adapter: BaseAdapter, spec: dict, run_id: str) -> AuditResult:
    codebase, interaction_log = adapter.generate(spec)
    metrics: list[MetricScore] = [
        mod.analyze(codebase, interaction_log, spec) for mod in ANALYZERS
    ]
    return AuditResult(
        run_id=run_id,
        condition=adapter.name,  # type: ignore[arg-type]
        spec_name=spec["name"],
        spec_version=str(spec.get("version", "0")),
        metrics=metrics,
        timestamp=datetime.now(timezone.utc),
    )


def run_experiment(
    spec_path: str | Path,
    run_id: str,
    adapters: Iterable[BaseAdapter],
    reports_dir: str | Path = "data/reports",
) -> Path:
    """Run every adapter against the spec, score with every analyzer, write CSV.

    The report is immutable (engineering principle 8) — if the target file
    already exists, refuse to overwrite. Re-run with a new ``run_id``.
    """
    spec = load_spec(spec_path)
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / f"{run_id}.csv"
    if out_path.exists():
        raise FileExistsError(
            f"report already exists (reports are immutable): {out_path}"
        )

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        for adapter in adapters:
            log.info("experiment: condition=%s spec=%s run_id=%s",
                     adapter.name, spec["name"], run_id)
            result = _score_one(adapter, spec, run_id)
            for m in result.metrics:
                writer.writerow([
                    result.run_id, result.condition, result.spec_name,
                    result.spec_version, m.name, m.value, m.unit,
                    result.timestamp.isoformat(),
                ])
    return out_path


def _replay_runner(raw_stream_path: Path):
    """A runner that returns events captured to disk by a prior adapter run."""
    def _run(prompt: str, work_dir: Path) -> list[dict]:
        return json.loads(Path(raw_stream_path).read_text())
    return _run


def build_default_adapters(run_id: str, captures_root: Path,
                           raw_root: Path | None = None) -> list[BaseAdapter]:
    """Construct the five adapters in canonical order from a captures layout.

    Expected layout under ``captures_root/<run_id>/<condition>/``:
      * human_control/   code/   interaction_log.json
      * <agent>/         code/   raw_stream.json

    The agent adapters use a replay runner so the experiment is deterministic
    once vendors have been captured — matching engineering principle 4.
    """
    base = Path(captures_root) / run_id
    raw_root = Path(raw_root) if raw_root else Path("data/raw")
    return [
        HumanControlAdapter(
            code_dir=base / "human_control" / "code",
            log_path=base / "human_control" / "interaction_log.json",
            run_id=run_id, raw_root=raw_root,
        ),
        ClaudeCodeAdapter(
            work_dir=base / "claude_code" / "code",
            run_id=run_id, raw_root=raw_root,
            runner=_replay_runner(base / "claude_code" / "raw_stream.json"),
        ),
        CursorAgentAdapter(
            work_dir=base / "cursor_agent" / "code",
            run_id=run_id, raw_root=raw_root,
            runner=_replay_runner(base / "cursor_agent" / "raw_stream.json"),
        ),
        AntigravityAdapter(
            work_dir=base / "antigravity" / "code",
            run_id=run_id, raw_root=raw_root,
            runner=_replay_runner(base / "antigravity" / "raw_stream.json"),
        ),
        ReplitAgentAdapter(
            work_dir=base / "replit_agent" / "code",
            run_id=run_id, raw_root=raw_root,
            runner=_replay_runner(base / "replit_agent" / "raw_stream.json"),
        ),
    ]
