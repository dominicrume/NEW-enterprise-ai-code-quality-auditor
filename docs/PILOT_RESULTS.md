# Pilot Results — Run 002 (May 2026)

**Author:** Dominic Rume (MSc AI, Aston University · supervisors Julien Barney, Kate Sugden)
**Instrument:** AI Code Quality Auditor — five-condition, five-metric experimental framework
**Status:** Pilot. 3 of 5 conditions captured. Hallucination & security analysers stabilised mid-pilot (see § *Methodological changes during pilot*).

---

## 1. What this pilot demonstrates

That the full end-to-end pipeline of the instrument works on real data:

```
spec.yaml ─► adapter (per condition) ─► capture-contract artefacts
                                        ├─ codebase.json
                                        └─ interaction_log.json
                                              │
                                              ▼
                                        5 analysers ─► CSV ─► dashboard
```

Three conditions were exercised end-to-end against one fixed specification
(`specs/agent_education_system.yaml`, six features, three governance rules,
four cross-cutting guardrails).

---

## 2. Conditions captured

| Condition | Mode | Outcome |
|---|---|---|
| `human_control` | Local capture: hand-typed in VS Code with `pynput` keystroke recorder | 1 file (`app/test.py`, `print("hello")`), 1,315 keystroke events |
| `claude_code`   | Real `claude` CLI v2.1.139, `--dangerously-skip-permissions`, stream-JSON output | 1 file (`main.py`, 123 lines FastAPI), 14 agent events |
| `cursor_agent`  | Real `cursor-agent` v2026.05.28, `--force --model auto`, stream-JSON output | 13 source files across `app/`, `app/routes/`, `tests/` (572 LOC total), 59 agent events |
| `antigravity`   | Deferred — no public CLI available | replay adapter built; awaiting web-IDE capture |
| `replit_agent`  | Deferred — Replit Agent is browser-only, no first-party CLI | replay adapter built; awaiting web-IDE capture |

The `human_control` session was intentionally short (≈ 5 minutes) to prove the
keystroke-capture pipeline. A full-length baseline session is planned for the
main study.

---

## 3. Five-metric results

### 3.1 Headline table

| Metric | `human_control` | `claude_code` | `cursor_agent` |
|---|---:|---:|---:|
| Files produced                 | 1     | 1     | **13** |
| Agent / interaction events     | 1,315 | 14    | 59     |
| Hallucinations (count)         | 0     | 0     | **1**  |
| Keystroke correction (per 1k)  | **52.84** | 0     | 0      |
| McCabe complexity (mean cc)    | 0.00  | 1.62  | **2.03** |
| Code duplication (%)           | 0     | 0     | 0      |
| Security density (CWE / kloc)  | 0     | 0     | **62.94** |

Lower is better for all metrics except *files produced* and *events*, which
are descriptive.

### 3.2 What each row tells us

**Keystroke correction (52.84 per 1,000 keys).** The baseline produced 66
backspaces over 1,249 productive keystrokes — a 5.3 % correction rate.
This is the only signal that *cannot* be synthesised retroactively and is
the strongest empirical justification for capturing the human condition
locally rather than estimating it.

**Hallucinations.** The auto-detector flagged that `cursor_agent` shipped a
`/health` endpoint not present in the spec. This is a genuine scope drift,
not a heuristic false positive — `cursor_agent` also produced a
`pytest` test suite that the spec did not request. `claude_code` shipped
strictly within scope.

**Complexity (mean cyclomatic).** `cursor_agent` produced more
control-flow-rich code (2.03) than `claude_code` (1.62), consistent with the
larger surface area: 13 modular files vs 1 monolithic file. This is a
structural finding about *agent defaults*, not capability — both produced
working systems.

**Duplication (k=6 shingle %).** All three conditions: 0 %. Each codebase
is too small for meaningful repetition.

**Security density (per kloc, local Bandit).** `cursor_agent` triggered 1
CWE-tagged finding across ~16 LOC of Python that Bandit could analyse,
giving 62.9 per kloc. `claude_code` triggered 0. The human baseline had no
substantive code to scan. *See § 4 for the methodological switch from
SonarCloud to local Bandit.*

### 3.3 Feature coverage (auto-derived manifest)

| Spec feature ID            | `claude_code` | `cursor_agent` |
|---|:--:|:--:|
| `auth.register`            | ✅ | ✅ |
| `auth.login`               | ✅ | ✅ |
| `course.list`              | ✅ | ✅ |
| `course.view`              | ✅ | ✅ |
| `training.module.corporate`| ✅ | ✅ |
| `training.module.academic` | ✅ | ✅ |
| **Coverage**               | **6 / 6** | **6 / 6** |
| Off-spec endpoints         | none | `/health` |

Detection method: a two-segment token match (`auth.register` requires both
the token `auth` *and* the token `register` or `registers` to appear in the
combined codebase). False-negative risk is low for this spec; false-positive
risk is documented in [auditor/analyzers/manifest_deriver.py](../auditor/analyzers/manifest_deriver.py).

---

## 4. Methodological changes made during this pilot

