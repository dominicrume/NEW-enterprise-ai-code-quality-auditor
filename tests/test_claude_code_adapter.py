"""Claude Code adapter — drives the vendor CLI; here we inject a fake runner."""
import json
import shutil
from pathlib import Path

from auditor.adapters.claude_code_adapter import ClaudeCodeAdapter


FIXTURE = Path(__file__).parent / "fixtures" / "claude_code"


def _fake_runner(raw_events: list[dict], produced_src: Path):
    """Return a runner that writes a captured codebase into work_dir and
    replays a pre-recorded raw event stream — i.e. simulates a real session.
    """
    def _runner(prompt: str, work_dir: Path):
        assert "SPEC" in prompt  # adapter rendered the spec into the prompt
        for child in produced_src.iterdir():
            dest = work_dir / child.name
            if child.is_dir():
                shutil.copytree(child, dest)
            else:
                shutil.copy2(child, dest)
        return raw_events
    return _runner


def test_drives_claude_code_and_persists(tmp_path, minimal_spec):
    raw_events = json.loads((FIXTURE / "raw_stream.json").read_text())
    work_dir = tmp_path / "workspace"

    adapter = ClaudeCodeAdapter(
        work_dir=work_dir,
        run_id="test_cc_001",
        raw_root=tmp_path / "raw",
        runner=_fake_runner(raw_events, FIXTURE / "produced_code"),
    )

    codebase, log = adapter.generate(minimal_spec)

    # Codebase loaded from work_dir
    assert "app/auth.py" in codebase["files"]
    assert codebase["manifest"] == ["auth.login"]

    # Interaction log obeys the capture contract: every event is agent_action
    assert len(log) == len(raw_events)
    assert all(e["type"] == "agent_action" for e in log)
    # Vendor detail preserved
    assert any(e.get("tool") == "Write" for e in log)
    assert any(e.get("detail") == "success" for e in log)
    assert any(e.get("subtype") == "result" for e in log)

    # Persistence
    dest = tmp_path / "raw" / "test_cc_001" / "claude_code"
    assert (dest / "codebase.json").is_file()
    assert (dest / "interaction_log.json").is_file()
    assert (dest / "raw_stream.json").is_file()
    assert (dest / "code" / "app" / "auth.py").is_file()
    assert json.loads((dest / "raw_stream.json").read_text()) == raw_events
