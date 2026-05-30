"""Smoke test: every code cell in notebooks/analysis.ipynb runs cleanly.

We don't run the real notebook tooling (papermill/jupyter) — we just
extract the code cells, redirect REPORTS_DIR at a tmp synthetic dataset,
and exec each cell. This catches breakage from analyzer / CSV-schema drift.
"""
import json
import random
from pathlib import Path

import pandas as pd
import pytest

NB = Path(__file__).parent.parent / "notebooks" / "analysis.ipynb"

CONDITIONS = ["human_control", "claude_code", "cursor_agent", "antigravity", "replit_agent"]
METRICS = ["security_density", "complexity_mean", "duplication_pct",
           "hallucinations", "correction_freq"]


def _synthesise_reports(reports_dir: Path, n_runs: int = 4) -> None:
    """Write n_runs CSVs giving us a real sample size for inferential tests."""
    rng = random.Random(42)
    reports_dir.mkdir(parents=True, exist_ok=True)
    for r in range(n_runs):
        rows = []
        for cond in CONDITIONS:
            for metric in METRICS:
                # Give human_control distinctly different values for some metrics
                # so omnibus tests have something to find.
                base = {"correction_freq": 80, "hallucinations": 0,
                        "security_density": 2.0, "complexity_mean": 3.0,
                        "duplication_pct": 5.0}[metric]
                if cond != "human_control" and metric == "correction_freq":
                    base = 0
                if cond == "claude_code" and metric == "hallucinations":
                    base = 2
                rows.append({
                    "run_id": f"run_{r:03d}",
                    "condition": cond,
                    "spec_name": "test",
                    "spec_version": "1",
                    "metric": metric,
                    "value": base + rng.uniform(-0.5, 0.5),
                    "unit": "",
                    "timestamp": "2026-05-27T00:00:00+00:00",
                })
        pd.DataFrame(rows).to_csv(reports_dir / f"run_{r:03d}.csv", index=False)


def test_notebook_cells_execute(tmp_path):
    reports = tmp_path / "data" / "reports"
    _synthesise_reports(reports)

    nb = json.loads(NB.read_text())
    code = "\n".join(
        "".join(cell["source"]) for cell in nb["cells"] if cell["cell_type"] == "code"
    )

    # Redirect REPORTS_DIR to the synthetic location and avoid GUI/savefig.
    preamble = (
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        f"_REPORTS_OVERRIDE = r'{reports}'\n"
    )
    code = code.replace(
        "REPORTS_DIR = Path('../data/reports')",
        "REPORTS_DIR = Path(_REPORTS_OVERRIDE)",
    )

    ns: dict = {}
    exec(preamble + code, ns)

    # Spot-check: the comparison_summary.csv was written.
    out = reports / "comparison_summary.csv"
    assert out.is_file()
    summary = pd.read_csv(out)
    assert {"metric", "p", "significant"}.issubset(summary.columns) or "metric" in summary.columns
    # The Kruskal omnibus runs over our synthetic data should detect the
    # correction_freq divergence between human_control and the agents.
    omnibus = ns["omnibus_df"]
    sig_metrics = set(omnibus.query("significant == True")["metric"]) if "significant" in omnibus.columns else set()
    assert "correction_freq" in sig_metrics
