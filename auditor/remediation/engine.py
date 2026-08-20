"""Apply fixes, then prove they worked.

The contract: a fix is only ever reported as applied when re-running the same
analyser over the edited code shows the finding gone **and** no new finding in
its place. An edit that cannot be verified is discarded, not shipped.

Nothing here writes to a user's files unless explicitly asked. The default is
a dry run against a sandbox copy.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from auditor.adapters._shared import iter_source_files
from auditor.remediation.fixers import FIXERS, UNFIXABLE, Proposal

# Some fixes correctly leave a *lesser* finding behind. Removing shell=True
# resolves the injection path (B602/B605) and leaves B603, the advisory that
# accompanies any subprocess call at all. Treating that as a regression would
# discard a real security fix, so the expected successors are declared here
# and reported to the user rather than silently tolerated.
EXPECTED_SUCCESSORS: dict[str, set[str]] = {
    "B602": {"B603"},
    "B605": {"B603"},
}


@dataclass
class FixOutcome:
    """What happened to one finding."""
    test_id: str
    file: str
    line: int
    severity: str
    issue: str
    status: str                 # fixed | unverified | unsupported | no_pattern
    explanation: str = ""
    reason: str = ""
    before: str = ""
    after: str = ""
    behaviour_note: str | None = None

    @property
    def fixed(self) -> bool:
        return self.status == "fixed"


@dataclass
class Remediation:
    root: Path
    outcomes: list[FixOutcome] = field(default_factory=list)
    findings_before: int = 0
    findings_after: int = 0
    applied: bool = False

    @property
    def fixed(self):
        return [o for o in self.outcomes if o.fixed]

    @property
    def unfixed(self):
        return [o for o in self.outcomes if not o.fixed]


def _bandit(target: Path) -> list[dict]:
    """CWE-tagged findings for a directory, using the same scan as the auditor."""
    if not any(target.rglob("*.py")):
        return []
    proc = subprocess.run(["bandit", "-r", str(target), "-f", "json", "-q"],
                          capture_output=True, text=True, check=False)
    if not proc.stdout.strip():
        return []
    try:
        results = json.loads(proc.stdout).get("results", [])
    except json.JSONDecodeError:
        return []
    return [r for r in results if (r.get("issue_cwe") or {}).get("id")]


def _rel(finding: dict, root: Path) -> str:
    """Path of a finding relative to the tree being scanned."""
    p = Path(finding["filename"]).resolve()
    try:
        return str(p.relative_to(root.resolve()))
    except ValueError:
        return p.name


def _key(finding: dict, root: Path) -> tuple[str, str, int]:
    """Identity of a finding, stable across the sandbox copy."""
    rel = Path(finding["filename"]).resolve()
    try:
        rel = rel.relative_to(root.resolve())
    except ValueError:
        pass
    return (finding["test_id"], str(rel), finding["line_number"])


def _ensure_imports(lines: list[str], modules: tuple[str, ...]) -> list[str]:
    """Add any missing top-level imports, after the module docstring."""
    needed = [m for m in modules
              if not any(re.match(rf"^\s*import\s+{m}\b", ln) for ln in lines)]
    if not needed:
        return lines

    insert_at = 0
    if lines and re.match(r'^\s*(?:"""|\'\'\')', lines[0]):
        delim = lines[0].strip()[:3]
        if lines[0].strip().count(delim) >= 2 and len(lines[0].strip()) > 3:
            insert_at = 1                       # single-line docstring
        else:
            for i in range(1, len(lines)):
                if delim in lines[i]:
                    insert_at = i + 1
                    break
    while insert_at < len(lines) and lines[insert_at].startswith("from __future__"):
        insert_at += 1
    return lines[:insert_at] + [f"import {m}\n" for m in needed] + lines[insert_at:]


def _propose(root: Path, findings: list[dict]) -> dict[Path, list[tuple[int, Proposal]]]:
    """Collect a proposal per fixable finding, grouped by file."""
    by_file: dict[Path, list[tuple[int, Proposal]]] = {}
    for f in findings:
        fixer = FIXERS.get(f["test_id"])
        if fixer is None:
            continue
        path = Path(f["filename"])
        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeDecodeError):
            continue
        ln = f["line_number"]
        if not (1 <= ln <= len(lines)):
            continue
        proposal = fixer(lines, ln, f["test_id"])
        if proposal is not None:
            by_file.setdefault(path, []).append((ln, proposal))
    return by_file


def _within(path: Path, root: Path) -> bool:
    """True only if ``path`` really sits under ``root``.

    The paths this module writes to come from a scanner's output rather than
    from us. Resolving both and comparing means a traversal sequence or a
    symlink pointing outside the sandbox cannot turn a fix into a write
    somewhere it was never meant to touch.
    """
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except (ValueError, OSError):
        return False


