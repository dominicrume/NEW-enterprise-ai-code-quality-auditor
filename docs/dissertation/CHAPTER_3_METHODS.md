# Chapter 3 — Methods

> Draft for MSc dissertation, Aston University, AI & Business Strategy. ~2,500 words.

## 3.1 Research design

This study compares five independent AI-coding workflows against one fixed
specification using five empirical quality metrics. The design is
between-conditions with replication: each condition produces *K* attempts
at each of *S* specifications, yielding *N = K × S* observations per
condition for every metric. The five conditions are pre-registered (see
[EXPERIMENT_PROTOCOL.md](../EXPERIMENT_PROTOCOL.md)) and held constant
across the experiment.

The five **conditions** (independent variable, vendor product):

| Condition | Vendor / product | Adapter file |
|---|---|---|
| `human_control` | none (hand-typed baseline) | `human_control_adapter.py` |
| `claude_code`   | Anthropic Claude Code CLI v2.1 | `claude_code_adapter.py` |
| `cursor_agent`  | Cursor Agent CLI v2026.05 | `cursor_agent_adapter.py` |
| `replit_agent`  | Replit Agent (web IDE, replay-captured) | `replit_agent_adapter.py` |
| `antigravity`   | Google Antigravity (desktop IDE, Gemini 3.5 Flash) | `antigravity_adapter.py` |

The five **metrics** (dependent variables, all machine-recorded):

1. **Security vulnerability density** — OWASP/CWE-tagged findings per 1,000 lines of code, computed by Bandit over the captured codebase.
2. **Cyclomatic complexity** — mean McCabe per function, computed by `radon`.
3. **Code duplication** — percentage of source lines inside any 6-line repeat shingle.
4. **Hallucination count** — features shipped that were *not* in the spec, detected by `manifest_deriver` (web routes + CLI subcommands).
5. **Keystroke correction frequency** — backspace + delete events per 1,000 keystrokes, recorded by `pynput` during the `human_control` condition; structurally zero for agentic conditions.

The **specifications** (treatment stimuli, identical across conditions):

| Spec | Domain | Features | Governance rules |
|---|---|---|---|
| `agent_education_system.yaml` | CRUD + auth (web app) | 6 | 3 |
| `data_pipeline.yaml` | ETL + scheduler (infrastructure) | 6 | 3 |
| `internal_tool_cli.yaml` | CLI tool with subcommands | 6 | 3 |

Three specifications were used (not one) so external-validity claims could
be made across task types: the dissertation reports whether the
condition-level differences hold across all three specifications, or
interact with task domain.

## 3.2 The capture contract

Every condition must produce two artefacts in a shape the analysers can
read without per-vendor branching:

```
codebase        : {"files": {path: content}, "manifest": [feature_ids]}
interaction_log : [ {"type": str, ...}, ... ]
                  where type ∈ {keystroke, backspace, delete, agent_action}
```

This is the **capture contract**. It is the methodological boundary that
makes the five conditions comparable: vendors that are very different
(a human typing keystrokes vs an agent streaming JSON tool calls) are
required to surface their work as the same shape. Adapter code translates
between the vendor's native output and the contract; analyser code never
touches a vendor.

For the `human_control` condition, `pynput` captures every key press in
real time and classifies each as `keystroke`, `backspace`, or `delete`.
For the four AI conditions, every event the vendor emits (tool call,
file edit, thinking block where exposed) is normalised to
`{"type": "agent_action", "subtype": <vendor type>, ...}`. Vendor-native
detail is preserved in sibling keys for forensics but is invisible to
the analysers.

The capture contract is enforced by `load_interaction_log` in each
adapter, which validates every event's type against the permitted set
and raises `ValueError` on the first malformed entry. Contract violations
abort the run rather than silently degrade the metric.

## 3.3 Capture procedure

### 3.3.1 Agent conditions (claude_code, cursor_agent)

Both vendors ship a non-interactive CLI that accepts a prompt and
streams JSON events to stdout. The adapters spawn the CLI with
`subprocess.run`, capture stdout line by line, parse each line as JSON,
and persist the raw stream alongside the contract-shaped events for
forensic re-analysis.

Anthropic Claude Code is invoked with
`claude -p <prompt> --output-format stream-json --verbose
--dangerously-skip-permissions`; the permission-skip flag is required
because the adapter runs unattended in a clean per-run working
directory (no human is present to confirm individual tool calls). The
agent is sandboxed to `~/sessions/<run_id>/code/`.

