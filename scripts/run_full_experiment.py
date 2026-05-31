"""Run the full pre-registered experiment: 4 agent conditions × 3 specs × K reps.

This is the script the dissertation cites. It:
  1. Loads the 3 pre-registered specs.
  2. Shuffles (condition × spec × rep) order to break time-of-day clustering.
  3. For each triple, runs the relevant adapter into a clean per-run work_dir.
  4. Persists model.txt + duration_seconds.txt + prompt.sha256 alongside the
     normal capture-contract artefacts.
  5. After all runs complete, scores every captured run and writes one
     long-format CSV at data/reports/<run_label>.csv.

human_control is NOT included here — it is hand-driven via
scripts/start_human_session.sh and added to the same CSV after the fact.

Usage:
    PYTHONPATH=. python scripts/run_full_experiment.py \\
        --reps 10 --run-label main_study_run_001

Environment overrides (optional):
    AUDITOR_SKIP_CLAUDE=1   skip claude_code
    AUDITOR_SKIP_CURSOR=1   skip cursor_agent
    AUDITOR_SKIP_REPLIT=1   skip replit_agent  (replay only — needs replay_dirs/replit_rep<N>/)
    AUDITOR_SKIP_ANTIGRAV=1 skip antigravity   (replay only — needs replay_dirs/antigravity_rep<N>/)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime, timezone

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from auditor.adapters.claude_code_adapter import ClaudeCodeAdapter
from auditor.adapters.cursor_agent_adapter import CursorAgentAdapter
from auditor.adapters.replit_agent_adapter import ReplitAgentAdapter
from auditor.adapters.antigravity_adapter import AntigravityAdapter
from auditor.analyzers import (
    hallucination_analyzer,
    keystroke_analyzer,
    complexity_analyzer,
    duplication_analyzer,
    security_analyzer,
)


SPECS = [
    "specs/agent_education_system.yaml",
    "specs/data_pipeline.yaml",
    "specs/internal_tool_cli.yaml",
]

ANALYZERS = [
    hallucination_analyzer,
    keystroke_analyzer,
    complexity_analyzer,
    duplication_analyzer,
    security_analyzer,
]


def _spec_key(spec_path: str) -> str:
    return Path(spec_path).stem


def _load_spec(spec_path: str) -> dict:
    return yaml.safe_load(open(REPO / spec_path))


def _prompt_hash(spec: dict) -> str:
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def _session_root(run_label: str, condition: str, spec_key: str, rep: int) -> Path:
    return Path.home() / "sessions" / run_label / f"{spec_key}_{condition}_rep{rep:02d}"


def _replay_root(run_label: str, condition: str, spec_key: str, rep: int) -> Path:
    return REPO / "replay_dirs" / run_label / f"{spec_key}_{condition}_rep{rep:02d}"


def _record_provenance(work_dir: Path, condition: str, spec: dict,
                       duration_s: float, model: str) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "model.txt").write_text(model)
    (work_dir / "duration_seconds.txt").write_text(f"{duration_s:.3f}")
    (work_dir / "prompt.sha256").write_text(_prompt_hash(spec))


def _run_one(condition: str, spec_path: str, rep: int, run_label: str) -> dict:
    """Run one (condition, spec, rep) triple. Returns a status dict."""
    spec = _load_spec(spec_path)
    spec_key = _spec_key(spec_path)
    run_id = f"{run_label}__{spec_key}__{condition}__rep{rep:02d}"
    session = _session_root(run_label, condition, spec_key, rep)
    session.mkdir(parents=True, exist_ok=True)

    t0 = time.monotonic()
    status = {"run_id": run_id, "condition": condition, "spec": spec_key,
              "rep": rep, "outcome": "ok"}

    try:
        if condition == "claude_code":
            adapter = ClaudeCodeAdapter(work_dir=session, run_id=run_id)
            model = "claude-sonnet-4-6"  # pinned; update if your CLI exposes the live version
        elif condition == "cursor_agent":
            adapter = CursorAgentAdapter(work_dir=session, run_id=run_id)
            model = "cursor-auto"
        elif condition == "replit_agent":
            replay = _replay_root(run_label, condition, spec_key, rep)
            if not replay.exists():
                status.update(outcome="missing_replay",
                              note=f"expected replay at {replay}")
                return status
            adapter = ReplitAgentAdapter(work_dir="/tmp/unused",
                                         replay_dir=replay,
                                         run_id=run_id)
            model = "replit-agent-default"
        elif condition == "antigravity":
            replay = _replay_root(run_label, condition, spec_key, rep)
            if not replay.exists():
                status.update(outcome="missing_replay",
                              note=f"expected replay at {replay}")
                return status
            adapter = AntigravityAdapter(work_dir="/tmp/unused",
                                         replay_dir=replay,
                                         run_id=run_id)
            model = "gemini-3.5-flash-medium"
        else:
            raise ValueError(f"unknown condition: {condition}")

        codebase, log = adapter.generate(spec)
        duration = time.monotonic() - t0

        raw_root = REPO / "data" / "raw" / run_id / condition
        _record_provenance(raw_root, condition, spec, duration, model)
        status["files"] = len(codebase["files"])
        status["events"] = len(log)
        status["duration_s"] = round(duration, 3)
    except Exception as exc:  # noqa: BLE001
        status.update(outcome="error",
                      error=type(exc).__name__,
                      error_msg=str(exc)[:200],
                      duration_s=round(time.monotonic() - t0, 3))
        traceback.print_exc()
    return status


def _score_all(run_label: str, statuses: list[dict]) -> Path:
    """Score every successful run and emit one long-format CSV."""
    ts = datetime.now(timezone.utc).isoformat()
    spec_cache = {s: _load_spec(s) for s in SPECS}
    rows: list[dict] = []

    for s in statuses:
        if s["outcome"] != "ok":
            continue
        spec_path = next(p for p in SPECS if _spec_key(p) == s["spec"])
        spec = spec_cache[spec_path]
        raw_dir = REPO / "data" / "raw" / s["run_id"] / s["condition"]
        codebase = json.loads((raw_dir / "codebase.json").read_text())
        log = json.loads((raw_dir / "interaction_log.json").read_text())
        for mod in ANALYZERS:
            score = mod.analyze(codebase, log, spec)
            rows.append({
                "run_label": run_label,
                "run_id": s["run_id"],
                "condition": s["condition"],
                "spec_name": spec["name"],
                "spec_version": spec["version"],
                "rep": s["rep"],
                "metric": score.name,
                "value": round(score.value, 6),
                "unit": score.unit,
                "duration_s": s.get("duration_s"),
                "timestamp": ts,
            })

    out = REPO / "data" / "reports" / f"{run_label}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "run_label", "run_id", "condition", "spec_name", "spec_version",
            "rep", "metric", "value", "unit", "duration_s", "timestamp",
        ])
        w.writeheader()
        w.writerows(rows)

    prov = REPO / "data" / "reports" / f"{run_label}.provenance.json"
    prov.write_text(json.dumps({
        "kind": "main_study",
        "spec_files": SPECS,
        "conditions": sorted({s["condition"] for s in statuses}),
        "reps_per_cell": max((s["rep"] for s in statuses), default=-1) + 1,
        "successful_runs": sum(1 for s in statuses if s["outcome"] == "ok"),
        "failed_runs": sum(1 for s in statuses if s["outcome"] != "ok"),
        "statuses": statuses,
        "timestamp": ts,
    }, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Full pre-registered experiment runner.")
    ap.add_argument("--reps", type=int, default=10,
                    help="Repetitions per (condition × spec). Default 10.")
    ap.add_argument("--run-label", default="main_study_run_001",
                    help="Label for the whole batch. Output: data/reports/<label>.csv")
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for run-order shuffle (recorded in provenance).")
    args = ap.parse_args()

    all_conditions = ["claude_code", "cursor_agent", "replit_agent", "antigravity"]
    enabled = [c for c in all_conditions
               if not os.environ.get(f"AUDITOR_SKIP_{c.split('_')[0].upper()}")]
    if not enabled:
        print("No conditions enabled. Aborting.")
        return 1

    triples = [(c, s, r) for c in enabled for s in SPECS for r in range(args.reps)]
    rng = random.Random(args.seed)
    rng.shuffle(triples)

    print(f"[run] {len(triples)} runs scheduled "
          f"({len(enabled)} conditions × {len(SPECS)} specs × {args.reps} reps)")

    statuses: list[dict] = []
    for i, (cond, spec, rep) in enumerate(triples, 1):
        print(f"\n[{i:3d}/{len(triples)}] {cond} · {_spec_key(spec)} · rep{rep:02d}")
        statuses.append(_run_one(cond, spec, rep, args.run_label))

    print("\n=== Run summary ===")
    by_outcome: dict[str, int] = {}
    for s in statuses:
        by_outcome[s["outcome"]] = by_outcome.get(s["outcome"], 0) + 1
    for k, v in by_outcome.items():
        print(f"  {k:18s} {v}")

    csv_path = _score_all(args.run_label, statuses)
    print(f"\n[done] CSV: {csv_path}")
    print(f"        Dashboard: https://auditor-dashboard-rume.fly.dev/report/{args.run_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
