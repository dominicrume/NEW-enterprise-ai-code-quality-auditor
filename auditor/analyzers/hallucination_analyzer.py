"""Hallucination: features in the produced code that are NOT in the spec.

Two paths:
  1. If ``codebase["manifest"]`` is non-empty, trust it (the human_control
     adapter declares this by hand): hallucinations = |manifest - spec|.
  2. Otherwise auto-derive from the code itself (manifest_deriver) and
     count detected endpoints that do not map to any spec feature. This
     unblocks the metric for agentic adapters that do not emit a manifest.
"""
from auditor.analyzers.manifest_deriver import derive
from auditor.models.audit_result import MetricScore


def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore:
    spec_ids = {f["id"] for f in spec.get("features", [])}
    manifest = set(codebase.get("manifest", []))

    if manifest:
        count = len(manifest - spec_ids)
    else:
        d = derive(spec, codebase)
        count = len(d["hallucinated_endpoints"]) + len(d.get("hallucinated_commands", []))

    return MetricScore(name="hallucinations", value=float(count), unit="count")
