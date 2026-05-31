"""Thin wrapper around auditor.core.study.run_study.

Kept for users who prefer the script form. The CLI equivalent is:

    auditor experiment --reps 10 --run-label main_001

Both ship the same engine (auditor.core.study).

Usage:
    PYTHONPATH=. python scripts/run_full_experiment.py \\
        --reps 10 --run-label main_study_run_001

Environment skips:
    AUDITOR_SKIP_CLAUDE=1 / SKIP_CURSOR / SKIP_REPLIT / SKIP_ANTIGRAV
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from auditor.core.study import AGENT_CONDITIONS, run_study


_ENV_TO_COND = {
    "AUDITOR_SKIP_CLAUDE":  "claude_code",
    "AUDITOR_SKIP_CURSOR":  "cursor_agent",
    "AUDITOR_SKIP_REPLIT":  "replit_agent",
    "AUDITOR_SKIP_ANTIGRAV": "antigravity",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Full pre-registered experiment runner.")
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--run-label", default="main_study_run_001")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    skip = tuple(cond for env, cond in _ENV_TO_COND.items() if os.environ.get(env))
    out = run_study(reps=args.reps, run_label=args.run_label,
                    seed=args.seed, skip=skip, repo_root=REPO)
    print(f"[done] CSV: {out}")
    print(f"        Dashboard: https://auditor-dashboard-rume.fly.dev/report/{args.run_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
