"""Decision thresholds for every metric — the single source of truth.

The bands are interpretation *policy*, not measurement. They are declared
once here so the CLI, the dashboard and the mobile client cannot drift
apart and tell a user three different stories about the same number.

Semantics: lower is better for every metric.
  value <  warning   -> "good"
  value <  critical  -> "warn"
  otherwise          -> "critical"
"""
from __future__ import annotations

from typing import Literal

Band = Literal["good", "warn", "critical"]

BANDS: dict[str, dict[str, float]] = {
    "security_density": {"ideal": 0.0, "warning": 50.0, "critical": 100.0},
    "complexity_mean":  {"ideal": 0.0, "warning": 3.0,  "critical": 6.0},
    "duplication_pct":  {"ideal": 0.0, "warning": 5.0,  "critical": 10.0},
    "hallucinations":   {"ideal": 0.0, "warning": 1.0,  "critical": 3.0},
    "correction_freq":  {"ideal": 0.0, "warning": 10.0, "critical": 25.0},
}


def band_for(metric: str, value: float) -> Band:
    """Classify ``value`` against ``metric``'s thresholds."""
    limits = BANDS.get(metric)
    if limits is None:
        return "good"
    if value >= limits["critical"]:
        return "critical"
    if value >= limits["warning"]:
        return "warn"
    return "good"
