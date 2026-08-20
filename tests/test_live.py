"""Tests for the live audit surface.

The behaviour that matters: a user who has never seen a spec can type what
they asked for and get scope-drift detection, and nothing is ever scored
against a stale definition of "what was asked for".
"""
import time
from pathlib import Path

import pytest
import yaml

from auditor.live.brief import build_spec, load_spec, parse_brief, save_spec, slugify
from auditor.live.server import LiveSession, create_app


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text("print('hi')\n")
    return tmp_path


@pytest.fixture
def client(project):
    session = LiveSession(project, interval=0.2)
    app = create_app(session)
    app.config["TESTING"] = True
    yield app.test_client(), session
    session.stop()


def _drift(client):
    report = client.get("/api/state").get_json()["report"]
    return next(m for m in report["metrics"] if m["name"] == "hallucinations")


# ------------------------------------------------------------------- brief

@pytest.mark.parametrize("text,expected", [
    ("Users can log in with email", "log.in.email"),
    ("- Build a course listing page", "course.listing.page"),
    ("1. Export data to CSV", "export.data.csv"),
])
def test_slugify_drops_filler_words(text, expected):
    from auditor.live.brief import _BULLET
    assert slugify(_BULLET.sub("", text), "x") == expected


def test_parse_brief_handles_bullets_and_numbering():
    features = parse_brief("- Register an account\n2) Log in\n• View courses\n\n  \n")
    assert [f["id"] for f in features] == ["register.account", "log.in", "view.courses"]
    assert features[0]["description"] == "Register an account"


def test_parse_brief_deduplicates_ids():
    ids = [f["id"] for f in parse_brief("Log in\nLog in\nLog in")]
    assert len(set(ids)) == 3


def test_brief_produces_a_spec_the_analysers_accept():
    spec = build_spec("Users can register\nUsers can log in")
    assert spec["name"] and spec["version"]
    assert len(spec["features"]) == 2
    assert all("id" in f and "description" in f for f in spec["features"])
    assert "governance" in spec and "allowlist" in spec


def test_spec_round_trips_to_an_editable_file(project):
    path = save_spec(project, build_spec("Users can register"))
    assert path.exists()
    assert path.read_text().startswith("#")          # explains itself to the reader
    assert yaml.safe_load(path.read_text())["features"][0]["id"] == "register"
    assert load_spec(project)["features"][0]["id"] == "register"


def test_load_spec_survives_a_corrupt_file(project):
    path = project / ".auditor" / "spec.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("{{ not: valid: yaml")
    assert load_spec(project) is None


# ------------------------------------------------------------------ server

def test_page_and_state_render_before_any_setup(client):
    c, _ = client
    assert c.get("/").status_code == 200
    state = c.get("/api/state").get_json()
    assert state["has_spec"] is False
    assert state["report"]["files"] == 1


def test_scope_drift_is_explained_not_zeroed_before_a_brief(client):
    c, _ = client
    drift = _drift(c)
    assert drift["value"] is None
    assert "asked for" in drift["skipped"]


def test_submitting_a_brief_turns_scope_drift_on(client, project):
    c, _ = client
    res = c.post("/api/brief", json={"brief": "Users can register\nUsers can log in"})
    assert res.status_code == 200
    assert res.get_json()["features"] == 2
    assert (project / ".auditor" / "spec.yaml").exists()

    drift = _drift(c)
    assert drift["skipped"] is None
    assert drift["value"] == 0.0


def test_empty_brief_is_rejected_with_a_usable_message(client):
    c, _ = client
    res = c.post("/api/brief", json={"brief": "   "})
    assert res.status_code == 400
    assert "asked" in res.get_json()["error"]


def test_off_spec_route_is_detected_after_a_brief(client, project):
    """The end-to-end promise: type the brief, agent goes off-spec, it shows."""
    c, _ = client
    c.post("/api/brief", json={"brief": "Users can register\nUsers can log in"})
    assert _drift(c)["value"] == 0.0

    (project / "api.py").write_text(
        'from fastapi import FastAPI\n'
        'app = FastAPI()\n\n'
        '@app.get("/health")\n'
        'def health():\n    return {}\n'
    )
    for _ in range(25):
        time.sleep(0.2)
        if _drift(c)["value"]:
            break
    assert _drift(c)["value"] == 1.0, "off-spec route was not detected live"


def test_stream_paints_immediately(client):
    """A new browser must never wait for a file change to see something."""
    c, _ = client
    with c.get("/api/stream", buffered=False) as res:
        assert res.status_code == 200
        first = next(res.response).decode()
    assert first.startswith("data: ")
    assert "metrics" in first


# ------------------------------------------------------- install resilience

def test_free_port_falls_through_a_collision():
    """A port collision must never be a decision the user has to make."""
    import socket

    from auditor.core.cli import _free_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as taken:
        taken.bind(("127.0.0.1", 0))
        occupied = taken.getsockname()[1]
        taken.listen(1)
        assert _free_port(occupied) != occupied


def test_module_entrypoint_exists():
    """`python -m auditor` must work when the console script isn't on PATH."""
    import auditor.__main__ as entry

    assert callable(entry.main)


def test_empty_project_reports_no_files_without_crashing(tmp_path):
    session = LiveSession(tmp_path, interval=0.2)
    client = create_app(session).test_client()
    report = client.get("/api/state").get_json()["report"]
    assert report["files"] == 0
    assert all(m["value"] is None for m in report["metrics"])
    session.stop()


# ------------------------------------------------------------------- csrf

def test_cross_origin_brief_is_rejected(client):
    """Binding to localhost does not stop a web page the user has open."""
    c, _ = client
    res = c.post("/api/brief",
                 json={"brief": "Attacker rewrites the spec"},
                 headers={"Origin": "https://evil.example"})
    assert res.status_code == 403
    assert "Cross-origin" in res.get_json()["error"]


def test_same_origin_brief_is_accepted(client):
    c, _ = client
    res = c.post("/api/brief", json={"brief": "Users can log in"},
                 headers={"Origin": "http://localhost"})
    assert res.status_code == 200


def test_non_browser_client_still_works(client):
    """curl and tests send no Origin header and must not be locked out."""
    c, _ = client
    assert c.post("/api/brief", json={"brief": "Users can log in"}).status_code == 200
