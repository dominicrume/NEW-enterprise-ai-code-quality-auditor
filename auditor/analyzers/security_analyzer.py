"""Security vulnerability density — SonarQube integration.

See docs/METRICS.md for the exact rule sets counted. In short:
  * issue ``type`` ∈ {VULNERABILITY, SECURITY_HOTSPOT}
  * at least one OWASP/CWE tag (``cwe*`` or ``owasp-*``)
  * status ∈ {OPEN, CONFIRMED, REOPENED}

The function signature is unchanged — the engine, adapters, and tests that
already call ``analyze(codebase, interaction_log, spec)`` keep working.
Credentials are read from ``settings`` (i.e. ``.env``), never inlined.
"""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request

from auditor.core.config import settings
from auditor.models.audit_result import MetricScore


_ISSUE_TYPES = "VULNERABILITY"
_OPEN_STATUSES = "OPEN,CONFIRMED,REOPENED"
_PAGE_SIZE = 500


def _is_owasp_or_cwe(issue: dict) -> bool:
    """True iff at least one tag identifies this as an OWASP/CWE finding."""
    for tag in issue.get("tags", []):
        t = tag.lower()
        if t == "cwe" or t.startswith("cwe-") or t.startswith("owasp-"):
            return True
    return False


def _fetch_issues(component_key: str) -> list[dict]:
    """Page through SonarQube's /api/issues/search for one project."""
    url = settings.sonarqube_url
    token = settings.sonarqube_token
    if not url or not token:
        raise RuntimeError(
            "SONARQUBE_URL and SONARQUBE_TOKEN must be set in .env to run the "
            "security analyzer."
        )
    auth = base64.b64encode(f"{token}:".encode()).decode()
    organization = settings.sonarqube_organization

    issues: list[dict] = []
    page = 1
    while True:
        params = {
            "componentKeys": component_key,
            "types": _ISSUE_TYPES,
            "statuses": _OPEN_STATUSES,
            "ps": _PAGE_SIZE,
            "p": page,
        }
        if organization:
            params["organization"] = organization
        qs = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{url.rstrip('/')}/api/issues/search?{qs}")
        req.add_header("Authorization", f"Basic {auth}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        batch = data.get("issues", [])
        issues.extend(batch)
        total = data.get("total", 0)
        if not batch or page * _PAGE_SIZE >= total:
            break
        page += 1
    return issues


def _project_key(spec: dict) -> str:
    return spec.get("sonar_project_key") or spec.get("name") or ""


def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore:
    loc = sum(len(c.splitlines()) for c in codebase.get("files", {}).values()) or 1
    key = _project_key(spec)
    if not key:
        raise ValueError("spec must define 'name' or 'sonar_project_key' for SonarQube lookup")
    issues = _fetch_issues(key)
    relevant = [i for i in issues if _is_owasp_or_cwe(i)]
    density = (len(relevant) / loc) * 1000
    return MetricScore(name="security_density", value=density, unit="per_kloc")
