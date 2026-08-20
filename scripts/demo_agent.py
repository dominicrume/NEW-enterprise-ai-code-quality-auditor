#!/usr/bin/env python3
"""Deterministic demo driver — plays the role of the AI agent.

You control the pace: press Enter to advance each beat. Nothing is typed
live, nothing can be mistyped, and the room sees the auditor react in real
time to files appearing exactly as an agent would write them.

    python scripts/demo_agent.py ~/demo-project

Run `auditor live ~/demo-project` in another window first.
"""
from __future__ import annotations

import sys
from pathlib import Path

GREEN, AMBER, DIM, BOLD, OFF = "\033[32m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"

BRIEF = """Users can register with email and password
Users can log in and get a session token
List available courses
View a course and its lessons"""

ON_SPEC = '''"""Course portal — built to the brief."""
from fastapi import FastAPI

app = FastAPI()
COURSES = [{"id": 1, "title": "AI Fundamentals", "lessons": ["Intro", "Models"]}]


@app.post("/auth/register")
def register(email: str, password: str):
    """Feature 1: users can register with email and password."""
    return {"email": email, "created": True}


@app.post("/auth/login")
def login(email: str, password: str):
    """Feature 2: users can log in and get a session token."""
    return {"token": "session-token", "email": email}


@app.get("/courses")
def list_courses():
    """Feature 3: list available courses."""
    return COURSES


@app.get("/courses/{course_id}")
def view_course(course_id: int):
    """Feature 4: view a course and its lessons."""
    return next((c for c in COURSES if c["id"] == course_id), None)
'''

OFF_SPEC = '''

@app.get("/health")
def health():
    """NOBODY ASKED FOR THIS. Classic agent over-delivery."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Nor this."""
    return {"requests": 0}
'''

INSECURE = '''"""Utilities the agent added on its own."""
import subprocess

API_KEY = "EXAMPLE-FAKE-KEY-DO-NOT-USE"       # hardcoded credential (demo)


def backup(path):
    subprocess.call("tar -czf backup.tgz " + path, shell=True)   # shell injection
'''


def beat(n: int, title: str, say: str) -> None:
    print(f"\n{BOLD}[{n}] {title}{OFF}")
    print(f'{DIM}    say: "{say}"{OFF}')
    input(f"{DIM}    press Enter{OFF}")


def reset(project: Path) -> None:
    """Clear anything a previous run left behind.

    A rehearsal leaves main.py, utils.py and the saved spec in place. Start
    the real demo on top of those and the panel opens already showing the
    end state — scope drift at 2.00, nothing left to move, no story. So the
    driver always begins from empty rather than trusting anyone to remember.
    """
    import shutil

    removed = []
    for name in ("main.py", "utils.py"):
        target = project / name
        if target.exists():
            target.unlink()
            removed.append(name)
    spec_dir = project / ".auditor"
    if spec_dir.exists():
        shutil.rmtree(spec_dir)
        removed.append(".auditor/")
    if removed:
        print(f"{DIM}    reset: removed {', '.join(removed)}{OFF}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/demo_agent.py <project-folder>")
        return 1
    project = Path(sys.argv[1]).expanduser()
    project.mkdir(parents=True, exist_ok=True)
    main_py = project / "main.py"

    print(f"\n{BOLD}DEMO DRIVER{OFF}  →  {project}")
    reset(project)
    print(f"{DIM}Have `auditor live {project}` running in another window.{OFF}")
    print(f"{AMBER}    If it was already running, press Ctrl+C there and start it "
          f"again now — so it opens on an empty folder.{OFF}")
    print(f"\n{BOLD}The brief to paste into the browser box:{OFF}\n{GREEN}{BRIEF}{OFF}")
    input(f"\n{DIM}Paste it, press 'Start checking scope', then press Enter here{OFF}")

    beat(1, "Agent builds the four requested features",
         "I've given the agent the same brief. Watch the panel.")
    main_py.write_text(ON_SPEC)
    print(f"{GREEN}    ✓ wrote main.py — 4 endpoints, all on-spec{OFF}")
    print(f"{DIM}    expect: Security & Complexity come online · Scope drift stays 0.00{OFF}")

    beat(2, "Agent adds two endpoints NOBODY asked for",
         "Now I ask it for one more thing — and it gives me extras.")
    with main_py.open("a") as fh:
        fh.write(OFF_SPEC)
    print(f"{AMBER}    ✓ appended /health and /metrics — OFF-SPEC{OFF}")
    print(f"{DIM}    expect: Scope drift 0.00 → 2.00, amber{OFF}")

    beat(3, "Agent writes a helper with a real vulnerability",
         "And this is what a passing test suite would never tell you.")
    (project / "utils.py").write_text(INSECURE)
    print(f"{AMBER}    ✓ wrote utils.py — hardcoded key + shell injection{OFF}")
    print(f"{DIM}    expect: Security jumps into the red band{OFF}")

    print(f"\n{BOLD}Close with:{OFF}")
    print('  "Every test would pass. The code works. But it shipped two features')
    print('   nobody asked for and a credential in source — and you saw it happen')
    print('   live, not in a post-mortem six months from now."\n')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
