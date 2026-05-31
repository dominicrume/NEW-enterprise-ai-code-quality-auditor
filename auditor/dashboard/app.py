"""Flask dashboard for the experiment CSV output.

Stage 3.5 — NOT in the dissertation scope. The CSV report is the
authoritative published artefact; this is a visual inspection layer.

Run:
    PYTHONPATH=. python -m auditor.dashboard.app
    # open http://127.0.0.1:5000
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from flask import Flask, abort, jsonify, render_template

ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = ROOT / "data" / "reports"

# Each metric's polarity: True = lower is better.
METRIC_LOWER_BETTER = {
    "security_density": True,
    "complexity_mean": True,
    "duplication_pct": True,
    "hallucinations": True,
    "correction_freq": True,
}

# Short human descriptions surfaced in the UI.
METRIC_BLURB = {
    "security_density": "OWASP/CWE-tagged SonarQube issues per 1000 LOC",
    "complexity_mean":  "Mean McCabe cyclomatic complexity per function (radon)",
    "duplication_pct":  "% of source lines inside a duplicated 6-line shingle",
    "hallucinations":   "Features shipped that were NOT in the spec",
    "correction_freq":  "Backspace + delete events per 1000 keystrokes",
}

app = Flask(__name__)


def _list_reports() -> list[dict]:
    if not REPORTS_DIR.exists():
        return []
    out = []
    for csv_path in sorted(REPORTS_DIR.glob("*.csv")):
        prov_path = REPORTS_DIR / f"{csv_path.stem}.provenance.json"
        prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
        out.append({
            "run_id": csv_path.stem,
            "csv": csv_path.name,
            "kind": prov.get("kind", "unknown"),
            "is_pilot": prov.get("kind") == "pilot",
            "is_dissertation_result": prov.get("is_dissertation_result", False),
            "generated_at": prov.get("generated_at"),
            "spec": prov.get("spec"),
        })
    return out


def _load_report(run_id: str) -> dict:
    csv_path = REPORTS_DIR / f"{run_id}.csv"
    if not csv_path.exists():
        abort(404)
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["value"] = float(r["value"])
            rows.append(r)

    pivot: dict[str, dict[str, float]] = defaultdict(dict)
    units: dict[str, str] = {}
    for r in rows:
        pivot[r["metric"]][r["condition"]] = r["value"]
        units[r["metric"]] = r.get("unit", "")

    conditions = sorted({r["condition"] for r in rows})
    metrics = sorted(pivot)

    # Per-metric normalization to [0, 1] where 1 = best.
    norm: dict[str, dict[str, float]] = {}
    for metric in metrics:
        values = [pivot[metric].get(c, 0.0) for c in conditions]
        vmin, vmax = min(values), max(values)
        spread = (vmax - vmin) or 1.0
        norm[metric] = {}
        for c in conditions:
            v = pivot[metric].get(c, 0.0)
            score = 1 - ((v - vmin) / spread) if METRIC_LOWER_BETTER.get(metric, True) \
                else ((v - vmin) / spread)
            norm[metric][c] = round(score, 4)

    # Per-metric ranking (1 = best). Ties share a rank.
    ranks: dict[str, dict[str, int]] = {}
    for metric in metrics:
        ordered = sorted(
            conditions,
            key=lambda c: pivot[metric].get(c, 0.0),
            reverse=not METRIC_LOWER_BETTER.get(metric, True),
        )
        rank_map: dict[str, int] = {}
        prev_value = None
        rank = 0
        for i, c in enumerate(ordered, start=1):
            v = pivot[metric].get(c, 0.0)
            if v != prev_value:
                rank = i
                prev_value = v
            rank_map[c] = rank
        ranks[metric] = rank_map

    # Composite leaderboard: lowest sum of ranks wins.
    leaderboard = []
    for c in conditions:
        total = sum(ranks[m][c] for m in metrics)
        leaderboard.append({
            "condition": c,
            "rank_sum": total,
            "avg_rank": round(total / max(len(metrics), 1), 2),
            "wins": sum(1 for m in metrics if ranks[m][c] == 1),
        })
    leaderboard.sort(key=lambda x: x["rank_sum"])
    for i, row in enumerate(leaderboard, start=1):
        row["overall_rank"] = i

    # Best / worst per metric (for hero cards).
    summary = []
    for metric in metrics:
        items = [(c, pivot[metric].get(c, 0.0)) for c in conditions]
        reverse = not METRIC_LOWER_BETTER.get(metric, True)
        items.sort(key=lambda x: x[1], reverse=reverse)
        summary.append({
            "metric": metric,
            "unit": units.get(metric, ""),
            "blurb": METRIC_BLURB.get(metric, ""),
            "best_condition": items[0][0],
            "best_value": items[0][1],
            "worst_condition": items[-1][0],
            "worst_value": items[-1][1],
            "values": {c: pivot[metric].get(c, 0.0) for c in conditions},
        })

    prov_path = REPORTS_DIR / f"{run_id}.provenance.json"
    provenance = json.loads(prov_path.read_text()) if prov_path.exists() else None

    # Auto-classify pilot vs dissertation per protocol §4: dissertation
    # threshold is N >= 5 reps per condition. Computed from the CSV itself,
    # so a report graduates automatically once enough data lands.
    reps_per_condition: dict[str, int] = {}
    for cond in conditions:
        cond_rows = [r for r in rows if r["condition"] == cond]
        per_metric_counts = defaultdict(int)
        for r in cond_rows:
            per_metric_counts[r["metric"]] += 1
        reps_per_condition[cond] = (
            min(per_metric_counts.values()) if per_metric_counts else 0
        )
    min_n = min(reps_per_condition.values()) if reps_per_condition else 0
    declared_kind = (provenance or {}).get("kind", "unknown")
    if min_n >= 5 or declared_kind == "main_study":
        banner_kind = "dissertation"
        banner_text = (
            f"Dissertation result. N = {min_n} runs per condition "
            f"(across {len(conditions)} conditions)."
        )
    elif declared_kind == "pilot" or min_n < 5:
        banner_kind = "pilot"
        banner_text = (
            f"Pilot data — N = {min_n} run(s) per condition. "
            "Dissertation threshold is N ≥ 5 per protocol §4."
        )
    else:
        banner_kind = "unknown"
        banner_text = "Provenance unknown — see provenance metadata at the foot of this report."

    return {
        "run_id": run_id,
        "rows": rows,
        "pivot": {m: pivot[m] for m in metrics},
        "norm": norm,
        "ranks": ranks,
        "summary": summary,
        "leaderboard": leaderboard,
        "units": units,
        "blurbs": METRIC_BLURB,
        "conditions": conditions,
        "metrics": metrics,
        "provenance": provenance,
        "banner_kind": banner_kind,
        "banner_text": banner_text,
        "reps_per_condition": reps_per_condition,
    }


# ---- HTML routes -----------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", reports=_list_reports())


@app.route("/report/<run_id>")
def report(run_id: str):
    return render_template("report.html", **_load_report(run_id))


# ---- JSON API --------------------------------------------------------------

@app.route("/api/reports")
def api_reports():
    return jsonify(_list_reports())


@app.route("/api/report/<run_id>")
def api_report(run_id: str):
    data = _load_report(run_id)
    # rows is large; the SPA can request it separately if needed.
    data = {k: v for k, v in data.items() if k != "rows"}
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
