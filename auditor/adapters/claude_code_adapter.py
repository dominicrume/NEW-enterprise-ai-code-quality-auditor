"""claude_code adapter — vendor: Anthropic Claude Code (see docs/METHODOLOGY.md).

Drives the Claude Code CLI in non-interactive ("-p") mode against the spec,
captures the streamed agent events, and reads back the final codebase from
the working directory the CLI wrote into.

All vendor-specific glue lives in this file; the engine remains neutral.

Capture contract (docs/METHODOLOGY.md):
  codebase        : {"files": {path: content}, "manifest": [feature_ids]}
  interaction_log : list of events, each with at minimum {"type": str}
                    where type ∈ {keystroke, backspace, delete, agent_action}.

Since Claude Code is an agentic system (no human keystrokes), every captured
event maps to ``agent_action`` with vendor-specific detail preserved in
sibling keys (``subtype``, ``tool``, etc.) for downstream forensics.
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
"""Signature: runner(prompt, work_dir) -> iterable of raw Claude Code events."""


def _default_runner(prompt: str, work_dir: Path, cli: str = "claude",
                    timeout: int = 600) -> list[dict]:
    """Invoke the real Claude Code CLI and parse its streaming JSON output."""
    proc = subprocess.run(
        [cli, "-p", prompt, "--output-format", "stream-json", "--verbose",
         "--dangerously-skip-permissions"],
        cwd=str(work_dir),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
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
    """Render the spec dict into a single prompt string for the agent."""
    return (
        "You are implementing the following specification. Build the code in "
        "the current working directory. Stay strictly within the listed "
        "features — do not invent extras.\n\n"
        f"SPEC:\n{json.dumps(spec, indent=2)}\n"
    )


def _to_contract_events(raw_events: Iterable[dict]) -> list[dict]:
    """Map every raw Claude Code event to a capture-contract event.

    All Claude Code events are agent actions; we preserve the original
    payload's identifying fields (``type``, ``subtype``, ``tool_name``) under
    new keys so analyzers can interrogate detail without leaking the vendor
    schema into the contract.
    """
    out: list[dict] = []
    for ev in raw_events:
        out.append({
            "type": "agent_action",
            "subtype": ev.get("type"),
            "detail": ev.get("subtype"),
            "tool": ev.get("tool_name") or ev.get("name"),
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
        if not path.is_file():
            continue
        if path.name == "manifest.json":
            continue
        if path.suffix not in _CODE_SUFFIXES:
            continue
        rel = path.relative_to(work_dir).as_posix()
        if any(part in _EXCLUDE_DIRS or part.endswith(".egg-info")
               for part in Path(rel).parts):
            continue
        files[rel] = path.read_text(encoding="utf-8")
    manifest_path = work_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    return {"files": files, "manifest": manifest}


class ClaudeCodeAdapter(BaseAdapter):
    name = "claude_code"

    def __init__(self, work_dir: str | Path, cli: str = "claude",
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

    def _persist(self, codebase: dict, interaction_log: list[dict],
                 raw_events: list[dict]) -> Path:
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
