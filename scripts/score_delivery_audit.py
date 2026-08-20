"""Score the AI-generated mobile client + landing page with the auditor.

Dogfooding: the instrument scoring code that Claude Code produced in this
session, against the spec of what was actually requested.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "/Users/dominicorumeuririe/Downloads/NEW-enterprise-ai-code-quality-auditor")
ROOT = Path("/Users/dominicorumeuririe/Downloads/NEW-enterprise-ai-code-quality-auditor")

import yaml
from auditor.analyzers import (
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    keystroke_analyzer,
    security_analyzer,
)

spec = yaml.safe_load((ROOT / "specs/assurance_mobile_client.yaml").read_text())

# Build the codebase exactly as an adapter would: only files this session
# authored, excluding dependencies and generated artefacts.
files = {}
for rel in [
    "mobile/App.tsx",
    "mobile/src/api.ts",
    "mobile/src/theme.ts",
    "mobile/src/components.tsx",
    "mobile/src/ReportsScreen.tsx",
    "mobile/src/ReportDetailScreen.tsx",
    "mobile/app.json",
    "mobile/eas.json",
    "docs/landing/mobile-app.html",
]:
    files[rel] = (ROOT / rel).read_text()

# The delivered feature manifest, derived by inspection of the code.
manifest = [
    "reports.list", "reports.detail", "metrics.bands",
    "reports.refresh", "theme.adaptive", "landing.page",
]

codebase = {"files": files, "manifest": manifest}
log: list[dict] = []  # agent condition: no keystrokes by construction

results = {}
for name, mod in [
    ("security_density", security_analyzer),
    ("complexity_mean", complexity_analyzer),
    ("duplication_pct", duplication_analyzer),
    ("hallucinations", hallucination_analyzer),
    ("correction_freq", keystroke_analyzer),
]:
    score = mod.analyze(codebase, log, spec)
    results[name] = (score.value, score.unit)

loc = sum(len(c.splitlines()) for c in files.values())
py_loc = sum(len(c.splitlines()) for f, c in files.items() if f.endswith(".py"))

print("=" * 68)
print("AUDIT — claude_code condition, spec: assurance_mobile_client v1.0.0")
print("=" * 68)
print(f"files: {len(files)}   total LOC: {loc}   python LOC: {py_loc}")
print()
print(f"{'metric':<20} {'value':>10}  unit")
print("-" * 44)
for k, (v, u) in results.items():
    print(f"{k:<20} {v:>10.2f}  {u}")

# Governance rules are not machine-checked by the five analysers; check the
# two that are mechanically checkable so the verdict is not overstated.
print()
print("GOVERNANCE (mechanical checks):")
blob = "\n".join(files.values())
import re
secretish = re.findall(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*[\"'][^\"']{8,}", blob)
print(f"  no_secrets_in_source          : {'FAIL' if secretish else 'pass'}")
hosts = set(re.findall(r"https?://([a-zA-Z0-9.\-]+)", blob))
allowed = {"auditor-dashboard-rume.fly.dev", "img.shields.io", "github.com"}
unexpected = sorted(h for h in hosts if h not in allowed)
print(f"  no_external_calls_without_allowlist : "
      f"{'review' if unexpected else 'pass'}"
      + (f"  -> {unexpected}" if unexpected else ""))

Path(tempfile.gettempdir(), "delivery_audit.json").write_text(json.dumps(
    {k: {"value": v, "unit": u} for k, (v, u) in results.items()}, indent=2))
