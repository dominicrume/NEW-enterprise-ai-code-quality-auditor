"""Small helper: use HumanControlAdapter to persist a human-captured folder + log.

Usage:
    python scripts/persist_human_run.py --code samples/human_code --log path/to/interaction_log.json
"""
from pathlib import Path
import argparse
from auditor.adapters.human_control_adapter import HumanControlAdapter

parser = argparse.ArgumentParser()
parser.add_argument("--code", type=Path, required=True)
parser.add_argument("--log", type=Path, required=True)
parser.add_argument("--run-id", type=str, default=None)

if __name__ == "__main__":
    args = parser.parse_args()
    adapter = HumanControlAdapter(args.code, args.log, run_id=args.run_id)
    codebase, log = adapter.generate({})
    print(f"persisted human run: {len(codebase['files'])} files, {len(log)} events")
