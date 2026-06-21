"""One-command human_control capture session.

Usage:
    PYTHONPATH=. python scripts/run_human_session.py --spec internal_tool_cli

What it does:
    1. Creates a workspace at data/raw/main_001__<spec>__human_control__rep00/
       human_control/ with a `code/` subdir for you to write into.
    2. Starts a global keystroke recorder (event types only — no payloads).
    3. Prints a banner telling you to code; Ctrl+C the recorder when done.
    4. After Ctrl+C, materialises the interaction log + codebase capture
       through the HumanControlAdapter so artefacts match the contract
       expected by the analyzer pipeline.
    5. Prints next-step commands to score the session through the same
       pipeline that produced the main_001 results.
"""
from __future__ import annotations

import argparse
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True,
                        help="Spec name without .yaml — e.g. internal_tool_cli")
    parser.add_argument("--run-label", default="main_001",
                        help="Run label (default matches the main study).")
    parser.add_argument("--rep", default="00",
                        help="Replicate index (default 00).")
    args = parser.parse_args()

    spec_path = ROOT / "specs" / f"{args.spec}.yaml"
    if not spec_path.is_file():
        print(f"[!] spec not found: {spec_path}", file=sys.stderr)
        return 1

    cond = "human_control"
    session_root = ROOT / "data" / "raw" / f"{args.run_label}__{args.spec}__{cond}__rep{args.rep}" / cond
    code_dir = session_root / "code"
    log_path = session_root / "interaction_log.json"
    code_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"  Human-control session")
    print(f"  spec       : {args.spec}")
    print(f"  rep        : {args.rep}")
    print(f"  workspace  : {code_dir}")
    print(f"  log output : {log_path}")
    print("=" * 70)
    print()
    print("  1. Read the spec — open it now in another window:")
    print(f"     code {spec_path.relative_to(ROOT)}")
    print()
    print(f"  2. Write your implementation INSIDE: {code_dir.relative_to(ROOT)}")
    print(f"     Use any filenames you want. Add a manifest.json at the")
    print(f"     root of that folder listing the feature ids you finished,")
    print(f"     e.g. [\"cli.init\",\"cli.add\",\"cli.list\"].")
    print()
    print("  3. macOS only: System Settings → Privacy & Security →")
    print("     Accessibility — toggle Terminal (or your shell app) ON")
    print("     so the recorder can see your keystrokes.")
    print()
    print("  4. When you're done coding, come back here and press Ctrl+C")
    print("     ONCE to stop the recorder. The artefacts will be saved.")
    print()
    input("  Press Enter to start the recorder ... ")
    print()
    print("  [recorder] running — type away in your editor")
    print()

    rec_cmd = [
        sys.executable, "-m", "auditor.adapters.human_control_recorder",
        "--record", "--out", str(log_path),
    ]
    proc = subprocess.Popen(rec_cmd, cwd=str(ROOT), env={"PYTHONPATH": str(ROOT), **__import__("os").environ})

    try:
        proc.wait()
    except KeyboardInterrupt:
        # Forward the interrupt; the recorder's own SIGINT handler will
        # stop the listener and flush events to disk.
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=5)
        except Exception:
            proc.terminate()

    if not log_path.is_file():
        print(f"\n[!] no interaction log written at {log_path}", file=sys.stderr)
        print("    Most common cause on macOS: Accessibility permission denied.", file=sys.stderr)
        return 2

    n_events = 0
    try:
        import json
        n_events = len(json.loads(log_path.read_text()))
    except Exception:
        pass

    files_written = sum(1 for _ in code_dir.rglob("*") if _.is_file())
    print()
    print("=" * 70)
    print(f"  Session captured.")
    print(f"    files written : {files_written}")
    print(f"    keystrokes etc: {n_events} events")
    print(f"    log           : {log_path}")
    print(f"    workspace     : {code_dir}")
    print("=" * 70)

    if files_written == 0:
        print()
        print("  ⚠️  No files in the workspace yet — did you remember to save")
        print(f"     your code into {code_dir.relative_to(ROOT)} ?")
        print("     You can still add files now and re-run the scoring step.")

    print()
    print("Next — score the session through the pipeline:")
    print()
    print("  PYTHONPATH=. python scripts/score_human_session.py \\")
    print(f"    --spec {args.spec} --run-label {args.run_label} --rep {args.rep}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
