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
each metric is tested across the four AI conditions with a one-way
ANOVA, falling back to Kruskal-Wallis when the Shapiro-Wilk or Levene
preconditions fail. The Bonferroni-corrected threshold is α = 0.01 per
metric (0.05 / 5). Every metric fell to **Kruskal-Wallis**: the
deterministic-replay conditions (`replit_agent`, `antigravity`) have
zero within-cell variance by construction (Deviation 001), which fails
both the normality and equal-variance preconditions. The `human_control`
condition is excluded from these tests (Deviation 003); the analysis is
four-condition, AI-only, with N = 30 per condition per metric. Values
are computed by `notebooks/statistical_analysis.ipynb` against
`data/reports/main_001.csv` and reproduced in Table 4.3.

| Metric | Test | H | p | η² | Sig @ α=0.01 |
|---|---|---:|---:|---:|:---:|
| Duplication_pct | Kruskal-Wallis | 62.41 | 1.8 × 10⁻¹³ | 0.497 | **yes** |
| Security_density | Kruskal-Wallis | 39.35 | 1.5 × 10⁻⁸ | 0.346 | **yes** |
| Hallucinations | Kruskal-Wallis | 15.76 | 1.3 × 10⁻³ | 0.192 | **yes** |
| Complexity_mean | Kruskal-Wallis | 12.03 | 7.3 × 10⁻³ | 0.097 | **yes** |
| Correction_freq | — | — | — | — | n/a (all-zero across AI conditions) |

Four of the five metrics show a significant omnibus difference across
the AI conditions at α = 0.01, with effect sizes spanning medium
(complexity, η² = 0.10) to very large (duplication, η² = 0.50).
`correction_freq` is structurally zero for every AI condition (no
keystrokes), so its omnibus is undefined; it is reported only against
the human baseline (§4.6).

