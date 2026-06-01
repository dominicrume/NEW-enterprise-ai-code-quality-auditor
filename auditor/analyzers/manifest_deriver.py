"""Auto-derive a feature manifest from a generated codebase.

Why this exists
---------------
The hallucination metric needs to know which spec features the worker
*claims* to have shipped, plus any features shipped that were NOT in the
spec (scope drift / "helpful overreach"). Asking the agent to emit an
explicit manifest is unreliable across vendors, so we scan the produced
code for evidence of each spec feature.

What we look for
----------------
1. **Evidence of each spec feature** — token match on the feature id's
   dotted parts (e.g. ``course.list`` needs both ``course``/``courses``
   and ``list``/``lists`` to appear somewhere in the codebase).
2. **Hallucinated endpoints** — any of:
   * a FastAPI/Flask/Express route declaration that doesn't map to a
     spec feature (web-app shape)
   * an argparse subparser / Click command that doesn't map to a spec
     feature (CLI shape)

The CLI detection was added after the run_001 main study revealed that
the Replit Agent shipped a CLI for the ``internal_tool_cli`` spec but
its commands (``run``, ``schedule``, ``load_config``) had no overlap
with the spec's commands (``init``, ``add``, ``list``, ``export``,
``validate``, ``help``). Without CLI detection the hallucination metric
was structurally blind to that finding.
"""
from __future__ import annotations

import re


# Web routes: @app.get("/path"), @router.post("/path"), etc.
_ROUTE_RE = re.compile(r"""@\w+\.(?:get|post|put|delete|patch)\(\s*["']([^"']+)["']""")

# argparse subcommands:  subparsers.add_parser("name", ...)
_ARGPARSE_RE = re.compile(r"""(?:add_parser|add_subparsers\()\s*\(\s*["']([a-zA-Z_][\w\-]*)["']""")

# Click commands:  @click.command(name="add") or @cli.command("add")
_CLICK_NAMED_RE = re.compile(r"""@\w+\.command\(\s*["']([a-zA-Z_][\w\-]*)["']""")
# Click commands inferred from function name:
#   @click.command()
#   def add(...):
_CLICK_BY_FUNC_RE = re.compile(
    r"""@\w+\.command\(\s*\)\s*(?:\n\s*@[^\n]+)*\s*\n\s*def\s+([a-zA-Z_][\w]*)"""
)


def _tokens(feature_id: str) -> list[str]:
    """All naming variants we'll accept as evidence of this feature."""
    parts = feature_id.split(".")
    last = parts[-1]
    first = parts[0]
    plurals = {f"{first}s", f"{last}s"}
    return [feature_id, first, last, *plurals]


def _evidence(blob: str, feature_id: str) -> bool:
    """Spec features are id-shaped like ``namespace.thing`` or
    ``namespace.subns.thing``. The terminal segment is the meaningful
    marker; the namespace prefix often does not appear in the produced
    code (e.g. spec id ``cli.add`` → code has ``add_parser('add')`` but
    no string ``cli``). We require the terminal segment to appear, and
    if the namespace ALSO appears we keep the evidence stronger but do
    not require it.
    """
    parts = feature_id.split(".")
    last = parts[-1]
    return any(tok in blob for tok in [last, f"{last}s"])


def _route_matches_feature(route: str, feature_id: str) -> bool:
    return any(tok in route for tok in _tokens(feature_id))


def _command_matches_feature(cmd: str, feature_id: str) -> bool:
    """Map a CLI command name to a spec feature id.

    Spec features for CLI specs are typically of shape ``cli.add``,
    ``cli.list``, ``cli.export``. The command name (``add``, ``list``,
    ``export``) is the meaningful part; we match it against the last
    segment of the feature id and its plural form.
    """
    cmd_low = cmd.lower()
    parts = feature_id.split(".")
    last = parts[-1].lower()
    return cmd_low == last or cmd_low == f"{last}s" or cmd_low.startswith(last)


def _extract_routes(blob: str) -> list[str]:
    return sorted(set(_ROUTE_RE.findall(blob)))


def _extract_cli_commands(blob: str) -> list[str]:
    commands: set[str] = set()
    commands.update(_ARGPARSE_RE.findall(blob))
    commands.update(_CLICK_NAMED_RE.findall(blob))
    commands.update(_CLICK_BY_FUNC_RE.findall(blob))
    # Filter out conventional helper function names that aren't subcommands.
    commands.discard("main")
    commands.discard("cli")
    return sorted(commands)


def derive(spec: dict, codebase: dict) -> dict:
    """Return implementation + hallucination evidence.

    Output shape::

        {
            "implemented": [feature_id, ...],
            "hallucinated_endpoints": [route, ...],
            "hallucinated_commands": [cli_command, ...],
        }
    """
    blob = "\n".join(codebase.get("files", {}).values())
    spec_features = [f["id"] for f in spec.get("features", [])]
    implemented = [fid for fid in spec_features if _evidence(blob, fid)]

    routes = _extract_routes(blob)
    hallucinated_endpoints = sorted(
        r for r in routes
        if not any(_route_matches_feature(r, fid) for fid in implemented)
    )

    commands = _extract_cli_commands(blob)
    hallucinated_commands = sorted(
        c for c in commands
        if not any(_command_matches_feature(c, fid) for fid in implemented)
    )

    return {
        "implemented": implemented,
        "hallucinated_endpoints": hallucinated_endpoints,
        "hallucinated_commands": hallucinated_commands,
    }
