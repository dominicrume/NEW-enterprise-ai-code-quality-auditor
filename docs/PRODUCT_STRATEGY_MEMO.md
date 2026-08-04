# Product Strategy Memo

## AI Code Quality Auditor

### Executive summary
AI Code Quality Auditor is an AI assurance product for organizations adopting agentic coding tools. Its value is not benchmarking for its own sake; it gives leadership a practical, evidence-backed method for deciding whether an AI coding tool is safe, governable, and worthy of adoption — *before* it reaches production. This memo restructures the strategy around the narrative agreed with our supervisor for the Alix Partners engagement: **problem → solution → credibility → outcome → differentiation**.

### 1. Problem
Organizations are adopting AI coding tools faster than they can assure them. They lack a reliable way to evaluate whether these tools:
- remain aligned to the specification they were given
- produce secure, maintainable code
- avoid scope drift — shipping features nobody asked for
- behave predictably under governance constraints

Existing approaches answer the wrong question. Benchmarks ask "can AI write code that runs?" The adoption decision needs: "will *this* tool behave safely and stay governable on *our* work?"

### 2. Solution
A decision-support platform built as three product layers:

1. **Evaluation engine** — five independent analyzers (security density, cyclomatic complexity, duplication, hallucination/scope drift, interaction dynamics), each scoring output against one fixed, versioned specification. One file per metric, one adapter per vendor — the architecture enforces comparability.
2. **Executive dashboard** — a live, decision-friendly interface that turns the five metrics into an understandable comparison across tools, deployed and clickable today.
3. **Deployment layer** — CLI, reproducible runs, provenance-stamped CSV/JSON reports, and replay adapters for vendors without programmatic access.

The experimental design is the moat: the same specification is given to multiple AI tools **and a human control baseline**, so every number has a comparator.

### 3. Credibility of the solution
Credibility is the product. Five design decisions make the evidence defensible:

1. **Fixed, externalised specification** — no tool sees a different task; specs are versioned, never modified mid-experiment.
2. **Deterministic, reproducible measurement** — local Bandit for security (version-pinnable, no external infrastructure), AST-based complexity, language-agnostic duplication detection.
3. **Provenance on every result** — each CSV ships with a provenance JSON tracing results back to spec, adapter, and analyzer versions.
4. **Validated labels** — hallucination findings are checked with blind hand-labelling and Cohen's kappa inter-rater reliability, not taken on faith from a heuristic.
5. **Documented limitations** — pilot sample size, Python-only complexity scope, and mid-pilot methodology changes are written up openly (docs/PILOT_RESULTS.md), which is what makes the instrument credible to a technical audience.

Pilot evidence already shows the instrument surfacing real risk: one tool shipped an off-spec endpoint and an unrequested test suite, and triggered a CWE-tagged security finding — while a competing tool on the identical task stayed strictly in scope. That difference is invisible to functional testing and is precisely the signal an adoption decision needs.

### 4. Outcome — the journey so far
- **Started with:** a dissertation research question and a YAML spec box.
- **Built:** the full pipeline — spec → per-vendor adapter → capture contract → five analyzers → CSV → live dashboard (https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human).
- **Proved:** three of five conditions captured end-to-end; meaningful, explainable differences between tools on identical work.
- **Hardened:** two analyzers rewritten when pilot data exposed structural bias — the security metric moved from SonarCloud to local Bandit, and hallucination detection gained an auto-derived manifest. Finding and fixing our own measurement flaws is part of the credibility story, not a weakness.

### 5. Differentiation — why this and not what already exists
This section responds directly to supervisor feedback: *"if something is already available in the market, why would your product be used?"*

| Market category | What it does | What it cannot do |
|---|---|---|
| Static analysis (SonarQube, Bandit) | Scores a codebase for issues | Cannot compare *tools*; no controlled conditions; no spec alignment; no human baseline. We use these as instruments inside the experiment. |
| AI benchmarks (SWE-bench, HumanEval) | Pass rates on public tasks | Public tasks, not your spec; functional success only; blind to scope drift, governance, maintainability. |
| Post-adoption analytics (productivity dashboards, DORA metrics) | Measures impact after rollout | The decision has already been made; risk has already been taken. |
| **AI Code Quality Auditor** | **Pre-adoption, spec-anchored, five-metric comparison of AI tools against a human baseline** | — |

The distinctive capability nothing else offers: **measuring hallucination as scope drift against a fixed specification**, with provenance, under controlled conditions.

### 6. Target users
Primary: engineering leaders, AI adoption/governance teams, risk stakeholders, and consulting partners advising on AI tooling. Secondary: researchers and internal audit teams.

### 7. Commercial routes
- **Partner-led evaluation programs** — the immediate Alix Partners opportunity, positioned in their own published language (see docs/ALIX_PARTNERS_INTELLIGENCE.md): their 2026 predictions report tells clients to invest 10–30% of budgets in *trust infrastructure* to escape the "AI Productivity Paradox" (20–30% dev acceleration that fails to convert to ROI). This platform is that trust infrastructure made concrete — a repeatable, billable evaluation their consultants can run for clients making adoption decisions, and a QA gate for their own Claude-based AI delivery work.
- **Enterprise pilots** — custom specs reflecting a client's own governance rules.
- **Self-serve** — CLI and dashboard for engineering teams running internal audits.

### 8. Roadmap priorities
Short term: presentation-ready demo (live + screen-recorded backup), main-study data collection (K ≥ 5 per condition), capture of the two deferred vendor conditions via replay adapters.
Medium term: reusable enterprise evaluation templates, guided workflows, richer executive reporting.
Long term: the broader AI assurance platform for software delivery — the trust layer for AI-assisted engineering.

### Key message
"This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."
