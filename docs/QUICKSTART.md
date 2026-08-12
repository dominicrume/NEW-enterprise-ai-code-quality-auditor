# Quickstart — audit an AI agent live

One command. No spec to write, no session to start, nothing to stop with Ctrl+C
except the tool itself.

```bash
pip install ai-code-quality-auditor
cd your-project
auditor live
```

A browser opens. Five checks are on screen. Leave it running while you or an
agent write code, and the numbers move.

---

## Testing it with Antigravity, step by step

This is the exact sequence to run a fresh project through Google Antigravity
with the auditor watching. It works identically for Cursor, Claude Code, Replit,
or you typing by hand — the auditor watches the *folder*, so it never needs to
know which tool is writing.

### 1. Make an empty project folder

```bash
mkdir ~/projects/course-portal && cd ~/projects/course-portal
```

### 2. Start the live audit — before the agent writes anything

```bash
auditor live
```

Your browser opens on `http://127.0.0.1:7777`. You will see:

- **`0 files · 0 lines`** — nothing built yet.
- Five metric cards. Security, Complexity and Duplication are live; **Scope
  drift** says *"needs a brief"*; **Rework** says *"needs a recorded session"*.
  Nothing shows a fake zero.
- A box at the top: **"What did you ask the agent to build?"**

### 3. Type the brief — the same words you are about to give Antigravity

Paste your prompt, one feature per line:

```
Users can register with email and password
Users can log in and get a session token
List available courses
View a course and its lessons
```

Press **Start checking scope**. Scope drift comes online and the brief is saved
to `.auditor/spec.yaml`, which you can edit later — it is yours, not hidden.

> **This is the step that matters.** Scope drift is the check that catches an
> agent building something nobody asked for. It needs to know what *was* asked
> for, and that is the only thing the tool cannot infer.

### 4. Open the same folder in Antigravity and give it the same prompt

Point Antigravity at `~/projects/course-portal` and paste the identical brief.
Then let it work.

**Keep the browser tab visible.** As Antigravity writes files:

- Metric cards update within a second or two of each save.
- The **Activity** feed logs what changed and what moved.
- When Antigravity writes its first Python file, Security and Complexity go
  from `n/a` to live numbers — marked **▲ now measurable**.

### 5. Now make it go off-spec — the demo moment

Ask Antigravity for something you deliberately did **not** put in the brief:

> "Also add a /health endpoint and a /metrics endpoint."

Within seconds, **Scope drift ticks from 0 → 1 → 2** and turns amber, unprompted.
That is the instrument catching an agent shipping work nobody requested — the
class of risk a passing test suite cannot see.

### 6. Stop when you're done

`Ctrl+C` in the terminal. The spec stays in `.auditor/spec.yaml`; run
`auditor live` again any time and it picks up where you left off.

---

## What each check needs to work

| Check | Works on | Needs |
|---|---|---|
| Security | Python only | nothing |
| Complexity | Python only | nothing |
| Duplication | any language | nothing |
| Scope drift | FastAPI routes, CLI subcommands | a brief |
| Rework | any | a recorded keystroke session |

Two honest constraints, both visible in the UI rather than hidden:

- **Security and Complexity read Python.** On a TypeScript or JavaScript project
  they report `n/a` with the reason — never `0.00`, which would read as a clean
  bill of health for code that was never scanned.
- **Scope drift detects FastAPI routes and CLI subcommands.** If your agent
  writes plain functions, it will not fire. For a live demo, ask for a **FastAPI**
  app.

## The other commands

```bash
auditor scan .                        # one-off audit, prints a table
auditor scan . --fail-on critical     # CI gate, exits 1 on a critical band
auditor scan . --json                 # machine-readable
auditor watch .                       # same as live, but in the terminal
```

`auditor experiment` and `auditor run` drive the controlled five-condition study
behind the dissertation. You do not need them to audit your own code.
