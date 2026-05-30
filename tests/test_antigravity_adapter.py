import json
import shutil
from pathlib import Path

from auditor.adapters.antigravity_adapter import AntigravityAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "antigravity"


def _fake_runner(raw_events, produced_src):
    def _runner(prompt, work_dir):
        assert "SPEC" in prompt
        for child in produced_src.iterdir():
            dest = work_dir / child.name
            shutil.copytree(child, dest) if child.is_dir() else shutil.copy2(child, dest)
        return raw_events
    return _runner


def test_antigravity_captures_session(tmp_path, minimal_spec):
    raw = json.loads((FIXTURE / "raw_stream.json").read_text())
    adapter = AntigravityAdapter(
        work_dir=tmp_path / "ws",
        run_id="test_ag_001",
        raw_root=tmp_path / "raw",
        runner=_fake_runner(raw, FIXTURE / "produced_code"),
    )
    codebase, log = adapter.generate(minimal_spec)

    assert "server.py" in codebase["files"]
    assert codebase["manifest"] == ["server.health"]
    assert all(e["type"] == "agent_action" for e in log)
    assert any(e.get("tool") == "write_file" for e in log)
    assert any(e.get("detail") == "success" for e in log)

    dest = tmp_path / "raw" / "test_ag_001" / "antigravity"
    assert (dest / "codebase.json").is_file()
    assert (dest / "interaction_log.json").is_file()
    assert (dest / "raw_stream.json").is_file()
    assert (dest / "code" / "server.py").is_file()
