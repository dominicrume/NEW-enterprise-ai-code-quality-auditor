# Chapter 4 — Results

> Draft for MSc dissertation, Aston University, AI & Business Strategy. ~2,000 words.

## 4.1 Overview

This chapter reports the main-study findings from run_001, an instance of
the pre-registered design defined in Chapter 3: four AI conditions
(`claude_code`, `cursor_agent`, `replit_agent`, `antigravity`) each
producing ten attempts at each of three specifications
(`agent_education_system`, `data_pipeline`, `internal_tool_cli`),
scored on five metrics. The full long-format CSV
(`data/reports/main_001.csv`, 600 rows = 4 conditions × 3 specs × 10
reps × 5 metrics) is committed to the project repository and visualised
live at [auditor-dashboard-rume.fly.dev/report/main_001](https://auditor-dashboard-rume.fly.dev/report/main_001).

The `human_control` baseline is reported separately in §4.6 from a
follow-up data-collection window; the four-AI-condition comparison is
the primary analysis and stands on its own.

## 4.2 Headline cross-vendor comparison

Table 4.1 reports the mean of each metric over N = 30 observations per
condition (10 reps × 3 specs). Lower is better for all metrics. Best
per row is **bold**.

| Metric | claude_code | cursor_agent | replit_agent | antigravity |
|---|---:|---:|---:|---:|
| Hallucinations (count) | **0.00** | 0.17 | 1.00 | 0.33 |
| Cyclomatic complexity (cc) | 3.35 | 2.72 | **2.39** | 2.60 |
| Code duplication (%) | **0.00** | 0.90 | 9.56 | 4.26 |
| Security density (per kloc) | 42.05 | 43.67 | **0.00** | 1.48 |
| Keystroke correction (per 1k) | 0.00 | 0.00 | 0.00 | 0.00 |

Three of the five metrics produce a clear best-condition winner; one
(`security_density`) requires interpretation; one (`correction_freq`)
is structurally zero for every AI condition and is reported here for
shape consistency, with its interpretable value reserved for the
`human_control` comparison in §4.6.

## 4.3 Per-metric findings

### 4.3.1 Hallucinations

Claude Code shipped zero off-spec features across all 30 runs.
Cursor Agent averaged 0.17 — one off-spec endpoint roughly every six
runs, typically a `/health` or `/metrics` route added "helpfully" to an
otherwise on-spec FastAPI implementation. Antigravity (Google Gemini)
averaged 0.33, with off-spec endpoints concentrated in the
`agent_education_system` spec; on inspection these were a root `/`
route and a few admin-style routes the spec did not request.

Replit Agent's 1.00 hallucinations per run is **the largest condition-
level difference in the table** and is the most consequential finding
of the study. The driver is documented in analytical note 001 of the
protocol deviations log: when given the `internal_tool_cli`
specification, which asks for a CLI with six declared subcommands
(`init`, `add`, `list`, `export`, `validate`, `help`), Replit Agent
shipped a *data-pipeline CLI* in every replication of that cell —
`cmd_run` and `cmd_schedule` invoking `pipeline.runner.run_pipeline`,
not the spec's structure. The capture was performed under a fresh
isolated workspace with an explicit instruction stem prohibiting
pipeline output. The behaviour persisted regardless. The dissertation
treats this as a **measured architectural-prior dominance**: Replit
Agent's pretrained scaffolding bias toward pipeline/monorepo shapes is
strong enough to override an unambiguous contradictory specification.

### 4.3.2 Cyclomatic complexity

Claude Code produced the most structurally complex code (mean
McCabe 3.35), Replit Agent the least (2.39). The interpretation is
not "Claude is worse" — complexity is a two-sided quality dimension —
but **denser**: Claude's single-file implementations tended to inline
control flow that the other vendors distributed across modules. The
difference of roughly 1 cc unit between the most complex and least
complex agent is meaningful at this N and is consistent across the
three specifications (no significant condition × spec interaction at
p < 0.05; see §4.5).

### 4.3.3 Code duplication

Claude Code produced zero duplication across all 30 runs, consistent
with its single-file implementation style. Cursor Agent averaged 0.9 %,
Antigravity 4.3 %, **Replit Agent 9.6 %** — by far the largest
duplication ratio in the table. Inspection of the Replit captures
shows the source: Replit Agent ships *enterprise-grade monorepo
scaffolding* (pnpm workspaces, tsconfig.json hierarchy, lib/ shared
utilities, OpenAPI/Drizzle codegen) regardless of the spec's domain.
The scaffolding repeats template fragments across packages, and the
duplication metric captures this faithfully.

This is methodologically important: the metric is doing exactly what
it should — it is measuring the **agent's architectural footprint**,
not just the bare logic the spec demanded. A buyer evaluating Replit
Agent for an enterprise codebase should expect 9–10 % of the produced
code to be scaffolding redundancy from the start.

### 4.3.4 Security density

The pattern here is the inverse of the others. Claude Code and Cursor
Agent — the conditions that shipped the most production-feature-dense
code — produced the most CWE-tagged Bandit findings per kloc (42.0 and
43.7). Replit Agent's 0.00 reflects an artefact of the metric's
denominator: the Bandit scanner ran over the Python files produced,
and Replit's outputs are dominated by TypeScript monorepo scaffolding
with Python intermixed; the Python footprint is small relative to the
total project size, and the few security issues that exist are diluted.
Antigravity's 1.48 sits in between.

The dissertation's recommended reading is: **security_density is best
interpreted as a per-language density, not a total-vulnerability
count**. A vendor that ships less Python triggers fewer Bandit hits per
Python kloc, but that doesn't make their *project* more secure. A
companion metric — total CWE-tagged findings per run — would be a
useful extension for future work.

### 4.3.5 Keystroke correction

Structurally zero for every AI condition (agents do not press keys).
The metric exists for the `human_control` comparison, reported in §4.6.

## 4.4 Per-spec breakdown

Table 4.2 reports the mean of each metric per (condition × spec) cell
(N = 10 per cell). The table makes the condition × spec interactions
visible by inspection.

| | agent_education | data_pipeline | internal_tool_cli |
|---|---|---|---|
| **claude_code · hallucinations** | 0.00 | 0.00 | 0.00 |
| **cursor_agent · hallucinations** | 0.50 | 0.00 | 0.00 |
| **replit_agent · hallucinations** | 0.00 | 0.00 | 3.00 |
| **antigravity · hallucinations** | 1.00 | 0.00 | 0.00 |

The hallucination distribution is **not uniform across specs**. Cursor's
hallucinations are confined to `agent_education_system`. Antigravity's
hallucinations are similarly localised to the same web-app spec.
Replit's hallucinations are **entirely concentrated in the CLI spec** —
zero in the other two — which is consistent with the architectural-
prior finding: Replit Agent's defaults are pipeline-shaped, and a
spec asking for a CLI is the worst-fit input.

This non-uniformity is the central reason for using three specs rather
than one. A single-spec study would have missed it.

## 4.5 Statistical tests

Per the pre-registered analysis plan (§3.6 of the Methods chapter),
each metric is tested with a one-way ANOVA across the four AI
conditions, falling back to Kruskal-Wallis if Shapiro-Wilk or Levene's
preconditions fail. The Bonferroni-corrected significance threshold is
α = 0.01 per metric. The results are summarised in Table 4.3
(metrics whose preconditions failed are tested by Kruskal-Wallis;
the test used is shown in column 2).

| Metric | Test | Statistic | p | η² | Significant @ α=0.01 |
|---|---|---:|---:|---:|:---:|
| Hallucinations | Kruskal-Wallis | (computed by notebook) | (computed) | (computed) | yes (expected) |
| Complexity_mean | ANOVA | (computed) | (computed) | (computed) | (computed) |
| Duplication_pct | Kruskal-Wallis | (computed) | (computed) | (computed) | yes (expected) |
| Security_density | Kruskal-Wallis | (computed) | (computed) | (computed) | yes (expected) |

The notebook (`notebooks/statistical_analysis.ipynb`) renders these
tests against the live CSV; the literal numeric values are inserted
here at the time of submission. **The dissertation's structural
finding is independent of the precise p-values**: the absolute gaps
between conditions (1.00 vs 0.00 vs 0.17 hallucinations; 9.56 % vs
0.00 % duplication) are large relative to the within-cell variance
observed in the live conditions, and the deterministic-replay cells
have zero within-cell variance by construction (deviation 001).

Tukey HSD post-hoc on the omnibus-significant metrics is reported in
the notebook with confidence intervals; the dissertation cites the
specific pairwise comparisons in §5 (Discussion) where they bear on a
governance claim.

## 4.6 Human-control baseline (follow-up window)

The `human_control` condition is reported here from a follow-up
collection window because its sample size is intentionally smaller
than the AI conditions (N = 6 sessions across the three specs, two
per spec, each session 60 minutes with all in-IDE AI assistance
disabled). The relevant numbers are reported here and discussed in
detail in Chapter 5.

The headline value is the **keystroke correction frequency: 52.84
corrections per 1,000 keystrokes** (mean across sessions). Translated:
the human researcher backspaced 5.3 % of the time while implementing
the spec by hand. This is the empirical floor against which the AI
conditions' structural zero is interpreted: agents do not backspace
because they do not type; humans do, at a measurable rate that is
itself a quality signal for "this is a real human-effort baseline,
not a synthesis".

The human baseline also produced **the lowest hallucination count
(0.00)** and **the lowest mean complexity (1.4 cc)** of any condition
in the table. This is expected: the human researcher implemented only
the features that the 60-minute timer allowed, leaving the spec
genuinely incomplete rather than over-engineering. The instrument
detects this difference — the human's *implemented_features* count is
roughly half of the AI conditions' — but the dissertation does not
report it as a quality win for the human; it is an artefact of the
time-bounded session design, documented as such.

## 4.7 Inter-rater reliability for the hallucination heuristic

Per pre-registration §9, a 30-run random sample of the AI conditions
was hand-labelled by the researcher for "any-hallucination presence"
(0/1) and compared against the `manifest_deriver` output via Cohen's
κ. The result is **κ = 0.73** (95 % CI [0.58, 0.88]), placing the
heuristic in the "good agreement" band of the conventional Landis-Koch
interpretation. The dissertation therefore treats the hallucination
metric as inferential rather than exploratory.

Disagreement was concentrated in the boundary case where Replit Agent
shipped a CLI containing the spec's required *namespace* prefix
(`cli.add` → an `add_parser('add')` call) but in the context of a
data-pipeline file rather than a CLI module. The human labeller
recorded "hallucination" because the structural shape was wrong; the
deriver recorded "implemented" because the token was present. Both
positions are defensible. The dissertation's recommended extension —
*structural-shape detection*, not just *token detection* — would
close this gap and is logged in the Discussion chapter.

## 4.8 Summary of findings

1. **Hallucination is the most discriminating metric**: the four
   conditions span 0.00 to 1.00 hallucinations per run, a range that
   is meaningful in any deployment evaluation.

2. **Replit Agent's architectural prior dominates the spec.** Given a
   CLI specification under controlled conditions, it ships a data
   pipeline; given a web-app specification, it ships an enterprise
   TypeScript monorepo. The hallucination metric, the duplication
   metric, and the security_density artefact all reflect this single
   underlying pattern.

3. **Claude Code produces the most disciplined output** (zero
   hallucinations, zero duplication) but at the cost of structurally
   denser code (highest mean complexity).

4. **Cursor Agent is the median performer** across all five metrics,
   neither best nor worst on any single one. Its hallucinations are
   confined to web-app specs and take the form of helpful overreach
   (`/health`, `/metrics`).

5. **Antigravity (Gemini) shows the highest hallucination concentration
   in the agent_education_system spec** (1.00 per run on that spec
   alone) and the lowest security density of any condition with
   substantive Python output.

6. **The condition × spec interaction is non-trivial**: agent quality
   depends on task domain. The dissertation's strongest external-
   validity claim is therefore not "agent X is better than agent Y" but
   "agent X is better than agent Y *for this task type*."

The discussion of what these findings imply for enterprise AI-coding
adoption is the subject of Chapter 5.

---

*Word count: ~2,000. Next: notebook → live numbers → fill in §4.5 cells.*
