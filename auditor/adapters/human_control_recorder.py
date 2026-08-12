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
import threading
import time
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


def _segment_paths(out_path: Path) -> list[Path]:
    """Every captured segment for this run, in capture order."""
    seg_dir = out_path.parent / "segments"
    return sorted(seg_dir.glob("segment_*.json")) if seg_dir.exists() else []


def _rebuild_combined(out_path: Path) -> int:
    """Concatenate all segments into the canonical interaction log.

    The scorer reads ``interaction_log.json``; per PROTOCOL_DEVIATIONS.md
    (Deviation 003) the human log is the concatenation of every capture
    segment, so total typing effort survives stopping and restarting.
    """
    combined: list[dict] = []
    for seg in _segment_paths(out_path):
        try:
            combined.extend(json.loads(seg.read_text()))
        except json.JSONDecodeError:
            print(f"[recorder] WARNING: skipping unreadable segment {seg.name}")
    out_path.write_text(json.dumps(combined, indent=2))
    return len(combined)


def record(out_path: Path, flush_every: float = 5.0) -> Path:
    """Capture keystrokes until SIGINT.

    Writes to a fresh timestamped *segment* file, autosaving every
    ``flush_every`` seconds, then rebuilds the combined interaction log from
    all segments. Restarting the recorder therefore adds to the session
    rather than destroying it, and a crash costs at most a few seconds.
    """
    try:
        from pynput import keyboard
    except ImportError as e:  # pragma: no cover - environment-specific
        raise SystemExit(
            "pynput is required for --record. Install with `pip install pynput`."
        ) from e

    out_path = Path(out_path)
    seg_dir = out_path.parent / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    seg_path = seg_dir / f"segment_{stamp}.json"

    prior = sum(len(json.loads(p.read_text() or "[]")) for p in _segment_paths(out_path))
    events: list[dict] = []
    stopping = threading.Event()

    def on_press(key):
        kind = _classify(key)
        if kind is not None:
            events.append({"type": kind})

    def save() -> int:
        snapshot = list(events)  # append is atomic; slice gives a stable view
        seg_path.write_text(json.dumps(snapshot, indent=2))
        return len(snapshot)

    def autosave():  # pragma: no cover - timing thread
        while not stopping.wait(flush_every):
            save()

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    saver = threading.Thread(target=autosave, daemon=True)
    saver.start()

    def _shutdown(*_):  # pragma: no cover - signal path
        listener.stop()

    signal.signal(signal.SIGINT, _shutdown)
    print(f"[recorder] capturing keystrokes — press Ctrl+C to stop.")
    print(f"[recorder] segment   : {seg_path}")
    print(f"[recorder] autosaving every {flush_every:g}s"
          + (f"; {prior} events already captured in earlier segments" if prior else ""))
    if sys.platform == "darwin":
        print("[recorder] macOS: if the event count stays at 0, grant your terminal "
              "Accessibility permission (System Settings › Privacy & Security › "
              "Accessibility) and restart this recorder.")
    listener.join()

    stopping.set()
    captured = save()
    total = _rebuild_combined(out_path)
    print(f"[recorder] wrote {captured} events to {seg_path.name}")
    print(f"[recorder] combined {total} events across "
          f"{len(_segment_paths(out_path))} segment(s) -> {out_path}")
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