Cursor Agent is invoked with
`cursor-agent -p --output-format stream-json --force --model auto`.
The `auto` model is a free-tier constraint; named models require a
paid subscription. The dissertation reports `cursor_agent` results
under this constraint and discusses the implication in §6 of the
Discussion chapter.

### 3.3.2 Replay conditions (replit_agent, antigravity)

Replit Agent and Google Antigravity do not expose a scriptable CLI.
Replit Agent runs inside replit.com's web IDE; Antigravity runs in
Google's desktop IDE. For these conditions the researcher runs the
session manually in the vendor's interface, then hands the produced
files and a captured event log to the adapter's `replay_dir` parameter,
which loads the artefacts through the same capture contract used by
the CLI-driven conditions.

Both replay adapters share the same loader and persistence code with
their CLI-driven counterparts; the only difference is the source of the
input bytes. The dissertation treats replay-mode captures as
methodologically equivalent to live captures — the analyser cannot tell
the difference and the capture contract is identical — but flags the
within-cell variance constraint discussed in §3.6 below.

### 3.3.3 Human-control condition

The researcher hand-codes the specification in VS Code for a
pre-registered 60-minute session per replication, with all AI extensions
(GitHub Copilot, Cursor tab-complete, Claude in-IDE) disabled and the
disabled state verified before each session. The `pynput`-backed
recorder runs in a parallel terminal and captures every key press at the
OS level, including modifier keys, backspaces, and deletes.

The session ends when the 60-minute timer expires or the researcher
finishes the spec, whichever comes first. The codebase is captured by
the same loader used for the AI conditions; the keystroke log is
captured by the recorder. Both are persisted under
`~/sessions/<run_id>/`.

## 3.4 Analyser pipeline

Each metric is implemented as a single Python function with a uniform
signature:

```python
def analyze(codebase: dict, interaction_log: list[dict], spec: dict) -> MetricScore
```

This signature does two things at once: it formalises the capture
contract (whatever the analyser sees is exactly what the contract
defines), and it forces analyser independence (no analyser can use any
condition-specific knowledge). The analyser pipeline is therefore
*blinded by construction*: condition labels are added by the
orchestrator, never the analyser.

### 3.4.1 Security density

`security_analyzer.py` materialises the captured codebase to a
temporary directory and invokes `bandit -r <dir> -f json -q`. Bandit's
JSON output enumerates findings with stable rule identifiers; the
analyser counts only findings whose `issue_cwe.id` field is non-null,
preserving the OWASP/CWE framing required by §3 of the
[Metrics document](../METRICS.md). The count is divided by the
codebase's Python line count and multiplied by 1,000 to express the
result as findings per 1,000 lines of code (`per_kloc`).

The original instrument design queried SonarCloud's REST API instead;
the switch to local Bandit during the pilot is documented in §4 of
the Pilot Results document and analytical note 002 of the protocol
deviations log. The change was made because SonarCloud's per-project
scoping meant every condition shared a numerator while differing in
denominator, producing artefactually large per-kloc figures
(>1000/kloc) for any codebase under 100 lines. Local Bandit scopes
the numerator to each condition's own captured code, restoring
methodological soundness.

### 3.4.2 Cyclomatic complexity

`complexity_analyzer.py` uses `radon.complexity.cc_visit` over each
Python file to enumerate every function/method's McCabe number, then
reports the arithmetic mean. Files outside the suffix whitelist
(`.py`, `.js`, `.ts`, etc.) and files inside excluded directories
(`.venv`, `__pycache__`, `site-packages`, `node_modules`) are skipped
by the codebase loader before the analyser sees them, so the metric
reflects the agent's *produced* code, not transitive dependencies.

### 3.4.3 Duplication

`duplication_analyzer.py` builds a hash set of every 6-consecutive-line
shingle across every source file (k=6 is the conventional plagiarism
detection window), counts the number of source lines that appear in
any shingle with cardinality ≥ 2, and divides by total source lines.
The metric is reported as a percentage.

### 3.4.4 Hallucination

`hallucination_analyzer.py` defers to `manifest_deriver.derive(spec,
codebase)`, which scans the codebase for evidence of each spec
feature (token-match on the feature's terminal identifier and its
plural) and for FastAPI/Flask web routes and argparse/Click CLI
subcommands. Routes and commands that do not map to any spec feature
are flagged as **hallucinated**; the metric is their count.

The CLI subcommand detection was added after the main study revealed
that one vendor shipped a data-pipeline CLI when given a spec asking
for a different CLI structure. Without CLI detection the metric was
structurally blind to that finding. Both the spec change and the
deriver upgrade are documented in the protocol deviations log
(analytical note 001) so the audit trail is complete.

