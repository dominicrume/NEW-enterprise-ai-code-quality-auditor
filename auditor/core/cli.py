"""Command-line entry.

  auditor run        --spec X --workflow Y --run-id R   [--captures-root]
  auditor experiment --spec X --run-id Y                [--captures-root --reports-dir]

`run` audits a single condition; `experiment` audits all five and emits the
combined CSV report. Both commands rely on a captures directory laid out as
``<captures-root>/<run-id>/<condition>/`` — produced by capture-time invocations
of the adapters (see human_control_recorder.py and the per-vendor capture
flow in docs/METHODOLOGY.md).
"""
import time
from pathlib import Path

import click

from auditor.core.experiment import build_default_adapters, run_experiment
from auditor.core.runner import run_audit

CONDITIONS = ["human_control", "claude_code", "cursor_agent", "antigravity", "replit_agent"]


@click.group()
def main():
    """AI Code Quality Auditor.

    \b
    Start here:       auditor live
    Audit a folder:   auditor scan .
    Watch a folder:   auditor watch .
    Run the study:    auditor experiment --run-label main_001 --reps 10
    """


@main.command("live")
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path),
                default=".")
@click.option("--port", default=7777, show_default=True, type=int)
@click.option("--no-open", is_flag=True, help="Don't open a browser automatically.")
@click.option("--interval", default=1.0, show_default=True, type=float,
              help="Seconds between change checks.")
def live_cmd(path: Path, port: int, no_open: bool, interval: float):
    """Open a live audit dashboard for a folder. Start here.

    \b
      auditor live            audit this folder, live, in your browser

    Watches the folder and updates as code changes — yours or an agent's.
    Type what you asked the agent to build and scope-drift checking turns
    on. Ctrl+C to stop.
    """
    import logging
    import threading
    import webbrowser

    import flask.cli

    from auditor.live.server import LiveSession, create_app

    # A local audit tool is not a deployment. The dev-server banner and the
    # per-request log are noise that reads as an error to a first-time user.
    flask.cli.show_server_banner = lambda *a, **k: None
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    session = LiveSession(path, interval=interval)
    app = create_app(session)  # starts the watcher

    url = f"http://127.0.0.1:{port}"
    click.echo()
    click.echo(f"  Live audit  {session.project}")
    click.echo(f"  {url}")
    click.echo(f"  {session.latest.file_count} files · "
               f"{session.latest.total_loc} lines · Ctrl+C to stop")
    click.echo()

    if not no_open:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()

    try:
        app.run(host="127.0.0.1", port=port, threaded=True,
                debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        session.stop()
        click.echo("stopped")


BAND_STYLE = {"good": "green", "warn": "yellow", "critical": "red"}
BAND_MARK = {"good": "OK", "warn": "WARN", "critical": "RISK"}


@main.command("scan")
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path),
                default=".")
@click.option("--spec", type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None,
              help="Spec YAML declaring what was asked for. Enables the scope-drift check.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON instead of a table.")
@click.option("--fail-on", type=click.Choice(["never", "warn", "critical"]),
              default="never", show_default=True,
              help="Exit non-zero at this severity, for CI gating.")
def scan_cmd(path: Path, spec: Path | None, as_json: bool, fail_on: str):
    """Audit a directory in place — no session, no setup.

    \b
      auditor scan .                       audit the current folder
      auditor scan ./src --spec spec.yaml  include the scope-drift check
      auditor scan . --fail-on critical    gate a CI pipeline
    """
    import json as _json

    import yaml
    from rich.console import Console
    from rich.table import Table

    from auditor.core.scan import scan_directory

    spec_data = yaml.safe_load(spec.read_text()) if spec else None
    result = scan_directory(path, spec_data)

    if as_json:
        click.echo(_json.dumps({
            "path": str(result.path),
            "files": result.file_count,
            "total_loc": result.total_loc,
            "python_files": result.python_files,
            "spec": result.spec_name,
            "coverage_note": result.coverage_note,
            "metrics": {
                o.name: ({"value": o.value, "unit": o.unit, "band": o.band}
                         if o.applicable else {"skipped": o.skipped_reason})
                for o in result.outcomes
            },
        }, indent=2))
    else:
        console = Console()
        console.print()
        console.print(f"[bold]{result.path}[/bold]")
        console.print(
            f"[dim]{result.file_count} files · {result.total_loc} lines · "
            f"{result.python_files} Python"
            + (f" · spec: {result.spec_name}" if result.spec_name else "")
            + "[/dim]\n"
        )

        table = Table(show_edge=False, header_style="dim", pad_edge=False)
        table.add_column("")
        table.add_column("Check")
        table.add_column("Value", justify="right")
        table.add_column("")
        for o in result.outcomes:
            if o.applicable:
                style = BAND_STYLE[o.band]
                table.add_row(f"[{style}]●[/{style}]", o.label,
                              f"{o.value:.2f}", f"[{style}]{BAND_MARK[o.band]}[/{style}]")
            else:
                table.add_row("[dim]○[/dim]", f"[dim]{o.label}[/dim]",
                              "[dim]n/a[/dim]", f"[dim]{o.skipped_reason}[/dim]")
        console.print(table)

        if result.coverage_note:
            console.print(f"\n[yellow]Coverage:[/yellow] {result.coverage_note}")
        console.print()

    thresholds = {"never": None, "warn": ("warn", "critical"), "critical": ("critical",)}
    trigger = thresholds[fail_on]
    if trigger and result.worst_band in trigger:
        raise SystemExit(1)


