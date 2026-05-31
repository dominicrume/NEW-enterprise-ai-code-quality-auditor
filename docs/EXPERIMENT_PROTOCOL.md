# EXPERIMENT_PROTOCOL — pre-registered dissertation study design

**Author:** Dominic Rume · MSc AI, Aston University
**Supervisors:** Julien Barney, Kate Sugden (JBKS1)
**Status:** Pre-registered. Committed *before* main-study data collection.
**Pre-registration timestamp:** This file's first git commit on `main`.

> **What pre-registration means.** Every metric, model version, sample size,
> and statistical test below is fixed in advance. Any deviation must be
> recorded in `docs/PROTOCOL_DEVIATIONS.md` with its reason, and reported
> in the dissertation Results chapter. This is what separates a pilot from
> a defensible dissertation result.

---

## 1. Research question

Do five AI-assisted coding workflows differ measurably across five
empirical quality metrics when implementing identical specifications?

### Hypotheses (two-sided)

For each of the five metrics M ∈ {hallucinations, correction_freq,
complexity_mean, duplication_pct, security_density}:

- **H₀(M):** All five conditions have the same population mean on M.
- **H₁(M):** At least one condition differs from the others on M.

Per-metric Bonferroni correction: α_per-test = 0.05 / 5 = **0.01**.

---

## 2. Independent variable — five conditions

Identical to the pilot, fixed for the main study:

| Condition | Vendor / product | Adapter |
|---|---|---|
| `human_control` | none (hand-typed baseline) | `human_control_adapter.py` |
| `claude_code`   | Anthropic Claude Code CLI | `claude_code_adapter.py` |
| `cursor_agent`  | Cursor Agent CLI          | `cursor_agent_adapter.py` |
| `replit_agent`  | Replit Agent (replay)     | `replit_agent_adapter.py` |
| `antigravity`   | Google Antigravity (replay) | `antigravity_adapter.py` |

### Model pinning (mandatory)

| Condition | Pinned model | Recorded where |
|---|---|---|
| claude_code | `claude-sonnet-4-6` (or current production tier at study start, recorded once and held) | `data/raw/<run_id>/<condition>/model.txt` |
| cursor_agent | `--model auto` (free tier limitation; documented as constraint) | as above |
| replit_agent | Replit Agent default at capture time (snapshot the version string visible in the IDE) | as above |
| antigravity | `Gemini 3.5 Flash (Medium)` (or whichever tier is held constant) | as above |

A model version change mid-study **invalidates that condition's run** and
the run must be re-collected on the original version (or, if unavailable,
the version change is documented and analysed as a separate condition).

---

## 3. Dependent variables — five metrics

Frozen at pilot definitions (see [METRICS.md](METRICS.md)).

| Metric | Unit | Direction | Analyser |
|---|---|---|---|
| Hallucinations           | count       | ↓ better | `hallucination_analyzer` (manifest + auto-derive) |
| Correction frequency     | per 1k keys | ↓ better | `keystroke_analyzer` |
| McCabe complexity (mean) | cc          | ↓ better | `complexity_analyzer` (radon) |
| Code duplication         | %           | ↓ better | `duplication_analyzer` (k=6 shingle) |
| Security density         | per kloc    | ↓ better | `security_analyzer` (local Bandit, CWE-tagged) |

---

## 4. Sample size & power calculation

| Quantity | Value | Rationale |
|---|---|---|
| Conditions (C)  | 5   | fixed |
| Specs (S)       | 3   | external-validity sweep |
| Reps per (C × S)| 10  | within-cell replication |
| **Total runs**  | **150** | C × S × reps |
| Reps per condition (across specs) | 30 | numerator of within-condition variance |

### Power justification

Target: detect a between-condition effect of Cohen's *f* ≥ 0.40 (medium-large)
with **80 %** power at α = 0.01 (Bonferroni-corrected per metric).

Using G*Power's one-way ANOVA module with 5 groups and *f* = 0.40,
α = 0.01, power = 0.80 → required N ≈ 95. Our N = 150 (30 per group)
exceeds this, giving > 90 % power and tolerating ~5 missing runs without
falling under the threshold.

---

## 5. Specs (three, pre-registered)

| Spec file | Domain | Why it's in the design |
|---|---|---|
| `specs/agent_education_system.yaml` | CRUD + auth (web app shape) | already piloted; familiar AI training-data shape |
| `specs/data_pipeline.yaml` | ETL + scheduled job (infrastructure shape) | tests whether agents do well *outside* web-app territory |
| `specs/internal_tool_cli.yaml` | CLI app with subcommands | tests structured-output and argument-parsing patterns |