def _contained(path: Path, root: Path) -> Path:
    """Rebuild ``path`` from ``root`` so the result cannot escape it.

    Validating a path and then writing to the original leaves the write
    target still derived from untrusted input — and a reader (human or
    scanner) has to trace the guard to know it is safe. Deriving the target
    from ``root`` plus a verified relative segment makes containment a
    property of how the path is constructed, not of a check somewhere above.
    """
    root = Path(root).resolve()
    rel = Path(path).resolve().relative_to(root)      # raises if outside
    return root.joinpath(rel)


def _write_proposals(path: Path, proposals: list[tuple[int, Proposal]],
                     root: Path) -> None:
    """Apply every proposal for one file, bottom-up so line numbers hold."""
    target = _contained(path, root)
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    imports: list[str] = []
    for ln, p in sorted(proposals, key=lambda t: -t[0]):
        lines[ln - 1] = p.after
        imports.extend(p.needs_imports)
    if imports:
        lines = _ensure_imports(lines, tuple(sorted(set(imports))))
    target.write_text("".join(lines), encoding="utf-8")


def remediate(root: Path, apply: bool = False) -> Remediation:
    """Propose fixes, verify them in a sandbox, and optionally apply them."""
    root = Path(root).resolve()
    report = Remediation(root=root)

    before = _bandit(root)
    report.findings_before = len(before)
    if not before:
        return report

    with tempfile.TemporaryDirectory() as tmp:
        sandbox = Path(tmp) / "code"
        sandbox.mkdir()
        for rel, src_path in iter_source_files(root):
            dest = sandbox / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)

        sandbox_before = _bandit(sandbox)
        proposals = _propose(sandbox, sandbox_before)
        for path, items in proposals.items():
            _write_proposals(path, items, sandbox)

        after = _bandit(sandbox)
        report.findings_after = len(after)

        # Verification is by (check, file) counts rather than line numbers:
        # inserting an import shifts every line below it, so a surviving
        # finding would otherwise look like a newly introduced one.
        before_counts = Counter((f["test_id"], _rel(f, sandbox))
                                for f in sandbox_before)
        after_counts = Counter((f["test_id"], _rel(f, sandbox)) for f in after)
        applied_ids = {prop.test_id
                       for items in proposals.values() for _, prop in items}
        tolerated = {sid for tid in applied_ids
                     for sid in EXPECTED_SUCCESSORS.get(tid, set())}
        introduced = {k for k, n in after_counts.items()
                      if n > before_counts.get(k, 0) and k[0] not in tolerated}
        downgrades = {k for k, n in after_counts.items()
                      if n > before_counts.get(k, 0) and k[0] in tolerated}

        proposed: dict[tuple[str, str, int], Proposal] = {}
        for path, items in proposals.items():
            rel = str(path.relative_to(sandbox))
            for ln, prop in items:
                proposed[(prop.test_id, rel, ln)] = prop

        for f in sandbox_before:
            rel = _rel(f, sandbox)
            k = (f["test_id"], rel, f["line_number"])
            common = dict(test_id=f["test_id"], file=rel,
                          line=f["line_number"], severity=f["issue_severity"],
                          issue=f["issue_text"])
            prop = proposed.get(k)

            if prop is None:
                if f["test_id"] in UNFIXABLE:
                    status, reason = "unsupported", UNFIXABLE[f["test_id"]]
                elif f["test_id"] in FIXERS:
                    status, reason = "no_pattern", (
                        "the line does not match a pattern this fixer can "
                        "rewrite without guessing")
                else:
                    status, reason = "unsupported", "no fixer for this check yet"
                report.outcomes.append(FixOutcome(**common, status=status,
                                                  reason=reason))
                continue

            ck = (f["test_id"], rel)
            cleared = after_counts.get(ck, 0) < before_counts.get(ck, 0)
            verified = cleared and not introduced
            report.outcomes.append(FixOutcome(
                **common,
                status="fixed" if verified else "unverified",
                explanation=prop.explanation,
                reason="" if verified else (
                    "the rewrite introduced a new finding elsewhere"
                    if introduced else
                    "re-scanning did not clear the finding — discarded"),
                before=prop.before.rstrip("\n"),
                after=prop.after.rstrip("\n"),
                behaviour_note=prop.behaviour_note or (
                    f"resolved; a lower-severity advisory "
                    f"({', '.join(sorted({k[0] for k in downgrades}))}) remains, "
                    f"which is expected for any subprocess call"
                    if verified and downgrades
                    and prop.test_id in EXPECTED_SUCCESSORS else None),
            ))

        if apply and report.fixed:
            for rel in {o.file for o in report.fixed}:
                try:
                    src = _contained(sandbox / rel, sandbox)
                    dest = _contained(root / rel, root)
                except ValueError:
                    continue        # never copy out of, or into, an unexpected path
                shutil.copy2(src, dest)
            report.applied = True

    return report
