"""Drive the claude_code condition end-to-end for one run.

Usage:
    python scripts/run_claude_code_session.py <run_id>

What it does:
    1. Loads specs/agent_education_system.yaml + governance_guardrails.yaml.
    2. Creates a clean work_dir at ~/sessions/<run_id>_claude/code/.
    3. Invokes the real `claude` CLI via ClaudeCodeAdapter against the spec.
    4. Persists codebase + agent-action log to data/raw/<run_id>/claude_code/.

Prereqs:
    - `claude` CLI on PATH (verified: 2.1.139).
    - Authenticated (run `claude` once interactively, or set ANTHROPIC_API_KEY).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from auditor.adapters.claude_code_adapter import ClaudeCodeAdapter

REPO = Path(__file__).resolve().parent.parent
SPECS = REPO / "specs"


def load_spec() -> dict:
    spec = yaml.safe_load((SPECS / "agent_education_system.yaml").read_text())
    guardrails = yaml.safe_load((SPECS / "governance_guardrails.yaml").read_text())
    spec["guardrails"] = guardrails.get("guardrails", [])
    return spec


def main(argv: list[str]) -> int:
    run_id = argv[1] if len(argv) > 1 else "run_001"
    work_dir = Path.home() / "sessions" / f"{run_id}_claude" / "code"
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"[claude_code] run_id   = {run_id}")
    print(f"[claude_code] work_dir = {work_dir}")
    print(f"[claude_code] invoking claude CLI (this may take several minutes)...")

    adapter = ClaudeCodeAdapter(work_dir=work_dir, run_id=run_id)
    codebase, log = adapter.generate(load_spec())

    print(f"[claude_code] done. {len(codebase['files'])} files, {len(log)} events.")
    print(f"[claude_code] snapshot at data/raw/{run_id}/claude_code/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
