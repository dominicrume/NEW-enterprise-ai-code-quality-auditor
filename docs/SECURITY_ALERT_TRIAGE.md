# Code-scanning triage

SonarCloud's alerts on this repository, and what was done about each. Kept in
version control because a dismissed alert with no recorded reason is
indistinguishable from one nobody looked at.

## Fixed

| # | Alert | What was wrong | Fix |
|---|---|---|---|
| 2, 3 | Temp files in a publicly writable directory | `work_dir="/tmp/unused"` — world-writable and predictable | `tempfile.gettempdir()` |
| 10 | Temp files in a publicly writable directory | Same, in the delivery-audit script | `tempfile.gettempdir()` |
| 7 | I/O vulnerable to path injection | The remediation engine wrote to paths taken from a scanner's output | Write targets are now *constructed* from the sandbox root plus a verified relative segment (`_contained`), so escaping is impossible by construction rather than prevented by a check |
| 4 | No dependency lock file | Nothing pinned the versions results were produced with | `requirements.lock`, generated from a clean install and used by CI |
| 12–20 | Dependencies not locked to verified versions | Unpinned installs in CI, Dockerfile and `action.yml` | Versions pinned; CI installs from the lock file |

## Dismissed, with reasons

**#8 — "Temporary files should not be created in publicly writable directories",
`remediation/fixers.py:81`.** The line is:

```python
tail = m.group(2)[len("/tmp/"):]
```

That is a string offset inside the fixer that *detects* hardcoded `/tmp` paths
in other people's code. No file is created and no path is used. The scanner
matched the literal, not a behaviour. Dismiss as **false positive**.

**#9 — "CSRF protections should not be disabled", `live/server.py`.** The rule
looks for a CSRF library (`flask-wtf`). The endpoint is a JSON API on
`127.0.0.1` called by `fetch` from its own page, and it is protected by an
`Origin` check with a `Sec-Fetch-Site` fallback — the standard mitigation for
this shape, and the one that actually addresses the real threat here (a page
the user has open in the same browser POSTing to localhost). Adding token
plumbing to a loopback JSON API would add a dependency and complexity without
closing anything the `Origin` check leaves open. Dismiss as **used in tests /
won't fix**, citing the `_same_origin` guard and its tests.

**#21 — "Agentic workflows should not be vulnerable to path injection",
`human_control_recorder.py:64`.** The path is `--out`, supplied by the person
running the recorder, and writing the interaction log where they asked is the
command's entire purpose. There is no privilege boundary to cross: the file is
written as the user, to a location the user named. Dismiss as **won't fix**.

**#11, 13, 15, 17, 19 — "Package manager scripts should not be executed during
installation".** Satisfying this requires `--only-binary=:all:`, which cannot
install this project (`pip install -e .` builds from source by definition) and
would exclude any source-only dependency. Versions are pinned and CI installs
from the lock file, which addresses the reproducibility concern the rule exists
to serve. Dismiss as **won't fix**.

## Re-checking

```bash
auditor scan .          # this project's own five metrics
pip install -r requirements.lock
```
