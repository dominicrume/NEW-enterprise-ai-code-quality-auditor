"""Human-control adapter — loads a real captured session from disk."""
import json
from pathlib import Path

import pytest

from auditor.adapters.human_control_adapter import HumanControlAdapter


FIXTURE = Path(__file__).parent / "fixtures" / "human_control"


def test_loads_codebase_and_log_and_persists(tmp_path, minimal_spec):
    adapter = HumanControlAdapter(
        code_dir=FIXTURE / "code",
        log_path=FIXTURE / "session.json",
        run_id="test_run_001",
        raw_root=tmp_path,
    )

    codebase, log = adapter.generate(minimal_spec)

    # Codebase shape
    assert "app/auth.py" in codebase["files"]
    assert "def login" in codebase["files"]["app/auth.py"]
    assert codebase["manifest"] == ["auth.login", "auth.register"]

    # Log shape + capture contract
    assert isinstance(log, list) and len(log) == 15
    assert {e["type"] for e in log} <= {"keystroke", "backspace", "delete", "agent_action"}
    assert sum(1 for e in log if e["type"] == "backspace") == 1
    assert sum(1 for e in log if e["type"] == "delete") == 1

    # Persistence under data/raw/<run_id>/human_control/
    dest = tmp_path / "test_run_001" / "human_control"
    assert (dest / "codebase.json").is_file()
    assert (dest / "interaction_log.json").is_file()
    assert (dest / "code" / "app" / "auth.py").is_file()
    assert json.loads((dest / "interaction_log.json").read_text()) == log


def test_rejects_malformed_log(tmp_path, minimal_spec):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"type": "mouse_click"}]))
    adapter = HumanControlAdapter(
        code_dir=FIXTURE / "code",
        log_path=bad,
        run_id="test_run_002",
        raw_root=tmp_path,
    )
    with pytest.raises(ValueError):
        adapter.generate(minimal_spec)
