"""Keystroke capture for the human-control baseline.

Behind a ``--record`` flag this opens a global keyboard listener via
``pynput``, classifies each press as ``keystroke``, ``backspace`` or
``delete``, and writes a JSON interaction log conforming to the adapter's
capture contract.

`pynput` is an optional dependency — the import is deferred so the rest of
the auditor remains usable on machines without it (e.g. CI).

Usage:
    python -m auditor.adapters.human_control_recorder --record \\
        --out data/raw/<run_id>/human_control/interaction_log.json
"""
from __future__ import annotations

import argparse
import json
import signal
import sys
from pathlib import Path

from auditor.core.config import settings


def _classify(key) -> str | None:
    """Map a pynput key to a capture-contract event type."""
    from pynput import keyboard  # local import — optional dep

    if key == keyboard.Key.backspace:
        return "backspace"
    if key == keyboard.Key.delete:
        return "delete"
    # Treat printable chars and ordinary modifier-less keys as keystrokes.
    if isinstance(key, keyboard.KeyCode) and key.char is not None:
        return "keystroke"
    if isinstance(key, keyboard.Key):
        # Modifier / navigation keys: count as a keystroke (a typed action).
        return "keystroke"
    return None


def record(out_path: Path) -> Path:
    """Block until SIGINT, writing events to ``out_path`` on exit."""
    try:
        from pynput import keyboard
    except ImportError as e:  # pragma: no cover - environment-specific
        raise SystemExit(
            "pynput is required for --record. Install with `pip install pynput`."
        ) from e

    events: list[dict] = []

    def on_press(key):
        kind = _classify(key)
        if kind is not None:
            events.append({"type": kind})

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    def _shutdown(*_):  # pragma: no cover - signal path
        listener.stop()

    signal.signal(signal.SIGINT, _shutdown)
    print(f"[recorder] capturing keystrokes — press Ctrl+C to stop. Output: {out_path}")
    listener.join()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(events, indent=2))
    print(f"[recorder] wrote {len(events)} events to {out_path}")
    return out_path


def _default_out() -> Path:
    return Path("data/raw") / settings.run_id / "human_control" / "interaction_log.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Human-control keystroke recorder")
    parser.add_argument("--record", action="store_true",
                        help="start capturing keystrokes (Ctrl+C to stop)")
    parser.add_argument("--out", type=Path, default=None,
                        help="output JSON path (default: data/raw/<run_id>/human_control/interaction_log.json)")
    args = parser.parse_args(argv)

    if not args.record:
        parser.print_help()
        return 1

    record(args.out or _default_out())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
