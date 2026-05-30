"""Hallucination: features in the manifest but NOT in the spec."""
from auditor.models.audit_result import MetricScore


def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore:
    spec_features = {f["id"] for f in spec.get("features", [])}
    manifest = set(codebase.get("manifest", []))
    hallucinated = manifest - spec_features
    return MetricScore(name="hallucinations", value=float(len(hallucinated)), unit="count")
