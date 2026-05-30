"""End-to-end experiment: five adapters × five analyzers → one CSV report."""
import csv
import json
import shutil
from pathlib import Path

import pytest

from auditor.analyzers import security_analyzer
from auditor.core.experiment import build_default_adapters, run_experiment

FIXTURES = Path(__file__).parent / "fixtures"
SPEC = FIXTURES / "experiment" / "spec.yaml"

CONDITIONS = ["human_control", "claude_code", "cursor_agent", "antigravity", "replit_agent"]
METRICS = {"security_density", "complexity_mean", "duplication_pct",
           "hallucinations", "correction_freq"}


def _stage_captures(captures_root: Path, run_id: str) -> None:
    """Assemble a captures dir reusing each adapter's existing test fixture."""
    base = captures_root / run_id

    # human_control
    src_hc = FIXTURES / "human_control"
    (base / "human_control").mkdir(parents=True)
    shutil.copytree(src_hc / "code", base / "human_control" / "code")
    shutil.copy(src_hc / "session.json", base / "human_control" / "interaction_log.json")

    # agents — each needs work_dir/code/ + raw_stream.json
    for cond in ["claude_code", "cursor_agent", "antigravity", "replit_agent"]:
        src = FIXTURES / cond
        (base / cond).mkdir(parents=True)
        shutil.copytree(src / "produced_code", base / cond / "code")
        shutil.copy(src / "raw_stream.json", base / cond / "raw_stream.json")


def test_experiment_runs_all_conditions_and_writes_csv(tmp_path, monkeypatch):
    # SonarQube is the only external call — stub it deterministically.
    monkeypatch.setattr(
        security_analyzer, "_fetch_issues",
        lambda key: [{"tags": ["cwe-79"]}, {"tags": ["owasp-a3"]}],
    )

    run_id = "exp_run_001"
    captures = tmp_path / "captures"
    _stage_captures(captures, run_id)

    adapters = build_default_adapters(
        run_id=run_id,
        captures_root=captures,
        raw_root=tmp_path / "raw",
    )
    assert [a.name for a in adapters] == CONDITIONS

    out = run_experiment(
        spec_path=SPEC,
        run_id=run_id,
        adapters=adapters,
        reports_dir=tmp_path / "reports",
    )

    assert out == tmp_path / "reports" / f"{run_id}.csv"
    assert out.is_file()

    with open(out) as f:
        rows = list(csv.DictReader(f))

    # 5 conditions × 5 metrics = 25 rows
    assert len(rows) == 25
    assert {r["condition"] for r in rows} == set(CONDITIONS)
    assert {r["metric"] for r in rows} == METRICS
    assert all(r["run_id"] == run_id for r in rows)
    assert all(r["spec_name"] == "experiment_test_spec" for r in rows)

    # Every condition produced one of each metric.
    for cond in CONDITIONS:
        cond_metrics = {r["metric"] for r in rows if r["condition"] == cond}
        assert cond_metrics == METRICS

    # Persistence side-effect from adapters: raw artefacts written.
    raw_root = tmp_path / "raw" / run_id
    for cond in CONDITIONS:
        assert (raw_root / cond / "codebase.json").is_file()
        assert (raw_root / cond / "interaction_log.json").is_file()


def test_experiment_refuses_to_overwrite_existing_report(tmp_path, monkeypatch):
    monkeypatch.setattr(security_analyzer, "_fetch_issues", lambda key: [])
    run_id = "exp_run_002"
    captures = tmp_path / "captures"
    _stage_captures(captures, run_id)
    adapters = build_default_adapters(run_id, captures, raw_root=tmp_path / "raw")
    reports = tmp_path / "reports"

    run_experiment(SPEC, run_id, adapters, reports_dir=reports)

    # Second run must refuse — reports are immutable.
    adapters2 = build_default_adapters(run_id, captures, raw_root=tmp_path / "raw2")
    with pytest.raises(FileExistsError):
        run_experiment(SPEC, run_id, adapters2, reports_dir=reports)