Each spec has six features + cross-cutting governance rules. All three
share the same `external_apis: []` allowlist so the `no_external_calls`
governance rule is comparable across the design.

---

## 6. Procedure

### 6.1 Agent conditions

Run via `scripts/run_full_experiment.py`. The script:
1. Iterates `(condition × spec × rep)`, total 120 agent runs.
2. Uses a fresh work_dir per run (no state leakage).
3. **Disables vendor-side caching** where the API exposes it
   (Anthropic `disable_prompt_caching`; equivalent for others).
4. Persists per-run artefacts under `data/raw/<run_id>/<condition>/`.
5. Records wall-clock duration, model version, and prompt hash.
6. Randomises the order of `(condition × spec × rep)` triples to avoid
   time-of-day clustering of any single condition.

### 6.2 Human-control condition

Conducted by the researcher in VS Code with the `pynput` recorder.
- **Session length: 60 minutes per session**, capped strictly.
- 30 sessions total (3 specs × 10 reps), conducted over ≥ 5 calendar
  days to avoid intra-day fatigue effects.
- VS Code AI extensions disabled (Copilot, Cursor, Claude tab-complete)
  and verified before each session via a screen recording of the
  Extensions panel.
- Paste detected as a single OS event will be flagged in the log and
  the affected session is re-run.

### 6.3 Capture-contract artefacts (per run)

```
data/raw/<run_id>/<condition>/
├── codebase.json          # captured-codebase shape
├── interaction_log.json   # capture-contract events
├── raw_stream.json        # vendor-native (for forensics)
├── model.txt              # exact model version string
├── prompt.sha256          # hash of the prompt sent
├── duration_seconds.txt   # wall clock
└── code/                  # frozen tree
```

### 6.4 Blinded scoring

Scoring is performed by `auditor experiment --run-id <id>` from raw
artefacts only. The analyser never sees the condition label
(it's an enum the analyser pipeline doesn't read). The CSV row's
`condition` column is added by the orchestrator, not the analyser —
so blinding is structural, not procedural.

---

## 7. Statistical analysis plan

Implemented in `notebooks/statistical_analysis.ipynb`. The notebook is
written and tested *before* the data collection completes; it operates
purely on the CSV shape and will run unchanged on the real data.

### 7.1 Per-metric tests

For each metric:
1. **Normality check** per (condition, spec) cell via Shapiro-Wilk.
2. If all cells normal **and** Levene's test for equal variance passes:
   - **One-way ANOVA** across the 5 conditions.
   - If significant at α_per-test = 0.01: **Tukey HSD** post-hoc.
3. Otherwise:
   - **Kruskal-Wallis** across the 5 conditions.
   - If significant: **Dunn's test** post-hoc with Bonferroni adjustment.
4. **Effect size**: η² for the omnibus test, Cohen's *d* for pairwise.
5. **95 % CI** on each condition's mean, bootstrapped (10 000 resamples).

### 7.2 Spec-effect check

A two-way ANOVA per metric with `condition` and `spec` as factors, to
test whether condition effects are stable across specs (the interaction
term). A significant interaction is itself a finding (some agents are
better for some task types).

### 7.3 Multiple-comparison policy

- Bonferroni across the 5 metrics → α_per-metric = 0.01.
- Tukey HSD already corrects within-metric pairwise tests.

### 7.4 Reporting policy

Every reported difference must include: mean ± 95 % CI per condition,
effect size, exact *p* value (not just `< 0.05`), and the number of
runs used in the comparison. Negative results are reported in full.

---

## 8. Refusals, failures, timeouts

Treated as data, not missingness.

| Outcome | Recorded as | How it affects metrics |
|---|---|---|
| Agent refuses to attempt | `refusal=true` row in CSV | excluded from continuous metrics; counted in a separate refusal-rate analysis |
| Agent times out (15 min) | `timeout=true` row | as above |
| Agent runs but produces 0 files | `empty_output=true` row | included in metrics (real data: 0 features, 0 complexity, etc.) |

A condition with > 30 % refusals/timeouts is reported separately as a
**capacity finding** rather than a quality finding.

---

## 9. Inter-rater reliability for the hallucination heuristic

Before the main analysis, a 30-run random sample is hand-labelled by the
researcher for hallucinated endpoints. Cohen's κ between hand labels and
`manifest_deriver.derive()` output is reported in the Results chapter. If
κ < 0.6, the metric is reported as "exploratory only" rather than
inferential.

---

## 10. Deviations log

Any deviation from this protocol after the timestamp of this file's
first commit is recorded with:
- Date and time of decision
- What changed
- Why
- How it affects the analysis

Logged in `docs/PROTOCOL_DEVIATIONS.md` (one append-only entry per
deviation). If empty, no deviations occurred.
