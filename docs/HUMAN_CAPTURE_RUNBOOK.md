# Human capture runbook

How to record a `human_control` session — you coding, by hand, with the
keystroke recorder running — and score it into a report.

## 0. Before you start (macOS, once)

`pynput` reads global key events, which macOS gates behind Accessibility
permission. **Without it the recorder runs but captures nothing** — this is the
single most common way to lose a session.

**System Settings › Privacy & Security › Accessibility** → enable the app you
run the recorder from (Terminal, iTerm, or VS Code if you use its terminal).
You must fully quit and reopen that app afterwards.

Verify before committing to a long session: start the recorder, type twenty
characters somewhere, press Ctrl+C, and confirm the event count is not zero.

## 1. Start the session

```bash
scripts/start_human_session.sh <run_id>        # e.g. website_001
```

This creates `~/sessions/<run_id>/code/`, opens it in VS Code, and starts the
recorder. **Write all your code inside that folder** — anything outside it is
not captured.

Leave the recorder terminal open and untouched. Ctrl+C ends the session.

### Stopping and restarting is now safe

Each recorder run writes a timestamped file under
`~/sessions/<run_id>/segments/`, and `log.json` is rebuilt as the concatenation
of every segment. Take breaks, restart, reboot — earlier segments survive. The
active segment autosaves every 5 seconds, so a crash costs seconds, not hours.

> This was not true before August 2026. The original recorder overwrote its log
> on every invocation, which is how ~2,133 events were lost in the main study
> (PROTOCOL_DEVIATIONS.md, Deviation 003).

## 2. Write the spec — before scoring, not before coding

The hallucination metric counts *features present in the code but absent from
the spec*. With no spec, every feature you build counts as scope drift and the
number is meaningless.

You can capture first and write the spec afterwards, but write it **from what
you intended to build**, not from what you ended up shipping — otherwise the
metric is circular and measures nothing.

Copy `specs/agent_education_system.yaml` as the shape: `name`, `version`,
`features[].id` + `description`, `governance[].rule`, `allowlist`.

## 3. Score the session

```bash
PYTHONPATH=. .venv/bin/python scripts/score_human_session.py <run_id>
```

Check the flags first — `--help` lists the expected spec and session paths.
Output lands in `data/reports/`, and the dashboard picks it up:

```bash
PYTHONPATH=. .venv/bin/python -m auditor.dashboard.app   # http://127.0.0.1:5050
```

## 4. What this session can and cannot support

**Can:** demonstrate the instrument end-to-end on a real build; give a live demo
far more convincing than a slide; produce a genuine second human data point.

**Cannot, on its own:** fix the human-baseline limitation in the dissertation.
That baseline is N = 1 per specification, author-executed (Deviation 003), and
one more author-executed session does not resolve it — the documented fix is
*independent, blinded participants*. A fresh session strengthens the
demonstration and the future-work story; it does not change the statistics
already submitted.

**Comparability:** a session against your own new spec is not comparable to
`main_001`, which used three fixed specs. To add a directly comparable data
point, code against an existing spec in `specs/` instead.

## 5. Known constraints

- Complexity is scored per function on `.py` files only. A website written in
  JS/TS will score 0.00 complexity — not a good result, an out-of-scope one.
  Duplication and hallucination are language-agnostic; security (Bandit) is
  Python-only.
- The recorder counts event *types*, not timings — it measures correction
  effort, not speed.
