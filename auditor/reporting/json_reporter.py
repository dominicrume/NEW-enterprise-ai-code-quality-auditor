"""Write AuditResult as JSON (one file per run+condition)."""
from pathlib import Path

from auditor.models.audit_result import AuditResult


def write(result: AuditResult, path: str | Path) -> None:
    Path(path).write_text(result.model_dump_json(indent=2), encoding="utf-8")
