"""CLI smoke tests using click's CliRunner against staged captures."""
import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from auditor.analyzers import security_analyzer
from auditor.core.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
SPEC = FIXTURES / "experiment" / "spec.yaml"


def _stage(captures_root: Path, run_id: str) -> None:
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


def test_run_command_audits_one_condition(tmp_path, monkeypatch):
    from auditor.models.audit_result import MetricScore
    monkeypatch.setattr(security_analyzer, "analyze",
                        lambda c,l,sp: MetricScore(name="security_density", value=0.0, unit="per_kloc"))
    captures = tmp_path / "captures"
    _stage(captures, "cli_run_001")
    monkeypatch.chdir(tmp_path)  # raw_root="data/raw" default → tmp

    result = CliRunner().invoke(main, [
        "run", "--spec", str(SPEC), "--workflow", "human_control",
        "--run-id", "cli_run_001", "--captures-root", str(captures),
    ])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["condition"] == "human_control"
    assert {m["name"] for m in payload["metrics"]} == {
        "security_density", "complexity_mean", "duplication_pct",
        "hallucinations", "correction_freq",
    }


def test_experiment_command_writes_csv(tmp_path, monkeypatch):
    from auditor.models.audit_result import MetricScore
    monkeypatch.setattr(security_analyzer, "analyze",
                        lambda c,l,sp: MetricScore(name="security_density", value=0.0, unit="per_kloc"))
    captures = tmp_path / "captures"
    _stage(captures, "cli_exp_001")
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "out"

    result = CliRunner().invoke(main, [
        "experiment", "--spec", str(SPEC), "--run-id", "cli_exp_001",
        "--captures-root", str(captures), "--reports-dir", str(reports),
    ])
    assert result.exit_code == 0, result.output
    assert (reports / "cli_exp_001.csv").is_file()
