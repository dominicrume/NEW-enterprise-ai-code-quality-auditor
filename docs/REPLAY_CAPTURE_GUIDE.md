# Replay capture guide — `replit_agent` and `antigravity`

Both vendors run inside their own web IDE — there is no first-party CLI we
can drive from the auditor. To score them, you run the session manually
in the browser, save two artefacts, and point the adapter's `replay_dir`
at the folder.

**Time: ~30 min per condition.**

---

## What every replay folder must contain

```
~/sessions/run_002_<vendor>/
├── code/                  ← the codebase the agent produced
│   ├── main.py            (or whatever files it wrote)
│   └── manifest.json      (optional — leave absent to auto-derive)
└── log.json               ← list of agent events, one dict per entry
```

`log.json` must be a JSON list of dicts. Each dict needs at minimum
`{"type": "agent_action"}` to satisfy the capture contract. Extra keys
(`subtype`, `tool`, `detail`) are preserved for forensics but ignored by
the analysers. Minimum acceptable log:

```json
[{"type": "agent_action"}]
```

---

## Replit Agent (browser only)

1. **Go to** https://replit.com → sign in → **+ Create App** → pick the
   *Python / FastAPI* template (or Blank — Replit Agent will scaffold).
2. **Open the Agent panel** (right-hand sidebar). Paste this prompt:
   ```
   Implement the specification below as a Replit project. Stay within
   the listed features only.

   <paste the full contents of specs/agent_education_system.yaml here>
   ```
3. **Let Replit Agent finish.** Watch the action log on the right.
4. **Capture the code.** In Replit: hamburger menu → *Download as zip*.
   Unzip into `~/sessions/run_002_replit/code/`.
5. **Capture the log.** Open Replit's Agent activity feed → Cmd-A → copy.
   You'll get a human-readable list of steps. Convert to JSON minimally:
   ```bash
   python -c '
   steps = """<paste here>""".strip().split("\n")
   import json
   open("/Users/you/sessions/run_002_replit/log.json","w").write(
     json.dumps([{"type":"agent_action","subtype":s} for s in steps if s], indent=2)
   )'
   ```
   If Replit doesn't expose a structured event log, you may legitimately
   record one event per visible action — the *count* and *type=agent_action*
   are what matter for the keystroke-correction metric (which is
   structurally 0 for any agent anyway).
6. **Score it:**
   ```bash
   cd ~/Downloads/ai-code-quality-auditor
   PYTHONPATH=. python -c "
   import yaml
   from auditor.adapters.replit_agent_adapter import ReplitAgentAdapter
   spec = yaml.safe_load(open('specs/agent_education_system.yaml'))
   a = ReplitAgentAdapter(
       work_dir='/tmp/unused',
       replay_dir='/Users/user/sessions/run_002_replit',
       run_id='run_002',
   )
   code, log = a.generate(spec)
   print(f'replit_agent: {len(code[\"files\"])} files, {len(log)} events')
   "
   ```

---

## Antigravity (Google Gemini, browser only)

1. **Go to** https://antigravity.google → sign in with your Google
   account → **New Project**.
2. **Paste the same spec prompt** as above into the chat. Let it run.
3. **Download the produced code.** Antigravity exposes the project as a
   web IDE — click the file tree → *Download project as zip*. Unzip into
   `~/sessions/run_002_antigravity/code/`.
4. **Capture the log.** Antigravity shows a *Plan / Steps* panel. Either
   export it as JSON (if the option exists) or convert manually with the
   same Python one-liner from the Replit step above, into
   `~/sessions/run_002_antigravity/log.json`.
5. **Score it:**
   ```bash
   PYTHONPATH=. python -c "
   import yaml
   from auditor.adapters.antigravity_adapter import AntigravityAdapter
   spec = yaml.safe_load(open('specs/agent_education_system.yaml'))
   a = AntigravityAdapter(
       work_dir='/tmp/unused',
       replay_dir='/Users/user/sessions/run_002_antigravity',
       run_id='run_002',
   )
   code, log = a.generate(spec)
   print(f'antigravity: {len(code[\"files\"])} files, {len(log)} events')
   "
   ```

---

## After both runs — regenerate the 5-condition CSV

```bash
cd ~/Downloads/ai-code-quality-auditor
PYTHONPATH=. python scripts/score_run_002.py   # (write me — script in scratchpad)
```

Or one-shot in the dashboard: refresh http://127.0.0.1:5050/ and the
`run_002_comparison.csv` will be re-derived next time you score.

---

## What to write in your dissertation about this capture method

> "For vendors that ship only a browser-based agent (Replit Agent;
> Google Antigravity), the auditor's `replay_dir` adapter pathway accepts
> a folder containing the produced codebase and a JSON event log. The
> session is conducted manually in the vendor's web IDE; the captured
> artefacts are then loaded through the identical capture contract used
> by the CLI-driven conditions, so all five conditions score against the
> same five analysers without per-vendor code paths."

That paragraph is what makes the methodology robust under questioning —
the replay path is not a workaround, it is a *first-class capture mode*
that absorbs vendor-access asymmetries without leaking vendor specifics
into the analyser layer.

---

## Common pitfalls

| Symptom | Fix |
|---|---|
| Adapter raises `FileNotFoundError: work_dir not found` | `replay_dir` path must exist *and* contain a `code/` subfolder |
| `0 files` after replay | Check your codebase suffix — loader only ingests `.py .js .ts .tsx .jsx .go .rs .java .rb .sql .yaml .yml .toml .md` |
| `0 events` after replay | `log.json` missing or not a JSON list. Minimum: `[{"type":"agent_action"}]` |
| Hallucinations metric flags everything | Your code uses unconventional naming; either declare a `manifest.json` by hand inside `code/` or refine the deriver tokens |
