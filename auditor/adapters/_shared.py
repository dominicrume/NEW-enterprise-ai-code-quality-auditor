"""Shared helpers for vendor adapters.

Every adapter loader was originally a verbatim copy of the same walk-and-filter.
That duplication (~80 LOC × 4 files) is the bulk of the auditor's SonarCloud
duplication score. Consolidating here drops it sharply without changing
behaviour.

Exports:
  CODE_SUFFIXES   — file extensions the codebase loader ingests
  EXCLUDE_DIRS    — directory names ignored by the codebase loader
  load_codebase() — walk-and-filter helper used by every vendor adapter
"""
from __future__ import annotations

import json
from pathlib import Path

CODE_SUFFIXES: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs",
    ".java", ".rb", ".sql", ".yaml", ".yml", ".toml", ".md",
})

EXCLUDE_DIRS: frozenset[str] = frozenset({
    ".venv", "venv", "env", "__pycache__", "node_modules",
    ".pytest_cache", ".git", "site-packages", "dist", "build",
    ".mypy_cache", ".ruff_cache", "egg-info",
})


def _excluded(rel_parts: tuple[str, ...]) -> bool:
    return any(part in EXCLUDE_DIRS or part.endswith(".egg-info")
               for part in rel_parts)


def iter_source_files(work_dir: Path):
    """Yield ``(relative_posix_path, absolute_path)`` for every scorable file.

    The single definition of "a file this instrument looks at". The codebase
    loader and the watcher both consume it, so a file can never be measured
    but not watched, or the reverse.
    """
    work_dir = Path(work_dir)
    for path in sorted(work_dir.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        if path.suffix not in CODE_SUFFIXES:
            continue
        rel = path.relative_to(work_dir)
        if _excluded(rel.parts):
            continue
        yield rel.as_posix(), path


def load_codebase(work_dir: Path) -> dict:
    """Walk ``work_dir``, return the capture-contract codebase dict.

    Skips the EXCLUDE_DIRS set so transitive deps (.venv, node_modules,
    site-packages, etc.) don't inflate any downstream metric.
    """
    work_dir = Path(work_dir)
    if not work_dir.is_dir():
        raise FileNotFoundError(f"work_dir not found: {work_dir}")

    files: dict[str, str] = {}
    for rel, path in iter_source_files(work_dir):
        try:
            files[rel] = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or vanished mid-walk — skip, never crash a scan

    manifest_path = work_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    return {"files": files, "manifest": manifest}
