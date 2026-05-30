"""Write AuditResult rows to CSV (one row per metric)."""
import csv
from pathlib import Path

from auditor.models.audit_result import AuditResult


def write(result: AuditResult, path: str | Path) -> None:
    path = Path(path)
    new_file = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(
                ["run_id", "condition", "spec_name", "metric", "value", "unit", "timestamp"]
            )
        for m in result.metrics:
            writer.writerow(
                [result.run_id, result.condition, result.spec_name,
                 m.name, m.value, m.unit, result.timestamp.isoformat()]
            )
