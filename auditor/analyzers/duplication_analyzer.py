"""Code duplication — k-line shingle detection.

See docs/METRICS.md: % of source lines appearing inside a duplicated
6-line shingle (whitespace-normalised, blank lines removed). Language
agnostic, no external tool required.
"""
from __future__ import annotations

from collections import defaultdict

from auditor.models.audit_result import MetricScore

SHINGLE_K = 6


def _normalise(content: str) -> list[tuple[int, str]]:
    """Return [(original_index, stripped_line), ...] for non-blank lines."""
    out: list[tuple[int, str]] = []
    for idx, raw in enumerate(content.splitlines()):
        s = " ".join(raw.split())  # collapse all whitespace runs
        if s:
            out.append((idx, s))
    return out


def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore:
    # File -> list of (line_index, normalised_line)
    per_file: dict[str, list[tuple[int, str]]] = {
        path: _normalise(content) for path, content in codebase.get("files", {}).items()
    }
    total_lines = sum(len(v) for v in per_file.values())
    if total_lines == 0:
        return MetricScore(name="duplication_pct", value=0.0, unit="%")

    # Build a global shingle index: tuple_of_lines -> list of (file, start_idx)
    shingles: dict[tuple[str, ...], list[tuple[str, int]]] = defaultdict(list)
    for path, norm in per_file.items():
        if len(norm) < SHINGLE_K:
            continue
        for i in range(len(norm) - SHINGLE_K + 1):
            key = tuple(line for _, line in norm[i:i + SHINGLE_K])
            shingles[key].append((path, i))

    # Mark every line that participates in a shingle with >=2 occurrences.
    duplicated: set[tuple[str, int]] = set()
    for key, occurrences in shingles.items():
        if len(occurrences) < 2:
            continue
        for path, start in occurrences:
            norm = per_file[path]
            for offset in range(SHINGLE_K):
                duplicated.add((path, norm[start + offset][0]))

    pct = 100.0 * len(duplicated) / total_lines
    return MetricScore(name="duplication_pct", value=pct, unit="%")