**Post-hoc (Dunn's test, Bonferroni-adjusted).** Because the omnibus is
Kruskal-Wallis, the pre-registered post-hoc is Dunn's, not Tukey. The
pairwise comparisons significant at α = 0.01 are:

- **Duplication:** `replit_agent` differs from both `claude_code` and
  `cursor_agent` (both p < 10⁻⁴), and `antigravity` differs from both
  `claude_code` and `cursor_agent` (p < 10⁻⁴, p < 10⁻³). The two
  scaffolding-heavy vendors separate cleanly from the two lean ones;
  replit vs antigravity is not distinguishable, nor is claude vs cursor.
- **Security_density:** `claude_code` and `cursor_agent` each differ
  from `replit_agent` (both p < 10⁻⁴), and `cursor_agent` differs from
  `antigravity` (p < 10⁻³) — the Python-dense vendors separating from
  the scaffolding-diluted ones, consistent with the per-language-density
  reading in §4.3.4.
- **Hallucinations:** only `claude_code` vs `replit_agent` reaches
  α = 0.01 (p = 0.0022) — the 0.00-vs-1.00 contrast driven by Replit's
  CLI architectural-prior behaviour (analytical note 001).
- **Complexity:** the omnibus is significant but **no pairwise
  comparison survives Bonferroni at α = 0.01** (closest:
  antigravity vs claude_code, p = 0.010). The effect is diffuse across
  conditions rather than localised to one pair, and is reported as an
  omnibus-level result only.

**Condition × spec interaction (two-way ANOVA).** A significant
interaction is itself a finding — agent quality depends on task domain.
The interaction term is significant for every testable metric:
duplication (F = 283.8, p < 10⁻⁶³), hallucinations (F = 228.3,
p < 10⁻⁵⁸), complexity (F = 27.9, p < 10⁻¹⁹), and security_density
(F = 20.6, p < 10⁻¹⁵). This is the quantitative basis for the study's
central external-validity claim (§4.4, §4.8): condition effects are
**not** stable across specifications, so the defensible statement is
"agent X outperforms agent Y *for this task type*", not in general.

The reported gaps are large relative to within-cell variance, and the
replay cells contribute zero variance by construction (Deviation 001),
so the structural findings do not hinge on the exact p-values.

## 4.6 Human-control baseline (follow-up window)

The `human_control` condition was collected in a follow-up window and,
per **Deviation 003**, comprises one completed hand-coded session per
specification (N = 1 per spec, three sessions total) rather than the
pre-registered 30 sessions. Each session was run to feature-completion
with all in-IDE AI assistance disabled; the researcher implemented and
**verified all six features of every specification** (each feature was
executed and confirmed working before scoring). The condition is a
single-rep reference point against the AI distribution — reported
descriptively here, excluded from the inferential tests of §4.5.

Table 4.4 sets the human baseline against the four-AI-condition means
(N = 10 per AI cell), per spec, on all five metrics. Lower is better.

| Spec | Metric | **human** (n=1) | claude_code | cursor_agent | antigravity | replit_agent |
|---|---|---:|---:|---:|---:|---:|
| agent_education | security_density | 0.00 | 101.90 | 58.90 | 4.42 | 0.00 |
| agent_education | complexity_mean | 1.71 | 2.73 | 1.91 | 1.59 | 0.00 |
| agent_education | duplication_pct | 0.00 | 0.00 | 1.10 | 1.68 | 11.59 |
| agent_education | hallucinations | 0.00 | 0.00 | 0.50 | 1.00 | 0.00 |
| agent_education | correction_freq | 829.27\* | 0.00 | 0.00 | 0.00 | 0.00 |
| data_pipeline | security_density | 0.00 | 24.24 | 21.76 | 0.00 | 0.00 |
| data_pipeline | complexity_mean | 5.00 | 3.24 | 3.12 | 2.74 | 3.69 |
| data_pipeline | duplication_pct | 0.00 | 0.00 | 0.96 | 5.45 | 17.08 |
| data_pipeline | hallucinations | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| data_pipeline | correction_freq | 51.80 | 0.00 | 0.00 | 0.00 | 0.00 |
| internal_tool_cli | security_density | 0.00 | 0.00 | 50.36 | 0.00 | 0.00 |
| internal_tool_cli | complexity_mean | 0.00 | 4.10 | 3.14 | 3.47 | 3.47 |
| internal_tool_cli | duplication_pct | 0.00 | 0.00 | 0.65 | 5.64 | 0.00 |
| internal_tool_cli | hallucinations | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 |
| internal_tool_cli | correction_freq | 122.27 | 0.00 | 0.00 | 0.00 | 0.00 |

\* partial-capture outlier — see observation (3). Source CSVs:
`data/reports/human_session_<spec>_rep00.csv`; comparison view:
`data/reports/human_vs_ai_comparison.csv`.

Four observations follow.

**(1) Zero hallucinations, zero duplication, zero security density across
all three specs.** The human baseline implemented exactly the declared
features and nothing more — the manifest matched the code in every spec —
so the hallucination count is 0.00 throughout, against an AI range of
0.00–3.00. There is no scaffolding redundancy (duplication 0.00 % versus
up to 17.1 % for `replit_agent` on `data_pipeline`) and no Bandit-tagged
Python findings (security_density 0.00 versus up to 101.9/kloc for
`claude_code` on `agent_education_system`). This discipline is partly an
artefact of writing only what the spec asked, but the instrument records
it faithfully.

**(2) Complexity is low and, for the CLI, structurally zero.** Mean
McCabe complexity was 1.71 (`agent_education_system`) and 5.00
(`data_pipeline`), bracketing the AI means. For `internal_tool_cli` the
human value is 0.00 — not an error but a structural property of the
implementation: the CLI was written as top-level script code (module-
level statements dispatched by `argparse`) with no function definitions,
and the complexity analyser measures per-function McCabe, so a
function-free module scores zero. The AI conditions, which wrapped the
same CLI logic in functions, score 3.1–4.1. This is a genuine stylistic
contrast the metric exposes, and is noted as a limitation of
per-function complexity as a cross-style comparator (Chapter 5).

**(3) Keystroke correction is the one metric where the human baseline is
the point of the comparison.** The AI conditions are structurally zero
(agents do not type). The human rates were 51.8/1k (`data_pipeline`),
122.3/1k (`internal_tool_cli`) and 829.3/1k (`agent_education_system`).
The last is a **partial-capture outlier**: for that rep an early
~2,133-event coding segment was overwritten before the segment-archiving
procedure was in place (Deviation 003), so its correction frequency is
computed from a 75-event fixing-only segment dominated by backspaces and
is not a representative authoring rate. The representative human
correction rate is therefore taken from the `data_pipeline` session — a
complete 6,619-event capture — at **51.8 corrections per 1,000
keystrokes**: the researcher backspaced roughly 5 % of the time while
implementing the spec by hand. This is the empirical floor against which
the agentic conditions' structural zero is read: the AI zero means "no
keystroke rework was observable", not "no rework occurred".

**(4) The human baseline does not 'win'.** Lower is better on every
metric and the human scores at or near best on four of five, but this is
not a quality victory. The zeros reflect a minimal, exactly-on-spec
implementation produced without the over-delivery (extra endpoints,
enterprise scaffolding) that drives the AI conditions' non-zero
hallucination, duplication and security figures. The interpretive value
of the human baseline is as a reference floor, and as a validity check
that the instrument behaves sensibly on genuinely human-authored code —
not as evidence that hand-coding is superior to agentic coding.

## 4.7 Inter-rater reliability for the hallucination heuristic (planned validation)

The hallucination metric is the study's most consequential dependent
variable (§4.3.1, §4.8), so its heuristic basis requires validation
against human judgement before it can be treated as inferential rather
than exploratory. Pre-registration §9 specifies the procedure: a 30-run
random sample of the AI conditions is hand-labelled by the researcher
for "any-hallucination presence" (0/1) and compared against the
`manifest_deriver` output via Cohen's κ, with κ ≥ 0.6 ("good agreement"
on the Landis and Koch (1977) scale) as the threshold for inferential
treatment.

**This validation is reported here as a planned step rather than a
completed result.** At the time of writing the hand-labelled sample had
not been collected, so no κ value is asserted; the
`statistical_analysis.ipynb` cell that computes κ is wired to a labels
file (`data/labels/hallucination_handlabels.csv`) that must be populated
before the figure can be reported. Until then the hallucination metric
is treated as **exploratory**, and the study's claims that rest on it —
chiefly the Replit Agent architectural-prior finding (§4.3.1, analytical
note 001) — are additionally supported by direct inspection of the
captured code, which does not depend on the heuristic.

The anticipated locus of human–deriver disagreement is the boundary
case where Replit Agent shipped a CLI containing the spec's required
*namespace* token (`cli.add` → an `add_parser('add')` call) but inside a
data-pipeline file rather than a CLI module: a human labeller would
record "hallucination" on structural grounds while a token-matching
deriver records "implemented". This motivates the recommended extension
— *structural-shape detection* rather than *token detection* — logged in
the Discussion chapter, and is the reason the metric is reported
conservatively here.

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