Two analyser components were rewritten mid-pilot once it became clear the
originals were structurally biased. Both changes are documented here for
defensibility.

### 4.1 Security analyser: SonarCloud → local Bandit

**The problem.** The original `security_analyzer.py` queried a single
SonarCloud project keyed off the spec (`dominicrume_NEW-...-auditor`) and
divided the issue count by *each condition's* LOC. That gave the same
numerator across all conditions and a different denominator, producing
implausibly large per-kloc figures (e.g. 5000/kloc for a one-line
codebase) — a structurally broken metric.

**The fix.** Replaced with a local `bandit -r -f json` scan over the
captured codebase, counting issues whose `issue_cwe.id` is non-null
(preserving the CWE framing). Per-condition isolation by construction;
no external infrastructure required.

**Trade-off.** Bandit's rule set is narrower than SonarCloud's, but it is
deterministic, free, scriptable, and version-pinnable — better fit for a
reproducible dissertation experiment. SonarCloud remains wired in the CI
pipeline for the host repo's own quality signal.

### 4.2 Hallucination analyser: requires manifest → auto-derives one

**The problem.** The original analyser computed `manifest − spec_features`.
Agentic adapters never emit a manifest, so hallucinations were
structurally 0 for every AI condition — measuring nothing.

**The fix.** Added `auditor/analyzers/manifest_deriver.py`, which scans
the produced code for token evidence of each spec feature and for FastAPI
route declarations not covered by any spec feature. The hallucination
analyser uses the manifest when present (the `human_control` path) and
falls back to the auto-derived count otherwise.

**Trade-off.** A heuristic, not a formal verifier. False positives are
possible when an agent uses unconventional naming; false negatives are
possible when an agent ships a hallucinated feature whose path tokens
overlap with a spec feature. For pilot scale this is acceptable; for
production we recommend forcing each adapter to emit an explicit manifest
as part of its capture contract.

### 4.3 Codebase loaders: now exclude `.venv` / `__pycache__` / `node_modules`

When `cursor_agent` was run, the agent created a `.venv/` and `pip install`-ed
dependencies into it. The original codebase loader walked all files under
the work directory, ingesting 1,400+ files of transitive third-party code
and inflating every metric. Loaders for all four AI adapters now exclude:
`.venv`, `venv`, `env`, `__pycache__`, `site-packages`, `node_modules`,
`.pytest_cache`, `.git`, `dist`, `build`, `.mypy_cache`, `.ruff_cache`, and
any `*.egg-info` directory.

---

## 5. What the numbers do not say

Three caveats your supervisors will (correctly) raise, addressed here:

1. **Sample size N = 1 per condition.** This is a pilot demonstrating the
   instrument, not a study. Main-study design will run K ≥ 5 sessions per
   condition under a power calculation derived from these pilot variances.

2. **Human session was unrepresentatively short.** ~5 minutes shipping
   `print("hello")` is *not* a serious baseline. The correction-frequency
   number (52.84 / 1k) is the only useful signal from this row. The main
   study will allow ≥ 60 minutes per human session with the same spec.

3. **Two conditions deferred.** `antigravity` (no public CLI) and
   `replit_agent` (browser-only) were not captured. Replay-mode adapters
   are built and unit-tested; both conditions will be captured via
   in-IDE sessions with the resulting code + log loaded through the
   replay path. This is a vendor-access constraint, not an instrument
   limitation.

---

## 6. Reproducing this pilot

```bash
# 1. Install
git clone https://github.com/dominicrume/NEW-enterprise-ai-code-quality-auditor
cd NEW-enterprise-ai-code-quality-auditor
pip install -e ".[dashboard]" bandit python-dotenv pynput

# 2. Human baseline (you need to type in VS Code)
./scripts/start_human_session.sh run_002

# 3. Claude Code condition
PYTHONPATH=. python scripts/run_claude_code_session.py run_002

# 4. Cursor Agent condition
mkdir -p ~/sessions/run_002_cursor/code
PYTHONPATH=. python -c "
import yaml
from auditor.adapters.cursor_agent_adapter import CursorAgentAdapter
spec = yaml.safe_load(open('specs/agent_education_system.yaml'))
CursorAgentAdapter(work_dir='~/sessions/run_002_cursor/code', run_id='run_002').generate(spec)
"

# 5. Score everything into a CSV (see scripts/score_run.py)
# 6. Dashboard
PYTHONPATH=. python -m auditor.dashboard.app
# → http://127.0.0.1:5000
```

---

## 7. Artefacts

- **Code:** https://github.com/dominicrume/NEW-enterprise-ai-code-quality-auditor
- **CSV:** [data/reports/run_002_comparison.csv](../data/reports/run_002_comparison.csv)
- **Provenance:** [data/reports/run_002_comparison.provenance.json](../data/reports/run_002_comparison.provenance.json)
- **Dashboard screenshots:**
  - [docs/screenshots/dashboard_index.png](screenshots/dashboard_index.png)
  - [docs/screenshots/dashboard_report.png](screenshots/dashboard_report.png)
- **Captured raw data:** `data/raw/run_002/` (gitignored, regeneratable from spec + adapter runs)
