"""Command-line entry.

  auditor run        --spec X --workflow Y --run-id R   [--captures-root]
  auditor experiment --spec X --run-id Y                [--captures-root --reports-dir]

`run` audits a single condition; `experiment` audits all five and emits the
combined CSV report. Both commands rely on a captures directory laid out as
``<captures-root>/<run-id>/<condition>/`` — produced by capture-time invocations
of the adapters (see human_control_recorder.py and the per-vendor capture
flow in docs/METHODOLOGY.md).
"""
from pathlib import Path

import click

from auditor.core.experiment import build_default_adapters, run_experiment
from auditor.core.runner import run_audit

CONDITIONS = ["human_control", "claude_code", "cursor_agent", "antigravity", "replit_agent"]


@click.group()
def main():
    """AI Code Quality Auditor."""


@main.command("run")
@click.option("--spec", required=True, help="Path to spec YAML.")
@click.option("--workflow", required=True, type=click.Choice(CONDITIONS))
@click.option("--run-id", required=True, help="Run identifier (locates the captures dir).")
@click.option("--captures-root", default="data/raw", show_default=True,
              help="Root holding <run-id>/<workflow>/ captured artefacts.")
def run_cmd(spec: str, workflow: str, run_id: str, captures_root: str):
    """Audit one condition and print the AuditResult as JSON."""
    adapters = build_default_adapters(run_id, Path(captures_root))
    adapter = next(a for a in adapters if a.name == workflow)
    result = run_audit(spec, adapter)
    click.echo(result.model_dump_json(indent=2))


@main.command("experiment")
@click.option("--spec", required=True, help="Path to spec YAML.")
@click.option("--run-id", required=True, help="Run identifier (also names the CSV).")
@click.option("--captures-root", default="data/raw", show_default=True,
              help="Root holding <run-id>/<condition>/ captured artefacts.")
@click.option("--reports-dir", default="data/reports", show_default=True,
              help="Directory the immutable CSV report is written to.")
def experiment_cmd(spec: str, run_id: str, captures_root: str, reports_dir: str):
    """Run all five adapters against one spec and emit one combined CSV."""
    adapters = build_default_adapters(run_id, Path(captures_root))
    out = run_experiment(spec, run_id, adapters, reports_dir=reports_dir)
    click.echo(f"wrote {out}")
