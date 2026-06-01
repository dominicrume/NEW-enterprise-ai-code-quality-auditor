"""Pilot waitlist — landing page renders, POST persists, admin endpoint is gated."""
import json
import pytest

from auditor.dashboard.app import app, WAITLIST_PATH


@pytest.fixture(autouse=True)
def _isolate_waitlist(tmp_path, monkeypatch):
    """Redirect WAITLIST_PATH to a tmp file per test so the real CSV is
    never touched, and any prior test data doesn't bleed across runs."""
    import auditor.dashboard.app as mod
    monkeypatch.setattr(mod, "WAITLIST_PATH", tmp_path / "waitlist.jsonl")
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_pilot_page_renders(client):
    res = client.get("/pilot")
    assert res.status_code == 200
    body = res.data.decode()
    assert "Cohort 1" in body
    assert "Claude Code" in body
    assert "Replit Agent" in body
    assert "Cohort 1 waitlist" in body  # form is visible (not the submitted-success state)


def test_post_persists_and_shows_thanks(client, monkeypatch):
    import auditor.dashboard.app as mod
    res = client.post("/pilot", data={
        "name": "Alex Buyer", "email": "alex@example.com",
        "company": "AcmeCo", "role": "Eng Manager",
        "context": "We use Cursor, want Claude scored too.",
    })
    assert res.status_code == 200
    assert b"You're on the list" in res.data
    # And persisted
    entries = [json.loads(l) for l in mod.WAITLIST_PATH.read_text().splitlines()]
    assert len(entries) == 1
    assert entries[0]["email"] == "alex@example.com"
    assert entries[0]["company"] == "AcmeCo"


def test_post_with_missing_fields_does_not_persist(client):
    import auditor.dashboard.app as mod
    res = client.post("/pilot", data={"name": "x"})
    assert res.status_code == 200  # still shows thanks, but nothing persisted
    assert not mod.WAITLIST_PATH.exists() or mod.WAITLIST_PATH.read_text().strip() == ""


def test_admin_requires_key(client):
    res = client.get("/pilot/admin")
    assert res.status_code == 401


def test_admin_returns_entries_with_key(client, monkeypatch):
    import auditor.dashboard.app as mod
    monkeypatch.setenv("WAITLIST_ADMIN_KEY", "secret123")
    mod.WAITLIST_PATH.write_text(json.dumps({
        "name": "X", "email": "x@y.z", "company": "Z"
    }) + "\n")
    res = client.get("/pilot/admin?key=secret123")
    assert res.status_code == 200
    body = json.loads(res.data)
    assert body["count"] == 1
    assert body["entries"][0]["email"] == "x@y.z"
