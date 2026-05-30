"""Shared pytest fixtures: synthetic codebases + specs."""
import pytest


@pytest.fixture
def minimal_spec() -> dict:
    return {
        "name": "test_spec",
        "version": "1",
        "features": [{"id": "auth.login", "description": "x"}],
    }


@pytest.fixture
def codebase_clean() -> dict:
    return {
        "files": {"app/auth.py": "def login(email, pw):\n    return True\n"},
        "manifest": ["auth.login"],
    }


@pytest.fixture
def codebase_hallucinating() -> dict:
    return {
        "files": {"app/x.py": "def login(): pass\n"},
        "manifest": ["auth.login", "auth.face_recognition", "auth.admin_backdoor"],
    }


@pytest.fixture
def interaction_log_typical() -> list[dict]:
    return [{"type": "keystroke"} for _ in range(900)] + [
        {"type": "backspace"} for _ in range(50)
    ] + [{"type": "delete"} for _ in range(50)]