def _render_scan_table(console, result):
    """Shared table renderer for `scan` and `watch`."""
    from rich.table import Table

    table = Table(show_edge=False, header_style="dim", pad_edge=False)
    table.add_column("")
    table.add_column("Check")
    table.add_column("Value", justify="right")
    table.add_column("")
    for o in result.outcomes:
        if o.applicable:
            style = BAND_STYLE[o.band]
            table.add_row(f"[{style}]●[/{style}]", o.label,
                          f"{o.value:.2f}", f"[{style}]{BAND_MARK[o.band]}[/{style}]")
        else:
            table.add_row("[dim]○[/dim]", f"[dim]{o.label}[/dim]",
                          "[dim]n/a[/dim]", f"[dim]{o.skipped_reason}[/dim]")
    console.print(table)


@main.command("watch")
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path),
                default=".")
@click.option("--spec", type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None,
              help="Spec YAML declaring what was asked for. Enables live scope-drift.")
@click.option("--interval", default=1.0, show_default=True, type=float,
              help="Seconds between change checks.")
def watch_cmd(path: Path, spec: Path | None, interval: float):
    """Re-audit continuously as the code changes.

    \b
      auditor watch .                       watch the current folder
      auditor watch . --spec spec.yaml      see scope drift appear live

    Leave this running while an agent works. Ctrl+C to stop.
    """
    import yaml
    from rich.console import Console

    from auditor.core.scan import scan_directory
    from auditor.core.watch import watch_directory

    console = Console()
    spec_data = yaml.safe_load(spec.read_text()) if spec else None
    baseline = scan_directory(path, spec_data)

    console.print()
    console.print(f"[bold]Watching {Path(path).resolve()}[/bold]")
    console.print(
        f"[dim]{baseline.file_count} files · {baseline.total_loc} lines"
        + (f" · spec: {baseline.spec_name}" if baseline.spec_name else " · no spec")
        + " · Ctrl+C to stop[/dim]\n"
    )
    _render_scan_table(console, baseline)
    if baseline.coverage_note:
        console.print(f"\n[yellow]Coverage:[/yellow] {baseline.coverage_note}")
    console.print("\n[dim]— waiting for changes —[/dim]")

    try:
        for event in watch_directory(path, spec_data, interval=interval):
            stamp = time.strftime("%H:%M:%S")
            shown = ", ".join(event.changed_files[:3])
            if len(event.changed_files) > 3:
                shown += f" +{len(event.changed_files) - 3} more"
            console.print(f"\n[dim]{stamp}[/dim]  [cyan]{shown}[/cyan]")

            if not event.deltas:
                console.print("  [dim]no change to any metric[/dim]")
                continue

            for d in event.deltas:
                if d.became_measurable:
                    style = BAND_STYLE[d.after_band]
                    console.print(
                        f"  [{style}]▲[/{style}] {d.label} now measurable — "
                        f"[{style}]{d.after:.2f} {BAND_MARK[d.after_band]}[/{style}]"
                    )
                elif d.became_unmeasurable:
                    console.print(f"  [dim]○ {d.label} no longer measurable[/dim]")
                else:
                    arrow = "↑" if d.direction == "worse" else "↓"
                    style = BAND_STYLE[d.after_band] if d.after_band else "white"
                    line = (f"  [{style}]{arrow}[/{style}] {d.label} "
                            f"{d.before:.2f} → [{style}]{d.after:.2f}[/{style}]")
                    if d.changed_band:
                        line += (f"  [{style}]{BAND_MARK[d.before_band]}"
                                 f" → {BAND_MARK[d.after_band]}[/{style}]")
                    console.print(line)

            if event.notable:
                console.print("  [yellow]↳ threshold crossed — worth a look[/yellow]")
    except KeyboardInterrupt:
        console.print("\n[dim]stopped[/dim]\n")


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
