"""Dashboard smoke tests — index page lists reports, report page renders."""
import csv
import json
from pathlib import Path

import pytest

from auditor.dashboard import app as dashboard_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    # Synthetic minimal CSV + provenance.
    rows = [
        ["run_id", "condition", "spec_name", "spec_version", "metric", "value", "unit", "timestamp"],
        ["test_001", "human_control", "s", "1", "complexity_mean", "1.5", "cc", "2026-05-27T00:00:00+00:00"],
        ["test_001", "claude_code", "s", "1", "complexity_mean", "2.0", "cc", "2026-05-27T00:00:00+00:00"],
    ]
    with open(reports / "test_001.csv", "w", newline="") as f:
        csv.writer(f).writerows(rows)
    (reports / "test_001.provenance.json").write_text(json.dumps({
        "kind": "pilot", "warning": "synthetic data", "is_dissertation_result": False,
    }))
    monkeypatch.setattr(dashboard_app, "REPORTS_DIR", reports)
    dashboard_app.app.config["TESTING"] = True
    return dashboard_app.app.test_client()


def test_index_lists_reports(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "test_001" in body
    assert "pilot" in body.lower()


def test_report_page_renders_table(client):
    resp = client.get("/report/test_001")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "complexity_mean" in body
    assert "human_control" in body
    assert "claude_code" in body
    assert "Pilot data" in body  # banner shown
    assert "synthetic data" in body


def test_report_page_exposes_view_mode_controls(client):
    resp = client.get("/report/test_001")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Calibrated scores" in body
    assert "Raw values" in body


def test_report_page_shows_metric_guidance_and_adoption_summary(client):
    resp = client.get("/report/test_001")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "Axis guidance" in body
    assert "What this means for adoption" in body


def test_unknown_report_is_404(client):
    assert client.get("/report/does_not_exist").status_code == 404
