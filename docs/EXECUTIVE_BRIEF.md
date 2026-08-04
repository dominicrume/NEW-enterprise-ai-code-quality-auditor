# Executive Brief

## AI Code Quality Auditor
*Prepared for the Alix Partners briefing (Paul — technical consulting; Ollie — management consulting), structured per supervisor guidance: what problem, how we solve it, the credibility of the solution, and the outcome.*

### 1. The problem we are solving
Enterprise adoption of AI coding tools is outpacing assurance. Organizations are rolling out agentic coding tools faster than they can answer the one question that matters before deployment: **"How do we know this tool is safe to adopt?"**

Functional success is not enough. A tool can pass every functional test and still:
- drift outside the requested scope (shipping features nobody asked for)
- introduce security vulnerabilities
- produce unmaintainable, over-complex code
- behave unpredictably under governance constraints

We stumbled on this gap through MSc dissertation research at Aston University: existing benchmarks tell you whether AI *can* write code, but nothing on the market tells an organization whether a specific tool is *trustworthy enough to adopt*.

### 2. How we solve it
We built a working platform that evaluates AI coding tools **against a fixed specification, before adoption** — the same task, given to multiple tools and a human baseline, scored on the same five checks:

| Credibility check | What it measures | How |
|---|---|---|
| Security density | CWE-tagged vulnerabilities per 1,000 lines | Bandit static analysis, deterministic and reproducible |
| Complexity | McCabe cyclomatic complexity per function | AST-based analysis (radon) |
| Duplication | % of lines inside duplicated blocks | Language-agnostic shingle detection |
| Hallucination | Features shipped that the spec never asked for | Spec-vs-codebase manifest comparison |
| Interaction dynamics | Correction behaviour during the session | Keystroke/agent-event capture |

The platform is three layers: an **evaluation engine** (five analyzers, one per metric), an **executive dashboard** (live, clickable), and a **deployment layer** (CLI, reproducible runs, exportable reports).

### 3. The credibility of the solution
This is where we differ from a slide-ware pitch — every claim is backed by a running instrument:

- **Real pilot data.** Three of five experimental conditions captured end-to-end (human control, Claude Code, Cursor Agent) against one fixed spec.
- **Real findings.** The instrument caught Cursor Agent shipping an off-spec `/health` endpoint and an unrequested test suite — genuine scope drift that functional testing would never flag. It caught a CWE-tagged security finding in the same condition. Claude Code stayed strictly in scope.
- **Honest methodology.** Every measurement is traceable: provenance files accompany every CSV, methodological changes are documented (including why we replaced SonarCloud with local Bandit mid-pilot), and hallucination labels are validated with blind hand-labelling and Cohen's kappa inter-rater reliability.
- **Live evidence.** The dashboard is deployed and clickable now: https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human

### 4. The outcome — where we started, where we are
- **Started with:** a research question and a YAML spec.
- **Now have:** a working end-to-end pipeline (spec → adapter → capture → five analyzers → CSV → live dashboard), pilot results that surface real adoption risks, and a defensible, documented methodology.
- **Next:** main study with K ≥ 5 sessions per condition, the two deferred vendor conditions captured via replay adapters, and partner pilots.

### 5. How this is different from what is already in the market
- **SonarQube / Bandit / static analysis** score *a codebase*. We score *the tool that produced it* — under controlled, comparable conditions. Static analyzers are instruments inside our experiment, not competitors to it.
- **Benchmarks (SWE-bench, HumanEval)** measure whether AI can solve public tasks. They say nothing about scope discipline, governance behaviour, or performance on *your* specification.
- **Post-adoption analytics** (productivity dashboards, DORA-style metrics) measure impact after rollout. We provide evidence *before* the adoption decision is made.
- No tool on the market measures **hallucination as scope drift against a fixed specification** with a human baseline for comparison. That is our distinctive contribution.

### 6. Why this serves Alix Partners' own agenda
*(Audience intelligence: docs/ALIX_PARTNERS_INTELLIGENCE.md)*

AlixPartners has already told the market what this platform delivers:
- Their **2026 enterprise software predictions** find AI accelerates development by 20–30% but the gains fail to convert — the **"AI Productivity Paradox"** — and prescribe that enterprises invest **10–30% of budgets in trust infrastructure**. This platform is trust infrastructure for AI-assisted engineering: the instrument behind the advice.
- Their **2026 Disruption Index** calls agentic AI adoption **"the great divider"** (51% of growth leaders vs 14% of the rest), with "lack of clarity or consensus" a top blocker. Five explainable credibility checks are precisely the clarity an adoption decision lacks.
- AlixPartners **delivers AI-built solutions to clients itself** (building with Claude under its Anthropic partnership) — so assurance of AI-generated code is also their own delivery-risk problem, and this platform can gate their own AI-assisted engagements.
- As a repeatable, spec-driven evaluation, it packages naturally as a **partner-led advisory offering**: a consultant runs it against a client's own governance rules and returns evidence, not opinion — results, not reports.

### Executive takeaway
We are not building another benchmark. We are building the trust layer that sits between "this AI tool looks impressive" and "we are prepared to deploy it."

### Final partner-facing message
"This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."
