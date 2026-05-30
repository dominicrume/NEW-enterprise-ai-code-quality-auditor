"""Produce a clearly-labelled pilot CSV using test fixtures as stand-in captures.

This is NOT the dissertation experiment. The CSV produced here exercises
the full pipeline (5 adapters x 5 analyzers -> 1 CSV) but the inputs are
synthetic fixtures, not real vendor sessions. The provenance JSON written
alongside the CSV makes this explicit.

Usage:
    PYTHONPATH=. python scripts/run_pilot.py
"""
from __future__ import annotations

import datetime as _dt
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Allow `python scripts/run_pilot.py` without PYTHONPATH set.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from auditor.analyzers import security_analyzer  # noqa: E402
from auditor.core.experiment import build_default_adapters, run_experiment  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SPEC = ROOT / "specs" / "agent_education_system.yaml"
REPORTS_DIR = ROOT / "data" / "reports"


def stage_captures(captures_root: Path, run_id: str) -> None:
    base = captures_root / run_id
    src_hc = FIXTURES / "human_control"
    (base / "human_control").mkdir(parents=True)
    shutil.copytree(src_hc / "code", base / "human_control" / "code")
    shutil.copy(src_hc / "session.json", base / "human_control" / "interaction_log.json")
    for cond in ["claude_code", "cursor_agent", "antigravity", "replit_agent"]:
        src = FIXTURES / cond
        (base / cond).mkdir(parents=True)
        shutil.copytree(src / "produced_code", base / cond / "code")
        shutil.copy(src / "raw_stream.json", base / cond / "raw_stream.json")


def main() -> Path:
    timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"pilot_{timestamp}"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        stage_captures(tmp_path / "captures", run_id)
        adapters = build_default_adapters(
            run_id=run_id,
            captures_root=tmp_path / "captures",
            raw_root=tmp_path / "raw",
        )
        # Stub SonarQube — pilot has no real project key.
        with patch.object(security_analyzer, "_fetch_issues", lambda key: []):
            csv_path = run_experiment(SPEC, run_id, adapters, reports_dir=REPORTS_DIR)

    provenance = {
        "run_id": run_id,
        "kind": "pilot",
        "is_dissertation_result": False,
        "warning": (
            "This CSV exercises the pipeline using synthetic test fixtures as "
            "stand-in captures. It is NOT the experimental result of any "
            "real vendor session. Do not cite as dissertation data."
        ),
        "spec": str(SPEC.relative_to(ROOT)),
        "sonarqube": "stubbed (returned no issues)",
        "captures_source": "tests/fixtures/",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "csv": csv_path.name,
    }
    prov_path = REPORTS_DIR / f"{run_id}.provenance.json"
    prov_path.write_text(json.dumps(provenance, indent=2))

    print(f"wrote {csv_path}")
    print(f"wrote {prov_path}")
    return csv_path


if __name__ == "__main__":
    main()
