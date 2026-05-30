"""Example keystroke recorder using `pynput`.

This mirrors `auditor.adapters.human_control_recorder.record` but is a
standalone script you can run to capture events to `data/raw/<run_id>/human_control/interaction_log.json`.

It captures printable keystrokes and records `backspace` / `delete` as distinct
events. It preserves order and writes a JSON array. Use Ctrl+C to stop.
"""
from pathlib import Path
import json
import signal
import sys
from datetime import datetime

try:
    from pynput import keyboard
except ImportError:
    print("pynput not installed. Run: pip install pynput")
    raise

RUN_ID = datetime.utcnow().strftime("pilot_%Y%m%dT%H%M%SZ")
OUT = Path("data/raw") / RUN_ID / "human_control" / "interaction_log.json"

_events = []


def _classify(key):
    if key == keyboard.Key.backspace:
        return "backspace"
    if key == keyboard.Key.delete:
        return "delete"
    if isinstance(key, keyboard.KeyCode) and key.char is not None:
        return "keystroke"
    if isinstance(key, keyboard.Key):
        return "keystroke"
    return None


def on_press(key):
    kind = _classify(key)
    if kind:
        _events.append({"type": kind, "time": datetime.utcnow().isoformat()})


listener = keyboard.Listener(on_press=on_press)
listener.start()


def _shutdown(sig, frame):
    listener.stop()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(_events, indent=2))
    print(f"Wrote {_events and len(_events) or 0} events to {OUT}")
    sys.exit(0)

signal.signal(signal.SIGINT, _shutdown)
print(f"Recording keystrokes to {OUT} — press Ctrl+C to stop")
listener.join()
