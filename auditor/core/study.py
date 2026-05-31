"""Main-study orchestration — the engine the CLI's `experiment` and the
`scripts/run_full_experiment.py` wrapper both call.

Public entry: ``run_study(reps, run_label, ...) -> Path`` — runs the full
shuffled (condition × spec × rep) loop, scores everything, and writes one
long-format CSV at ``data/reports/<run_label>.csv`` plus its provenance.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

import yaml

from auditor.adapters.antigravity_adapter import AntigravityAdapter
from auditor.adapters.claude_code_adapter import ClaudeCodeAdapter
from auditor.adapters.cursor_agent_adapter import CursorAgentAdapter
from auditor.adapters.replit_agent_adapter import ReplitAgentAdapter
from auditor.analyzers import (
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
    security_analyzer,
)

DEFAULT_SPECS = [
    "specs/agent_education_system.yaml",
    "specs/data_pipeline.yaml",
    "specs/internal_tool_cli.yaml",
]
AGENT_CONDITIONS = ("claude_code", "cursor_agent", "replit_agent", "antigravity")
ANALYZERS = [
    hallucination_analyzer, keystroke_analyzer, complexity_analyzer,
    duplication_analyzer, security_analyzer,
]


def _spec_key(spec_path: str) -> str:
    return Path(spec_path).stem


def _prompt_hash(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def _record_provenance(work_dir: Path, spec: dict, duration_s: float, model: str) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "model.txt").write_text(model)
    (work_dir / "duration_seconds.txt").write_text(f"{duration_s:.3f}")
    (work_dir / "prompt.sha256").write_text(_prompt_hash(spec))


def _run_one(condition: str, spec: dict, spec_key: str, rep: int,
             run_label: str, repo_root: Path, sessions_root: Path,
             replay_root: Path) -> dict:
    run_id = f"{run_label}__{spec_key}__{condition}__rep{rep:02d}"
    session = sessions_root / f"{spec_key}_{condition}_rep{rep:02d}"
    session.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()
    status: dict = {"run_id": run_id, "condition": condition,
                    "spec": spec_key, "rep": rep, "outcome": "ok"}
    try:
        if condition == "claude_code":
            adapter = ClaudeCodeAdapter(work_dir=session, run_id=run_id,
                                        raw_root=repo_root / "data" / "raw")
            model = "claude-sonnet-4-6"
        elif condition == "cursor_agent":
            adapter = CursorAgentAdapter(work_dir=session, run_id=run_id,
                                         raw_root=repo_root / "data" / "raw")
            model = "cursor-auto"
        elif condition == "replit_agent":
            replay = replay_root / f"{spec_key}_{condition}_rep{rep:02d}"
            if not replay.exists():
                status.update(outcome="missing_replay", note=str(replay))
                return status
            adapter = ReplitAgentAdapter(work_dir="/tmp/unused", replay_dir=replay,
                                         run_id=run_id,
                                         raw_root=repo_root / "data" / "raw")
            model = "replit-agent-default"
        elif condition == "antigravity":
            replay = replay_root / f"{spec_key}_{condition}_rep{rep:02d}"
            if not replay.exists():
                status.update(outcome="missing_replay", note=str(replay))
                return status
            adapter = AntigravityAdapter(work_dir="/tmp/unused", replay_dir=replay,
                                         run_id=run_id,
                                         raw_root=repo_root / "data" / "raw")
            model = "gemini-3.5-flash-medium"
        else:
            raise ValueError(f"unknown condition: {condition}")

        codebase, log = adapter.generate(spec)
        duration = time.monotonic() - t0
        _record_provenance(repo_root / "data" / "raw" / run_id / condition,
                           spec, duration, model)
        status.update(files=len(codebase["files"]), events=len(log),
                      duration_s=round(duration, 3))
    except Exception as exc:  # noqa: BLE001
        status.update(outcome="error", error=type(exc).__name__,
                      error_msg=str(exc)[:200],
                      duration_s=round(time.monotonic() - t0, 3))
        traceback.print_exc()
    return status


def _score_all(run_label: str, statuses: list[dict],
               specs: list[str], repo_root: Path) -> Path:
    ts = datetime.now(timezone.utc).isoformat()
    spec_cache = {s: yaml.safe_load(open(repo_root / s)) for s in specs}
    rows: list[dict] = []

    for s in statuses:
        if s["outcome"] != "ok":
            continue
        spec_path = next(p for p in specs if _spec_key(p) == s["spec"])
        spec = spec_cache[spec_path]
        raw_dir = repo_root / "data" / "raw" / s["run_id"] / s["condition"]
        codebase = json.loads((raw_dir / "codebase.json").read_text())
        log = json.loads((raw_dir / "interaction_log.json").read_text())
        for mod in ANALYZERS:
            score = mod.analyze(codebase, log, spec)
            rows.append({
                "run_label": run_label, "run_id": s["run_id"],
                "condition": s["condition"], "spec_name": spec["name"],
                "spec_version": spec["version"], "rep": s["rep"],
                "metric": score.name, "value": round(score.value, 6),
                "unit": score.unit, "duration_s": s.get("duration_s"),
                "timestamp": ts,
            })

    out = repo_root / "data" / "reports" / f"{run_label}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["run_label", "run_id", "condition", "spec_name", "spec_version",
              "rep", "metric", "value", "unit", "duration_s", "timestamp"]
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    prov = repo_root / "data" / "reports" / f"{run_label}.provenance.json"
    prov.write_text(json.dumps({
        "kind": "main_study",
        "spec_files": specs,
        "conditions": sorted({s["condition"] for s in statuses}),
        "reps_per_cell": max((s["rep"] for s in statuses), default=-1) + 1,
        "successful_runs": sum(1 for s in statuses if s["outcome"] == "ok"),
        "failed_runs": sum(1 for s in statuses if s["outcome"] != "ok"),
        "statuses": statuses,
        "timestamp": ts,
    }, indent=2))
    return out


def run_study(reps: int = 10, run_label: str = "main_study_run_001",
              seed: int = 42, specs: Iterable[str] | None = None,
              skip: Iterable[str] = (),
              repo_root: Path | None = None,
              log: Callable[[str], None] = print) -> Path:
    """Run the full study. Returns the CSV path."""
    repo_root = repo_root or Path.cwd()
    specs = list(specs) if specs else list(DEFAULT_SPECS)
    enabled = [c for c in AGENT_CONDITIONS if c not in skip]
    if not enabled:
        raise SystemExit("No conditions enabled — nothing to do.")

    triples = [(c, s, r) for c in enabled for s in specs for r in range(reps)]
    random.Random(seed).shuffle(triples)
    sessions_root = Path.home() / "sessions" / run_label
    replay_root = repo_root / "replay_dirs" / run_label

    log(f"[study] {len(triples)} runs scheduled "
        f"({len(enabled)} conditions × {len(specs)} specs × {reps} reps)")

    statuses: list[dict] = []
    for i, (cond, spec_path, rep) in enumerate(triples, 1):
        spec = yaml.safe_load(open(repo_root / spec_path))
        log(f"[{i:3d}/{len(triples)}] {cond} · {_spec_key(spec_path)} · rep{rep:02d}")
        statuses.append(_run_one(cond, spec, _spec_key(spec_path), rep,
                                 run_label, repo_root, sessions_root, replay_root))

    by_outcome: dict[str, int] = {}
    for s in statuses:
        by_outcome[s["outcome"]] = by_outcome.get(s["outcome"], 0) + 1
    log(f"[study] outcome summary: {by_outcome}")

    csv_path = _score_all(run_label, statuses, specs, repo_root)
    log(f"[study] CSV: {csv_path}")
    return csv_path
