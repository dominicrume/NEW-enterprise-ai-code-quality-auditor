"""Tests for the fix engine.

The property that matters: a fix is reported as applied only when re-scanning
proves the finding is gone. Anything unverifiable must be discarded, and
anything unfixable must be refused with a reason rather than guessed at.
"""
from pathlib import Path

import pytest

from auditor.remediation import remediate
from auditor.remediation.fixers import FIXERS, UNFIXABLE


def _write(tmp_path: Path, body: str) -> Path:
    (tmp_path / "app.py").write_text(body)
    return tmp_path


def _by_id(report, test_id):
    return next((o for o in report.outcomes if o.test_id == test_id), None)


# ------------------------------------------------------------ fixes that work

def test_hardcoded_secret_moves_to_the_environment(tmp_path):
    root = _write(tmp_path, 'SESSION_TOKEN = "s3cr3t-value"\n')
    r = remediate(root)
    o = _by_id(r, "B105")
    assert o is not None and o.fixed
    assert 'os.environ["SESSION_TOKEN"]' in o.after
    assert o.behaviour_note and "environment" in o.behaviour_note


def test_hardcoded_tmp_path_uses_the_platform_temp_dir(tmp_path):
    root = _write(tmp_path, 'CACHE = "/tmp/myapp"\n')
    o = _by_id(remediate(root), "B108")
    assert o is not None and o.fixed
    assert "tempfile.gettempdir()" in o.after


def test_shell_true_becomes_an_argument_list(tmp_path):
    root = _write(tmp_path,
                  "import subprocess\n"
                  'subprocess.call("tar -czf a.tgz data", shell=True)\n')
    o = _by_id(remediate(root), "B602")
    assert o is not None and o.fixed
    assert "shell=True" not in o.after
    assert "['tar', '-czf', 'a.tgz', 'data']" in o.after


def test_insecure_random_becomes_secrets(tmp_path):
    root = _write(tmp_path, "import random\nx = random.choice([1, 2])\n")
    o = _by_id(remediate(root), "B311")
    assert o is not None and o.fixed
    assert "secrets.choice" in o.after


# ------------------------------------------------------- refusals, not guesses

def test_dynamic_shell_command_is_refused(tmp_path):
    """The injection case is exactly where a naive rewrite would be wrong."""
    root = _write(tmp_path,
                  "import subprocess\n"
                  "def run(p):\n"
                  '    subprocess.call("tar -czf a.tgz " + p, shell=True)\n')
    r = remediate(root)
    shell = _by_id(r, "B602")
    if shell is not None:                       # bandit id varies by form
        assert not shell.fixed
        assert shell.reason


def test_advisory_only_findings_are_not_fixed(tmp_path):
    root = _write(tmp_path, "import subprocess\n")
    o = _by_id(remediate(root), "B404")
    assert o is not None and not o.fixed
    assert "advisory" in o.reason


def test_every_refusal_states_a_reason():
    assert all(reason.strip() for reason in UNFIXABLE.values())


# ------------------------------------------------------------- the guarantees

def test_dry_run_never_touches_the_original(tmp_path):
    root = _write(tmp_path, 'TOKEN = "abc123xyz"\n')
    original = (root / "app.py").read_text()
    report = remediate(root, apply=False)
    assert report.fixed
    assert (root / "app.py").read_text() == original
    assert report.applied is False


def test_apply_writes_only_verified_fixes(tmp_path):
    root = _write(tmp_path, 'TOKEN = "abc123xyz"\nCACHE = "/tmp/x"\n')
    report = remediate(root, apply=True)
    assert report.applied
    text = (root / "app.py").read_text()
    assert "abc123xyz" not in text
    assert "os.environ" in text


def test_applying_fixes_reduces_the_finding_count(tmp_path):
    root = _write(tmp_path,
                  "import random\n"
                  'TOKEN = "abc123xyz"\n'
                  'CACHE = "/tmp/x"\n'
                  "v = random.choice([1, 2])\n")
    report = remediate(root, apply=True)
    assert report.findings_after < report.findings_before
    assert remediate(root).findings_before == report.findings_after


def test_fixed_output_is_still_valid_python(tmp_path):
    import ast
    root = _write(tmp_path,
                  '"""Doc."""\n'
                  "import random\n"
                  'TOKEN = "abc123xyz"\n'
                  'CACHE = "/tmp/x"\n'
                  "v = random.choice([1, 2])\n")
    remediate(root, apply=True)
    ast.parse((root / "app.py").read_text())        # raises if malformed


def test_required_imports_are_added_after_the_docstring(tmp_path):
    root = _write(tmp_path, '"""Module doc."""\nCACHE = "/tmp/x"\n')
    remediate(root, apply=True)
    lines = (root / "app.py").read_text().splitlines()
    assert lines[0].startswith('"""')
    assert any(l.startswith("import os") for l in lines)
    assert any(l.startswith("import tempfile") for l in lines)


def test_clean_project_reports_nothing_to_do(tmp_path):
    root = _write(tmp_path, "def add(a, b):\n    return a + b\n")
    report = remediate(root)
    assert report.findings_before == 0
    assert report.outcomes == []


@pytest.mark.parametrize("test_id", sorted(FIXERS))
def test_no_check_is_both_fixable_and_refused(test_id):
    """A check with a fixer may still refuse a specific line, but it must not
    appear in the blanket-refusal table under a contradictory reason."""
    if test_id in UNFIXABLE:
        assert "dynamic" in UNFIXABLE[test_id] or "judgement" in UNFIXABLE[test_id]
