"""Deterministic fixers for specific, well-understood findings.

Every fixer is conservative by construction:

* it edits only the line the finding points at;
* it re-reads that line and returns ``None`` if the expected pattern is not
  there, rather than guessing;
* it never rewrites a construct whose behaviour it cannot preserve.

A deliberate omission: findings whose correct fix depends on intent the code
does not contain — a partial executable path, a subprocess call with a
dynamically built command — have no fixer. Reporting "cannot fix safely, and
here is why" is more useful than a plausible edit that changes what the
program does.
"""
from __future__ import annotations
import os
import tempfile

import re
import shlex
from dataclasses import dataclass
from typing import Callable

Lines = list[str]


@dataclass
class Proposal:
    """One concrete edit, ready to be applied and then verified."""
    test_id: str
    line_number: int
    before: str
    after: str
    explanation: str
    needs_imports: tuple[str, ...] = ()
    behaviour_note: str | None = None      # stated when behaviour changes


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _env_name(var: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", var.upper()).strip("_") or "SECRET"


# --------------------------------------------------------------- B105/6/7
_ASSIGN_SECRET = re.compile(
    r'^(?P<lead>\s*)(?P<var>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*'
    r'(?P<q>["\'])(?P<val>(?:(?!(?P=q)).)*)(?P=q)\s*(?P<tail>#.*)?$'
)


def fix_hardcoded_secret(lines: Lines, ln: int, test_id: str) -> Proposal | None:
    """`TOKEN = "literal"` -> read it from the environment instead."""
    line = lines[ln - 1]
    m = _ASSIGN_SECRET.match(line.rstrip("\n"))
    if not m:
        return None
    var, env = m.group("var"), _env_name(m.group("var"))
    after = f'{m.group("lead")}{var} = os.environ["{env}"]\n'
    return Proposal(
        test_id=test_id, line_number=ln, before=line, after=after,
        explanation=f"read {var} from the {env} environment variable "
                    f"instead of embedding it in source",
        needs_imports=("os",),
        behaviour_note=f"{env} must be set in the environment, or the program "
                       f"will raise KeyError at import",
    )


# ------------------------------------------------------------------- B108
_TMP_LITERAL = re.compile(r'(["\'])(/tmp/(?:(?!\1).)*)\1')


def fix_hardcoded_tmp(lines: Lines, ln: int, test_id: str) -> Proposal | None:
    """A literal `/tmp/...` path -> the platform's temp directory."""
    line = lines[ln - 1]
    m = _TMP_LITERAL.search(line)
    if not m:
        return None
    tail = m.group(2)[len(os.path.join(tempfile.gettempdir(), "")):]
    replacement = f'os.path.join(tempfile.gettempdir(), "{tail}")'
    return Proposal(
        test_id=test_id, line_number=ln, before=line,
        after=line[: m.start()] + replacement + line[m.end():],
        explanation="use the platform temp directory rather than a hardcoded "
                    "/tmp path, which is world-writable and predictable",
        needs_imports=("os", "tempfile"),
    )


# ------------------------------------------------------------------- B110
_EXCEPT_PASS = re.compile(r'^(?P<lead>\s*)pass\s*(?:#.*)?$')


def fix_try_except_pass(lines: Lines, ln: int, test_id: str) -> Proposal | None:
    """A silent `except: pass` -> record why it was ignored."""
    line = lines[ln - 1]
    m = _EXCEPT_PASS.match(line.rstrip("\n"))
    if not m:
        return None
    lead = m.group("lead")
    after = (f'{lead}logging.debug("suppressed exception", exc_info=True)\n')
    return Proposal(
        test_id=test_id, line_number=ln, before=line, after=after,
        explanation="record the suppressed exception instead of discarding it "
                    "silently, so the failure is diagnosable",
        needs_imports=("logging",),
    )


# ------------------------------------------------------------------- B311
def fix_insecure_random(lines: Lines, ln: int, test_id: str) -> Proposal | None:
    """`random.*` used where unpredictability matters -> `secrets`."""
    line = lines[ln - 1]
    if "random.randint(" in line:
        after = re.sub(r"random\.randint\(\s*0\s*,\s*([^)]+)\)",
                       r"secrets.randbelow(\1 + 1)", line)
    elif "random.choice(" in line:
        after = line.replace("random.choice(", "secrets.choice(")
    elif "random.random()" in line:
        after = line.replace("random.random()", "secrets.randbits(53) / (1 << 53)")
    else:
        return None
    if after == line:
        return None
    return Proposal(
        test_id=test_id, line_number=ln, before=line, after=after,
        explanation="use the cryptographically secure `secrets` module in "
                    "place of `random`, which is predictable from its seed",
        needs_imports=("secrets",),
    )


# --------------------------------------------------------- B602 / B605
_SHELL_CALL = re.compile(
    r'(?P<head>subprocess\.(?:call|run|check_call|check_output|Popen)\(\s*)'
    r'(?P<q>["\'])(?P<cmd>(?:(?!(?P=q)).)*)(?P=q)'
    r'(?P<mid>\s*,\s*)shell\s*=\s*True'
)


def fix_shell_true(lines: Lines, ln: int, test_id: str) -> Proposal | None:
    """`shell=True` with a *literal* command -> an argument list.

    Only a fully literal command is converted. If the command is built from a
    variable, an f-string or concatenation — which is exactly the injection
    case — no fix is proposed, because the safe rewrite depends on which parts
    are meant to be data.
    """
    line = lines[ln - 1]
    m = _SHELL_CALL.search(line)
    if not m:
        return None
    cmd = m.group("cmd")
    if any(t in cmd for t in ("{", "%", "+")):
        return None                       # dynamic — refuse, see docstring
    try:
        argv = shlex.split(cmd)
    except ValueError:
        return None
    if not argv:
        return None
    after = line[: m.start()] + m.group("head") + repr(argv) + line[m.end():]
    after = after.replace(", shell=True", "").replace(",shell=True", "")
    return Proposal(
        test_id=test_id, line_number=ln, before=line, after=after,
        explanation="pass the command as a list so it is executed directly "
                    "rather than through a shell, removing the injection path",
    )


# Findings deliberately left alone, with the reason shown to the user.
UNFIXABLE: dict[str, str] = {
    "B404": "advisory only — importing subprocess is not itself a defect",
    "B603": "needs human judgement: whether the input is trusted is not "
            "visible in the code",
    "B607": "needs the absolute path for this machine, which the source "
            "does not contain",
    "B602": "command is built dynamically — the safe rewrite depends on which "
            "parts are data",
    "B605": "command is built dynamically — the safe rewrite depends on which "
            "parts are data",
}

FIXERS: dict[str, Callable[[Lines, int, str], Proposal | None]] = {
    "B105": fix_hardcoded_secret,
    "B106": fix_hardcoded_secret,
    "B107": fix_hardcoded_secret,
    "B108": fix_hardcoded_tmp,
    "B110": fix_try_except_pass,
    "B311": fix_insecure_random,
    "B602": fix_shell_true,
    "B605": fix_shell_true,
}
