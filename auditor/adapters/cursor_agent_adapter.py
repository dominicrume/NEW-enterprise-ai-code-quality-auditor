"""cursor_agent adapter — vendor: Cursor (agent mode CLI).

Drives ``cursor-agent`` non-interactively against the spec, captures the
streamed agent events, and reads the produced codebase from the work_dir.

Capture contract: see docs/METHODOLOGY.md. Cursor is agentic, so every
captured event maps to ``agent_action`` with vendor detail preserved as
sibling keys (``subtype``, ``tool``).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable

from auditor.adapters.base_adapter import BaseAdapter
from auditor.core.config import settings


_CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
                  ".rb", ".sql", ".yaml", ".yml", ".toml", ".md"}

Runner = Callable[[str, Path], Iterable[dict]]


def _default_runner(prompt: str, work_dir: Path, cli: str = "cursor-agent",
                    timeout: int = 600) -> list[dict]:
    proc = subprocess.run(
        [cli, "-p", prompt, "--output-format", "stream-json"],
        cwd=str(work_dir), capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    events: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _build_prompt(spec: dict) -> str:
    return (
        "Implement the specification below in the current working directory. "
        "Do not introduce features outside the listed set.\n\n"
        f"SPEC:\n{json.dumps(spec, indent=2)}\n"
    )


def _to_contract_events(raw_events: Iterable[dict]) -> list[dict]:
    out: list[dict] = []
    for ev in raw_events:
        out.append({
            "type": "agent_action",
            "subtype": ev.get("type") or ev.get("event"),
            "detail": ev.get("subtype") or ev.get("status"),
            "tool": ev.get("tool") or ev.get("tool_name"),
        })
    return out


def _load_codebase(work_dir: Path) -> dict:
    work_dir = Path(work_dir)
    if not work_dir.is_dir():
        raise FileNotFoundError(f"work_dir not found: {work_dir}")
    files: dict[str, str] = {}
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        if path.suffix not in _CODE_SUFFIXES:
            continue
        files[path.relative_to(work_dir).as_posix()] = path.read_text(encoding="utf-8")
    manifest_path = work_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    return {"files": files, "manifest": manifest}


class CursorAgentAdapter(BaseAdapter):
    name = "cursor_agent"

    def __init__(self, work_dir: str | Path, cli: str = "cursor-agent",
                 run_id: str | None = None, raw_root: str | Path = "data/raw",
                 runner: Runner | None = None, timeout: int = 600):
        self.work_dir = Path(work_dir)
        self.cli = cli
        self.run_id = run_id or settings.run_id
        self.raw_root = Path(raw_root)
        self.timeout = timeout
        self._runner: Runner = runner or (
            lambda prompt, wd: _default_runner(prompt, wd, cli=self.cli, timeout=self.timeout)
        )

    def _persist(self, codebase, interaction_log, raw_events) -> Path:
        dest = self.raw_root / self.run_id / self.name
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "codebase.json").write_text(json.dumps(codebase, indent=2))
        (dest / "interaction_log.json").write_text(json.dumps(interaction_log, indent=2))
        (dest / "raw_stream.json").write_text(json.dumps(raw_events, indent=2))
        code_copy = dest / "code"
        if code_copy.exists():
            shutil.rmtree(code_copy)
        shutil.copytree(self.work_dir, code_copy)
        return dest

    def generate(self, spec: dict) -> tuple[dict, list[dict]]:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        prompt = _build_prompt(spec)
        raw_events = list(self._runner(prompt, self.work_dir))
        interaction_log = _to_contract_events(raw_events)
        codebase = _load_codebase(self.work_dir)
        self._persist(codebase, interaction_log, raw_events)
        return codebase, interaction_log
