"""replit_agent adapter — vendor: Replit autonomous agent.

Drives Replit's agent CLI (or HTTP shim) against the spec, captures its
streamed agent events, and reads the produced codebase from the work_dir.

Capture contract: see docs/METHODOLOGY.md. Replit Agent is fully agentic, so
every captured event maps to ``agent_action``.
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


def _default_runner(prompt: str, work_dir: Path, cli: str = "replit",
                    timeout: int = 900) -> list[dict]:
    proc = subprocess.run(
        [cli, "agent", "run", "--prompt", prompt, "--stream", "json"],
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
        "Implement the specification below as a Replit project. Stay within "
        "the listed features only.\n\n"
        f"SPEC:\n{json.dumps(spec, indent=2)}\n"
    )


def _to_contract_events(raw_events: Iterable[dict]) -> list[dict]:
    out: list[dict] = []
    for ev in raw_events:
        out.append({
            "type": "agent_action",
            "subtype": ev.get("event") or ev.get("type"),
            "detail": ev.get("status") or ev.get("stage"),
            "tool": ev.get("tool") or ev.get("action"),
        })
    return out


def _load_codebase(work_dir: Path) -> dict:
    work_dir = Path(work_dir)
    if not work_dir.is_dir():
        raise FileNotFoundError(f"work_dir not found: {work_dir}")
    _EXCLUDE_DIRS = {".venv", "venv", "env", "__pycache__", "node_modules",
                     ".pytest_cache", ".git", "site-packages", "dist", "build",
                     ".mypy_cache", ".ruff_cache", "egg-info"}
    files: dict[str, str] = {}
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        if path.suffix not in _CODE_SUFFIXES:
            continue
        if any(part in _EXCLUDE_DIRS or part.endswith(".egg-info")
               for part in path.relative_to(work_dir).parts):
            continue
        files[path.relative_to(work_dir).as_posix()] = path.read_text(encoding="utf-8")
    manifest_path = work_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    return {"files": files, "manifest": manifest}


class ReplitAgentAdapter(BaseAdapter):
    name = "replit_agent"

    def __init__(self, work_dir: str | Path, cli: str = "replit",
                 run_id: str | None = None, raw_root: str | Path = "data/raw",
                 runner: Runner | None = None, timeout: int = 900,
                 replay_dir: str | Path | None = None):
        """
        replay_dir: if given, skip the CLI and load codebase from this folder
        plus an interaction log from ``<replay_dir>/log.json``. Lets you capture
        Replit Agent sessions manually in the Replit web IDE, download the
        artefacts, and score them through the same pipeline.
        """
        self.work_dir = Path(work_dir)
        self.cli = cli
        self.run_id = run_id or settings.run_id
        self.raw_root = Path(raw_root)
        self.timeout = timeout
        self.replay_dir = Path(replay_dir) if replay_dir else None
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
        if self.replay_dir is not None:
            codebase = _load_codebase(self.replay_dir)
            log_path = self.replay_dir / "log.json"
            interaction_log = (
                json.loads(log_path.read_text()) if log_path.exists() else []
            )
            self._persist(codebase, interaction_log, raw_events=[])
            return codebase, interaction_log
        self.work_dir.mkdir(parents=True, exist_ok=True)
        prompt = _build_prompt(spec)
        raw_events = list(self._runner(prompt, self.work_dir))
        interaction_log = _to_contract_events(raw_events)
        codebase = _load_codebase(self.work_dir)
        self._persist(codebase, interaction_log, raw_events)
        return codebase, interaction_log
