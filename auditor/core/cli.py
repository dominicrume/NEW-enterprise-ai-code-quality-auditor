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
@click.option("--spec", default=None,
              help="Path to one spec YAML (pilot mode only). Ignored if --reps is set.")
@click.option("--run-id", default=None,
              help="Pilot mode: identifier locating <captures-root>/<run-id>/.")
@click.option("--run-label", default=None,
              help="Main-study mode: label for the orchestrated batch.")
@click.option("--reps", default=None, type=int,
              help="Main-study mode: repetitions per (condition × spec). "
                   "Triggers the full pre-registered orchestrator. "
                   "Use --reps 10 for the default dissertation design.")
@click.option("--seed", default=42, show_default=True, type=int,
              help="RNG seed for the run-order shuffle (main-study mode).")
@click.option("--skip", multiple=True,
              help="Conditions to skip in main-study mode "
                   "(e.g. --skip replit_agent --skip antigravity).")
@click.option("--captures-root", default="data/raw", show_default=True,
              help="Pilot mode: root holding pre-captured <run-id>/<condition>/.")
@click.option("--reports-dir", default="data/reports", show_default=True,
              help="Pilot mode: directory the immutable CSV report is written to.")
def experiment_cmd(spec, run_id, run_label, reps, seed, skip,
                   captures_root, reports_dir):
    """Run an experiment and emit a CSV.

    Two modes:

    \b
    PILOT MODE — score pre-captured artefacts (legacy):
        auditor experiment --spec specs/X.yaml --run-id pilot_001

    \b
    MAIN-STUDY MODE — orchestrate the full pre-registered design:
        auditor experiment --reps 10 --run-label main_001
    """
    if reps is not None:
        from auditor.core.study import run_study
        if not run_label:
            raise click.UsageError("--run-label is required with --reps")
        out = run_study(reps=reps, run_label=run_label, seed=seed,
                        skip=tuple(skip), log=click.echo)
        click.echo(f"wrote {out}")
        return
    if not (spec and run_id):
        raise click.UsageError(
            "pilot mode needs --spec and --run-id; main-study mode needs --reps and --run-label")
    adapters = build_default_adapters(run_id, Path(captures_root))
    out = run_experiment(spec, run_id, adapters, reports_dir=reports_dir)
    click.echo(f"wrote {out}")
