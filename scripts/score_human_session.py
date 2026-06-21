"""Score a captured human_control session through the analyzer pipeline.

Run after `scripts/run_human_session.py` finishes:

    PYTHONPATH=. python scripts/score_human_session.py \\
        --spec internal_tool_cli --run-label main_001 --rep 00

Output: prints the per-metric scores AND appends a row to a session-local
CSV at data/reports/human_session_<spec>_rep<NN>.csv so the result is
permanently captured next to the main study artefacts.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from auditor.adapters.human_control_adapter import HumanControlAdapter  # noqa: E402
from auditor.analyzers import (  # noqa: E402
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
    security_analyzer,
)


ANALYZERS = [
    security_analyzer, complexity_analyzer, duplication_analyzer,
    hallucination_analyzer, keystroke_analyzer,
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--run-label", default="main_001")
    parser.add_argument("--rep", default="00")
    args = parser.parse_args()

    spec_path = ROOT / "specs" / f"{args.spec}.yaml"
    if not spec_path.is_file():
        print(f"[!] spec not found: {spec_path}", file=sys.stderr)
        return 1
    spec = yaml.safe_load(spec_path.read_text())

    session_root = ROOT / "data" / "raw" / f"{args.run_label}__{args.spec}__human_control__rep{args.rep}" / "human_control"
    code_dir = session_root / "code"
    log_path = session_root / "interaction_log.json"
    if not code_dir.is_dir() or not log_path.is_file():
        print(f"[!] missing session artefacts. Expected:", file=sys.stderr)
        print(f"      code dir : {code_dir}", file=sys.stderr)
        print(f"      log file : {log_path}", file=sys.stderr)
        return 2

    adapter = HumanControlAdapter(
        code_dir=code_dir, log_path=log_path,
        run_id=f"{args.run_label}__{args.spec}__rep{args.rep}",
        raw_root=ROOT / "data" / "raw" / "_human_session_persist",
    )
    codebase, interaction_log = adapter.generate(spec)

    print()
    print("=" * 70)
    print(f"  Human-control results — spec={args.spec} rep={args.rep}")
    print("=" * 70)
    scores = []
    for mod in ANALYZERS:
        score = mod.analyze(codebase, interaction_log, spec)
        scores.append(score)
        unit = f" {score.unit}" if score.unit else ""
        print(f"    {score.name:<18} {score.value:>10.3f}{unit}")
    print("=" * 70)

    reports_dir = ROOT / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"human_session_{args.spec}_rep{args.rep}.csv"
    new_file = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["run_label", "spec_name", "spec_version", "condition",
                        "rep", "metric", "value", "unit", "timestamp"])
        ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
        for s in scores:
            w.writerow([args.run_label, spec.get("name", args.spec),
                        str(spec.get("version", "0")), "human_control",
                        args.rep, s.name, s.value, s.unit, ts])
    print(f"  CSV row appended: {out.relative_to(ROOT)}")
    print()
    print("To compare your baseline against the AI agents in main_001:")
    print(f"    open data/reports/{out.name}")
    print(f"    open data/reports/main_001.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
