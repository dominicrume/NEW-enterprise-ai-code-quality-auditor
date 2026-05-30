"""Auto-derive a feature manifest from a generated codebase.

Background: the hallucination metric needs to know which spec features the
worker *claims* to have shipped. Asking the agent to emit a manifest is
unreliable across vendors. Instead, we scan the produced code for evidence
of each spec feature and report two things:

  - implemented_ids : spec features whose marker IS found in the code
  - hallucinated_endpoints : route paths in the code that are NOT covered
    by any spec feature marker (likely scope drift)

For the pilot, "evidence" is a substring search of the code for either:
  * the feature id itself (e.g. ``auth.login``)
  * the id's last segment as a path (e.g. ``/login``)
  * the id's last segment as an identifier (e.g. ``def login``,
    ``register(``)

This is a heuristic, documented as a pilot limitation in METHODOLOGY.md.
For production we recommend forcing each adapter to emit an explicit
manifest as part of its capture contract.
"""
from __future__ import annotations

import re


_ROUTE_RE = re.compile(r"""@\w+\.(?:get|post|put|delete|patch)\(\s*["']([^"']+)["']""")


def _tokens(feature_id: str) -> list[str]:
    """All naming variants we'll accept as evidence of this feature.

    For ``course.list`` we accept: ``course.list``, ``course``, ``courses``,
    ``list``, ``/course``, ``/courses``, ``def list_courses``, etc.
    """
    parts = feature_id.split(".")
    last = parts[-1]
    first = parts[0]
    plurals = {f"{first}s", f"{last}s"}
    return [feature_id, first, last, *plurals]


def _evidence(blob: str, feature_id: str) -> bool:
    parts = feature_id.split(".")
    return all(any(tok in blob for tok in [p, f"{p}s"]) for p in parts)


def _route_matches_feature(route: str, feature_id: str) -> bool:
    return any(tok in route for tok in _tokens(feature_id))


def derive(spec: dict, codebase: dict) -> dict:
    """Return ``{implemented: [...], hallucinated_endpoints: [...]}``."""
    blob = "\n".join(codebase.get("files", {}).values())
    spec_features = [f["id"] for f in spec.get("features", [])]
    implemented = [fid for fid in spec_features if _evidence(blob, fid)]
    routes = set(_ROUTE_RE.findall(blob))
    hallucinated = sorted(
        r for r in routes
        if not any(_route_matches_feature(r, fid) for fid in implemented)
    )
    return {"implemented": implemented, "hallucinated_endpoints": hallucinated}
