"""Flask dashboard for the experiment CSV output.

Stage 3.5 — NOT in the dissertation scope. The CSV report is the
authoritative published artefact; this is a visual inspection layer.

Run:
    PYTHONPATH=. python -m auditor.dashboard.app
    # open http://127.0.0.1:5050

(Port 5000 is avoided because macOS AirPlay Receiver hijacks it and
returns HTTP 403; AUDITOR_PORT overrides the default if needed.)
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

# Calibrated interpretation for partner-facing charts.
# These values are not arbitrary; they reflect the metric semantics in
# docs/METRICS.md and the practical decision thresholds for enterprise use.
METRIC_CALIBRATION = {
    "security_density": {"ideal": 0.0, "warning": 50.0, "critical": 100.0},
    "complexity_mean": {"ideal": 0.0, "warning": 3.0, "critical": 6.0},
    "duplication_pct": {"ideal": 0.0, "warning": 5.0, "critical": 10.0},
    "hallucinations": {"ideal": 0.0, "warning": 1.0, "critical": 3.0},
    "correction_freq": {"ideal": 0.0, "warning": 10.0, "critical": 25.0},
}

# Short human descriptions surfaced in the UI.
METRIC_BLURB = {
    "security_density": "OWASP/CWE-tagged Bandit findings per 1000 lines of Python (per-language density)",
    "complexity_mean":  "Mean McCabe cyclomatic complexity per function (radon)",
    "duplication_pct":  "% of source lines inside a duplicated 6-line shingle",
    "hallucinations":   "Features shipped that were NOT in the spec",
    "correction_freq":  "Backspace + delete events per 1000 keystrokes",
}

# Explicit interpretation guidance for the charts and the adoption story.
METRIC_GUIDANCE = {
    "security_density": {
        "axis": "Axis guidance: lower is better. Values at or below 50 are manageable; 50 to 100 is a warning band; above 100 is a clear governance concern.",
        "adoption": "What this means for adoption: tools that produce frequent security issues should not be rolled out broadly without remediation and review.",
    },
    "complexity_mean": {
        "axis": "Axis guidance: lower is better. Values at or below 3 are broadly sustainable; 3 to 6 signals rising maintainability risk; above 6 is likely to become brittle in production.",
        "adoption": "What this means for adoption: code that is structurally complex is harder to maintain, review, and govern at scale.",
    },
    "duplication_pct": {
        "axis": "Axis guidance: lower is better. Values at or below 5 are healthy; 5 to 10 suggests avoidable copy-and-paste debt; above 10 is a strong sign of maintainability problems.",
        "adoption": "What this means for adoption: high duplication increases the chance of inconsistent fixes and makes long-term stewardship harder.",
    },
    "hallucinations": {
        "axis": "Axis guidance: lower is better. Zero is ideal; 1 to 3 indicates scope drift and trust risk; above 3 is a serious control failure.",
        "adoption": "What this means for adoption: a tool that ships features outside the spec creates procedural and compliance risk, even when it appears productive.",
    },
    "correction_freq": {
        "axis": "Axis guidance: lower is better. Values at or below 10 are efficient; 10 to 25 indicates repeated editing effort; above 25 suggests a poor interaction loop for real-world use.",
        "adoption": "What this means for adoption: high correction frequency points to friction that can erode developer trust and slow delivery.",
    },
}

app = Flask(__name__)


def _is_multi_condition_report(csv_path: Path) -> bool:
    """True only for long-format CSVs with >= 2 conditions. Hides single-spec
    human captures and wide comparison tables from the index for a clean view."""
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not {"metric", "condition", "value"} <= set(reader.fieldnames or []):
                return False
            conditions = {r["condition"] for r in reader if r.get("condition")}
        return len(conditions) >= 2
    except Exception:
        return False


def _list_reports() -> list[dict]:
    if not REPORTS_DIR.exists():
        return []
    out = []
    for csv_path in sorted(REPORTS_DIR.glob("*.csv")):
        if not _is_multi_condition_report(csv_path):
            continue
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
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        required = {"metric", "condition", "value"}
        missing = required - header
        if missing:
            # Not a long-format experiment CSV (e.g. the wide human_vs_ai
            # comparison view). Fail with a clear 400 instead of a 500.
            abort(
                400,
                description=(
                    f"'{run_id}.csv' is not a long-format report — it is missing "
                    f"column(s): {', '.join(sorted(missing))}. The dashboard renders "
                    "long-format CSVs (one row per metric × condition × rep, with a "
                    "'value' column). Wide comparison tables like "
                    "'human_vs_ai_comparison.csv' should be opened as a file, not via "
                    "/report/."
                ),
            )
        rows = []
        for r in reader:
            try:
                r["value"] = float(r["value"])
            except (TypeError, ValueError):
                continue
            rows.append(r)

    # Aggregate by (metric, condition) as the MEAN across specs/reps, not the
    # last value seen (the previous behaviour silently dropped all but one row).
    agg: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    units: dict[str, str] = {}
    for r in rows:
        agg[r["metric"]][r["condition"]].append(r["value"])
        units[r["metric"]] = r.get("unit", "")
    pivot: dict[str, dict[str, float]] = {
        m: {c: sum(v) / len(v) for c, v in conds.items()}
        for m, conds in agg.items()
    }

    conditions = sorted({r["condition"] for r in rows})
    metrics = sorted(pivot)

    # Calibrated scores from [0, 1] where 1 = best, based on metric-specific
    # decision thresholds rather than a pure within-report min-max rescale.
    norm: dict[str, dict[str, float]] = {}
    for metric in metrics:
        cfg = METRIC_CALIBRATION.get(metric, {"ideal": 0.0, "warning": 1.0, "critical": 2.0})
        ideal = cfg["ideal"]
        warning = cfg["warning"]
        critical = cfg["critical"]
        norm[metric] = {}
        for c in conditions:
            v = pivot[metric].get(c, 0.0)
            if not METRIC_LOWER_BETTER.get(metric, True):
                if v <= ideal:
                    score = 1.0
                elif v >= critical:
                    score = 0.0
                else:
                    score = 1.0 - ((v - ideal) / (critical - ideal))
            else:
                if v <= ideal:
                    score = 1.0
                elif v >= critical:
                    score = 0.0
                else:
                    score = max(0.0, 1.0 - ((v - ideal) / max(critical - ideal, 1e-6)))
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
        "metric_guidance": METRIC_GUIDANCE,
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


# ---- Pilot waitlist --------------------------------------------------------
# Visa-safe: collects email addresses for a future commercial cohort. No
# payment is taken; no commercial service is offered now. Submissions
# persist to data/waitlist.jsonl, gitignored, retrievable via `fly ssh
# console` or by emailing them to the operator on submit (best-effort).

import os
from datetime import datetime, timezone
from flask import request

WAITLIST_PATH = ROOT / "data" / "waitlist.jsonl"


def _persist_waitlist(entry: dict) -> None:
    WAITLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with WAITLIST_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _notify_operator(entry: dict) -> None:
    """Best-effort email to the operator. Silently swallows any error so
    the form submission still succeeds for the user."""
    try:
        import smtplib
        from email.message import EmailMessage
        host = os.environ.get("SMTP_HOST")
        if not host:
            return
        msg = EmailMessage()
        msg["Subject"] = f"[auditor waitlist] {entry.get('company','?')} — {entry.get('name','?')}"
        msg["From"] = os.environ.get("SMTP_FROM", "noreply@auditor.local")
        msg["To"] = os.environ.get("OPERATOR_EMAIL", "dominicrume@gmail.com")
        msg.set_content(json.dumps(entry, indent=2))
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587"))) as s:
            s.starttls()
            s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
            s.send_message(msg)
    except Exception:
        pass


@app.route("/pilot", methods=["GET", "POST"])
def pilot():
    if request.method == "POST":
        entry = {
            "name":    (request.form.get("name") or "").strip()[:120],
            "email":   (request.form.get("email") or "").strip()[:200],
            "company": (request.form.get("company") or "").strip()[:200],
            "role":    (request.form.get("role") or "").strip()[:200],
            "context": (request.form.get("context") or "").strip()[:2000],
            "ip":      request.headers.get("Fly-Client-IP") or request.remote_addr or "",
            "ua":      (request.user_agent.string or "")[:300],
            "ts":      datetime.now(timezone.utc).isoformat(),
        }
        if entry["email"] and entry["name"] and entry["company"]:
            _persist_waitlist(entry)
            _notify_operator(entry)
        return render_template("pilot.html", submitted=True)
    return render_template("pilot.html", submitted=False)


@app.route("/pilot/admin")
def pilot_admin():
    """Operator-only view. Protected by a single env token so the URL alone
    isn't enough — `?key=<WAITLIST_ADMIN_KEY>` is required."""
    key = request.args.get("key", "")
    expected = os.environ.get("WAITLIST_ADMIN_KEY", "")
    if not expected or key != expected:
        return ("unauthorised", 401)
    if not WAITLIST_PATH.exists():
        return jsonify({"entries": [], "count": 0})
    entries = [json.loads(line) for line in WAITLIST_PATH.read_text().splitlines() if line.strip()]
    return jsonify({"entries": entries, "count": len(entries)})


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
    # Avoid macOS AirPlay's port 5000 (HTTP 403 hijack). Override via env.
    port = int(os.environ.get("AUDITOR_PORT", "5050"))
    app.run(host="127.0.0.1", port=port, debug=False)