The deriver is a heuristic, not a verifier, and is documented as such.
Cohen's κ between the deriver's output and a hand-labelled sample of
30 runs is reported in the Results chapter; the dissertation treats
the hallucination metric as inferential only if κ ≥ 0.6.

### 3.4.5 Keystroke correction

`keystroke_analyzer.py` counts every event with `type ∈ {"backspace",
"delete"}` and divides by the total `keystroke` count, scaling to per
1,000. The metric is structurally zero for the four AI conditions
(agents do not press keys) and is the only metric for which the
`human_control` condition produces a non-zero value by construction.
Its inclusion is justified by §2.2 of the Metrics document: an
empirical floor for "how much rework does a human do on the same
spec" is necessary to interpret the agentic conditions' zero against
*something*, not against the absence of a number.

## 3.5 Pre-registration

The study design was committed to the project's git repository as
`docs/EXPERIMENT_PROTOCOL.md` before any main-study data was captured.
The first commit timestamp of that file is the methodological
boundary between pilot exploration and the dissertation result. Every
detail — sample size, model versions, statistical test, multiple-
comparisons policy — was fixed in advance. Subsequent changes are
appended to `docs/PROTOCOL_DEVIATIONS.md` with date, rationale, and
analytical consequence; the file is empty if no deviation occurred.

Three deviations were recorded during the main study:

- **Deviation 001**: replay-mode within-cell variance is structurally
  zero for web/desktop-IDE vendors. Reported as N=1 effective per cell
  for those conditions; pairwise statistical tests exclude these cells
  from variance estimates and use ranked comparisons instead.
- **Deviation 002** (and 003, since rescinded after verification):
  initially flagged contamination of one cell, retracted after the
  researcher confirmed workspace isolation. The retraction itself is
  retained in the log to preserve audit integrity.
- **Analytical note 001**: Replit Agent shipped a data-pipeline CLI
  when given the `internal_tool_cli` specification under a fresh
  workspace and explicit instructions prohibiting pipeline output.
  Reported as a measured architectural-prior dominance, not operator
  error.

## 3.6 Statistical analysis plan

The pre-registered analysis is implemented in
`notebooks/statistical_analysis.ipynb` and is identical for every
metric:

1. **Normality** is checked per `(condition, spec)` cell via
   Shapiro-Wilk at p > 0.05.
2. **Variance equality** is checked across the five conditions via
   Levene's test at p > 0.05.
3. If both pass: **one-way ANOVA** across the five conditions per
   metric. If significant at the per-test α of 0.01 (Bonferroni
   correction across five metrics), **Tukey HSD** is run as a
   post-hoc to identify the responsible pairs.
4. If either fails: **Kruskal-Wallis** across the five conditions per
   metric, with **Dunn's test** post-hoc under Bonferroni adjustment.
5. **Effect sizes** are reported as η² for the omnibus and Cohen's *d*
   for pairwise comparisons.
6. **95% confidence intervals** on each condition's mean are bootstrap-
   resampled with 10,000 replicates.
7. A **two-way ANOVA** with condition × spec is run per metric to test
   whether condition effects are stable across task domains. A
   significant interaction is itself a finding (some agents are better
   at some task types) and is reported as such.

The replay-mode constraint (deviation 001) is handled by excluding
those cells from variance estimates but including them in ranked
comparisons. The reporting policy is: every reported difference
includes mean ± 95 % CI, effect size, exact *p*-value, and the cell N
used in the comparison.

## 3.7 Reproducibility infrastructure

The instrument is shipped as a Python package on PyPI
(`ai-code-quality-auditor`, version 0.2.0+) and a GitHub Action
(`dominicrume/NEW-enterprise-ai-code-quality-auditor@v1`). The full
main study is reproducible from a clean machine in three commands:

```bash
pipx install ai-code-quality-auditor
git clone <repo>
auditor experiment --reps 10 --run-label replication_001
```

The dissertation's headline CSV is committed to the repository at
`data/reports/main_001.csv` with an accompanying
`main_001.provenance.json` documenting the model versions, prompt
hashes, and per-run durations. A live read-only dashboard at
[auditor-dashboard-rume.fly.dev/report/main_001](https://auditor-dashboard-rume.fly.dev/report/main_001)
renders the same CSV with banner provenance that auto-flips from
"Pilot data" to "Dissertation result" when N ≥ 5 per condition is
reached — a structural guard against misrepresenting pilot data as a
dissertation result.

---

*Word count: ~2,500. Next: Chapter 4 — Results.*
