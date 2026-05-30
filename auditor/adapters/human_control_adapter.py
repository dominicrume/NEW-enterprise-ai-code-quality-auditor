"""Human control: the baseline condition.

Captures a real local development session performed by a human with no AI
assistance. Two artefacts are produced:

* a **codebase** — read from a directory the developer points at after they
  finish writing code by hand;
* an **interaction log** — produced by `human_control_recorder.py`, which
  records keystrokes via `pynput` during the session.

Both artefacts are persisted to ``data/raw/<run_id>/human_control/`` so the
analyzer stage has reproducible inputs.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from auditor.adapters.base_adapter import BaseAdapter
from auditor.core.config import settings


# File extensions considered source code for the baseline.
_CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
                  ".rb", ".sql", ".yaml", ".yml", ".toml", ".md"}


def load_codebase(code_dir: Path) -> dict:
    """Read every source file under ``code_dir`` into the capture-contract shape.

    The manifest is intentionally derived from a ``manifest.json`` file at the
    root of ``code_dir`` if present, otherwise the empty list — the human
    decides what features they actually shipped, not the loader.
    """
    code_dir = Path(code_dir)
    if not code_dir.is_dir():
        raise FileNotFoundError(f"codebase directory not found: {code_dir}")

    files: dict[str, str] = {}
    for path in sorted(code_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "manifest.json":
            continue
        if path.suffix not in _CODE_SUFFIXES:
            continue
        rel = path.relative_to(code_dir).as_posix()
        files[rel] = path.read_text(encoding="utf-8")

    manifest_path = code_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    return {"files": files, "manifest": manifest}


def load_interaction_log(log_path: Path) -> list[dict]:
    """Load a recorded session JSON file. Validates the capture contract."""
    log_path = Path(log_path)
    if not log_path.is_file():
        raise FileNotFoundError(f"interaction log not found: {log_path}")
    events = json.loads(log_path.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise ValueError("interaction log must be a JSON list of events")
    permitted = {"keystroke", "backspace", "delete", "agent_action"}
    for ev in events:
        if not isinstance(ev, dict) or "type" not in ev:
            raise ValueError(f"malformed event: {ev!r}")
        if ev["type"] not in permitted:
            raise ValueError(f"unsupported event type: {ev['type']!r}")
    return events


class HumanControlAdapter(BaseAdapter):
    """Baseline adapter — does not generate code, it *loads* what a human wrote."""

    name = "human_control"

    def __init__(self, code_dir: str | Path, log_path: str | Path,
                 run_id: str | None = None, raw_root: str | Path = "data/raw"):
        self.code_dir = Path(code_dir)
        self.log_path = Path(log_path)
        self.run_id = run_id or settings.run_id
        self.raw_root = Path(raw_root)

    def _persist(self, codebase: dict, interaction_log: list[dict]) -> Path:
        dest = self.raw_root / self.run_id / self.name
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "codebase.json").write_text(json.dumps(codebase, indent=2))
        (dest / "interaction_log.json").write_text(json.dumps(interaction_log, indent=2))
        # Preserve the original source tree alongside the JSON snapshot.
        code_copy = dest / "code"
        if code_copy.exists():
            shutil.rmtree(code_copy)
        shutil.copytree(self.code_dir, code_copy)
        return dest

    def generate(self, spec: dict) -> tuple[dict, list[dict]]:
        codebase = load_codebase(self.code_dir)
        interaction_log = load_interaction_log(self.log_path)
        self._persist(codebase, interaction_log)
        return codebase, interaction_log
