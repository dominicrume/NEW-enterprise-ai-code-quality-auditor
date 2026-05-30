"""Security analyzer — SonarQube integration. Network is monkeypatched."""
import json
from pathlib import Path

import pytest

from auditor.analyzers import security_analyzer

FIXTURE = Path(__file__).parent / "fixtures" / "sonarqube" / "issues_response.json"


@pytest.fixture
def sonar_payload():
    return json.loads(FIXTURE.read_text())


@pytest.fixture
def codebase_1kloc():
    # 1000 lines exactly -> per-kloc density equals raw count.
    body = "\n".join(f"x = {i}" for i in range(1000)) + "\n"
    return {"files": {"app.py": body}, "manifest": []}


def test_counts_only_owasp_or_cwe_tagged_issues(monkeypatch, codebase_1kloc, sonar_payload):
    captured = {}

    def fake_fetch(component_key):
        captured["key"] = component_key
        return sonar_payload["issues"]

    monkeypatch.setattr(security_analyzer, "_fetch_issues", fake_fetch)

    spec = {"name": "agent_education_system", "version": "1"}
    score = security_analyzer.analyze(codebase_1kloc, [], spec)

    assert score.name == "security_density"
    assert score.unit == "per_kloc"
    # 3 of 4 issues are OWASP/CWE tagged; LOC is 1000 → density = 3.0
    assert score.value == pytest.approx(3.0)
    # The project key is taken from the spec name.
    assert captured["key"] == "agent_education_system"


def test_prefers_sonar_project_key_when_present(monkeypatch, codebase_1kloc):
    captured = {}

    def fake_fetch(component_key):
        captured["key"] = component_key
        return []

    monkeypatch.setattr(security_analyzer, "_fetch_issues", fake_fetch)
    security_analyzer.analyze(
        codebase_1kloc, [],
        {"name": "fallback", "sonar_project_key": "explicit_key"},
    )
    assert captured["key"] == "explicit_key"


def test_raises_without_credentials(monkeypatch, codebase_1kloc):
    monkeypatch.setattr(security_analyzer.settings, "sonarqube_url", "")
    monkeypatch.setattr(security_analyzer.settings, "sonarqube_token", "")
    with pytest.raises(RuntimeError, match="SONARQUBE_URL"):
        security_analyzer.analyze(codebase_1kloc, [], {"name": "x"})
