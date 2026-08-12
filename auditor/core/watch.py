"""Continuous audit — re-score a directory as it changes.

``scan`` answers "what is the state of this code?". ``watch`` answers the
question that actually matters while an agent is working: *what did that
change do to it?* Drift is visible as it happens rather than discovered
afterwards.

Change detection is by polling file mtime and size. This is deliberate:
a filesystem-event library would add a dependency and platform-specific
behaviour to save a stat() sweep that costs milliseconds on any codebase
this instrument is meant for.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from auditor.adapters._shared import iter_source_files
from auditor.core.calibration import Band
from auditor.core.scan import ScanResult, scan_directory

Fingerprint = dict[str, tuple[float, int]]


@dataclass
class MetricDelta:
    """How one metric moved between two consecutive audits."""
    name: str
    label: str
    before: float | None
    after: float | None
    before_band: Band | None
    after_band: Band | None

    @property
    def became_measurable(self) -> bool:
        """A metric that could not be computed now can — e.g. the first
        Python file appeared, bringing security and complexity online."""
        return self.before is None and self.after is not None

    @property
    def became_unmeasurable(self) -> bool:
        return self.before is not None and self.after is None

    @property
    def changed_band(self) -> bool:
        return (self.before_band is not None and self.after_band is not None
                and self.before_band != self.after_band)

    @property
    def direction(self) -> str:
        if self.before is None or self.after is None:
            return ""
        if self.after > self.before:
            return "worse"      # every metric is lower-is-better
        if self.after < self.before:
            return "better"
        return ""


@dataclass
class WatchEvent:
    """One re-audit triggered by a filesystem change."""
    changed_files: list[str]
    result: ScanResult
    deltas: list[MetricDelta]

    @property
    def notable(self) -> bool:
        """Worth interrupting a human for."""
        return any(d.changed_band or d.became_measurable or d.became_unmeasurable
                   for d in self.deltas)


def fingerprint(path: Path) -> Fingerprint:
    """Cheap change signature for every scorable file under ``path``."""
    out: Fingerprint = {}
    for rel, abs_path in iter_source_files(path):
        try:
            st = abs_path.stat()
        except OSError:
            continue  # deleted between walk and stat
        out[rel] = (st.st_mtime, st.st_size)
    return out


def changed_files(old: Fingerprint, new: Fingerprint) -> list[str]:
    """Files added, removed, or modified between two fingerprints."""
    return sorted(set(old) ^ set(new) | {k for k in set(old) & set(new) if old[k] != new[k]})


def diff_results(old: ScanResult, new: ScanResult) -> list[MetricDelta]:
    """Per-metric movement between two audits, changes only."""
    before = {o.name: o for o in old.outcomes}
    deltas: list[MetricDelta] = []
    for outcome in new.outcomes:
        prior = before.get(outcome.name)
        if prior is None:
            continue
        if prior.value == outcome.value and prior.band == outcome.band:
            continue
        deltas.append(MetricDelta(
            name=outcome.name, label=outcome.label,
            before=prior.value, after=outcome.value,
            before_band=prior.band, after_band=outcome.band,
        ))
    return deltas


def watch_directory(
    path: Path,
    spec: dict | None = None,
    interval: float = 1.0,
    settle: float = 0.6,
    stop: Callable[[], bool] | None = None,
) -> Iterator[WatchEvent]:
    """Yield a :class:`WatchEvent` each time ``path`` changes and is re-audited.

    ``settle`` waits for writes to stop before re-auditing, so an agent
    writing twelve files produces one audit rather than twelve.
    """
    path = Path(path).resolve()
    previous_result = scan_directory(path, spec)
    previous_print = fingerprint(path)

    while not (stop and stop()):
        time.sleep(interval)
        current = fingerprint(path)
        touched = changed_files(previous_print, current)
        if not touched:
            continue

        # Let a burst of writes finish before scoring it.
        while True:
            time.sleep(settle)
            settled = fingerprint(path)
            if settled == current:
                break
            current = settled
            touched = changed_files(previous_print, current)

        result = scan_directory(path, spec)
        yield WatchEvent(
            changed_files=touched,
            result=result,
            deltas=diff_results(previous_result, result),
        )
        previous_result, previous_print = result, current
