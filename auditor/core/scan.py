"""Zero-ceremony audit of any directory.

The experiment path (``auditor run`` / ``auditor experiment``) exists to
serve a controlled study: fixed spec, isolated workspace, one condition per
capture. That rigour is right for the dissertation and wrong as a front
door — it forces a user to decide, before writing a line, that this folder
is The Session.

``scan`` inverts that. Point it at a directory that already exists, however
the code got there, and it reports what it can actually measure.

The design rule that matters: **a metric is reported only where it applies.**
Bandit and radon read Python; on a TypeScript project they will happily
return 0.00, and printing that as a score would be a lie of exactly the kind
this instrument exists to catch. Inapplicable metrics are reported as
``n/a`` with the reason, never as a zero.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from auditor.adapters._shared import load_codebase
from auditor.analyzers import (
    complexity_analyzer,
    duplication_analyzer,
    hallucination_analyzer,
    security_analyzer,
)
from auditor.core.calibration import Band, band_for


@dataclass
class MetricOutcome:
    """One metric's result, or the reason it could not be computed."""
    name: str
    label: str
    value: float | None = None
    unit: str = ""
    band: Band | None = None
    skipped_reason: str | None = None

    @property
    def applicable(self) -> bool:
        return self.skipped_reason is None


@dataclass
class ScanResult:
    path: Path
    file_count: int = 0
    total_loc: int = 0
    python_files: int = 0
    python_loc: int = 0
    spec_name: str | None = None
    outcomes: list[MetricOutcome] = field(default_factory=list)

    @property
    def worst_band(self) -> Band:
        order = {"good": 0, "warn": 1, "critical": 2}
        bands = [o.band for o in self.outcomes if o.band]
        return max(bands, key=lambda b: order[b]) if bands else "good"

    @property
    def coverage_note(self) -> str | None:
        """A plain-language warning when whole metric families were skipped."""
        if self.file_count and not self.python_files:
            return (
                "No Python files found. Security and complexity are Python-only "
                "and were not measured — this is a coverage gap, not a clean result."
            )
        return None


# label, analyser, and the predicate that decides whether it can run at all
_METRICS = [
    ("security_density", "Security", security_analyzer),
    ("complexity_mean", "Complexity", complexity_analyzer),
    ("duplication_pct", "Duplication", duplication_analyzer),
    ("hallucinations", "Scope drift", hallucination_analyzer),
]


def scan_directory(path: Path, spec: dict | None = None) -> ScanResult:
    """Audit ``path`` in place. No session, no capture, no cleanup."""
    path = Path(path).resolve()
    codebase = load_codebase(path)
    files = codebase.get("files", {})

    result = ScanResult(
        path=path,
        file_count=len(files),
        total_loc=sum(len(c.splitlines()) for c in files.values()),
        python_files=sum(1 for f in files if f.endswith(".py")),
        python_loc=sum(len(c.splitlines()) for f, c in files.items() if f.endswith(".py")),
        spec_name=(spec or {}).get("name"),
    )

    for name, label, module in _METRICS:
        reason = _skip_reason(name, result, spec)
        if reason:
            result.outcomes.append(MetricOutcome(name=name, label=label, skipped_reason=reason))
            continue
        score = module.analyze(codebase, [], spec or {})
        result.outcomes.append(MetricOutcome(
            name=name, label=label, value=score.value, unit=score.unit,
            band=band_for(name, score.value),
        ))

    # correction_freq counts backspaces per thousand keystrokes, so it needs an
    # interaction log captured while the code was being written. A directory has
    # no such thing and never will: scan reads what was produced, not how.
    #
    # The hint used to name `auditor session`, which is not a command -- a user
    # following it got "Error: No such command". Only the adapters produce an
    # interaction log, from a captures directory, so point at the command that
    # reads them.
    result.outcomes.append(MetricOutcome(
        name="correction_freq", label="Rework",
        skipped_reason="not measurable from a directory; needs a captured "
                       "session (auditor run --workflow ...)",
    ))
    return result


def _skip_reason(metric: str, r: ScanResult, spec: dict | None) -> str | None:
    if r.file_count == 0:
        return "no analysable files found"
    if metric in ("security_density", "complexity_mean") and r.python_files == 0:
        return "no Python files (analyser is Python-only)"
    if metric == "hallucinations" and not spec:
        return "needs --spec to know what was asked for"
    return None
