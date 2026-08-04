# Product Strategy Memo

## AI Code Quality Auditor

*Internal commercial appendix. The Executive Brief (docs/EXECUTIVE_BRIEF.md) is the sole partner leave-behind; this memo holds the strategy detail the brief deliberately omits — target users, commercial routes, roadmap.*

### Executive summary
AI Code Quality Auditor is an AI assurance product for organizations adopting agentic coding tools — in one line: **due diligence for AI coding tools**. Its value is not benchmarking for its own sake; it gives leadership a practical, evidence-backed method for deciding whether an AI coding tool is safe, governable, and worthy of adoption — *before* it reaches production. This memo restructures the strategy around the narrative agreed with our supervisor for the Alix Partners engagement: **problem → solution → credibility → outcome → differentiation**.

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

The experimental design is the moat: the same specification is given to multiple AI tools **and a human reference** (currently single-developer, disclosed as a reference point rather than a statistical comparison), so tool scores are read against something other than each other.

### 3. Credibility of the solution
Credibility is the product. Five design decisions make the evidence defensible:

1. **Fixed, externalised specification** — no tool sees a different task; specs are versioned, never modified mid-experiment.
2. **Deterministic, reproducible measurement** — local Bandit for security (version-pinnable, no external infrastructure), AST-based complexity, language-agnostic duplication detection.
3. **Provenance on every result** — each CSV ships with a provenance JSON tracing results back to spec, adapter, and analyzer versions.
4. **Triangulated findings** — the headline hallucination result is confirmed by direct code inspection (independent of the detection heuristic); the heuristic itself is reported as exploratory pending blind hand-label validation (Cohen's kappa, protocol prepared), and the CLI-shape detector added in response to the observed behaviour is logged as an analytical note.
5. **Documented limitations** — the replay design for IDE-bound vendors, the single-developer human reference, Python-only complexity scope, and mid-study methodology corrections are written up openly, which is what makes the instrument credible to a technical audience.

The completed main study — 66 captured tool sessions (60 live CLI runs plus 6 controlled IDE sessions across four leading agents and three task domains), each scored on five checks, 600 metric rows — shows the instrument surfacing risk no functional benchmark can see. The starkest result: in a controlled, contamination-checked session, one leading agent was given a CLI specification that explicitly prohibited pipeline output and shipped a data-pipeline application anyway, confirmed by direct code inspection (live multi-session re-capture is the immediate next step). Meanwhile the most disciplined tool shipped zero off-spec features and zero duplication across its thirty live runs. All four testable metrics differ significantly between tools, the winner flips with task type, and — given the replay design — the tests are treated as supporting evidence behind the absolute gaps: the empirical basis for selling *profile-based selection*, not leaderboards.

### 4. Outcome — the journey so far
- **Started with:** a dissertation research question and a YAML spec box.
- **Built:** the full pipeline — spec → per-vendor adapter → capture contract → five analyzers → CSV → live dashboard (https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human).
- **Proved:** a completed, pre-registered cross-vendor study — 66 captured tool sessions across four commercial agentic tools and three specifications, plus human reference sessions, 600 metric rows — with large, explainable differences on identical work.
- **Hardened:** two analyzers rewritten when pilot data exposed structural bias (security: SonarCloud → local Bandit; hallucination: auto-derived manifest), and a headline "zero vulnerabilities" score in the main study flagged as a blind spot (the tool wrote almost none of the code the scanner reads) rather than reported as a security win. Finding and reporting our own measurement flaws is part of the credibility story, not a weakness.

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
- **Partner-led evaluation programs** — the immediate Alix Partners opportunity, positioned in their own published language (see docs/ALIX_PARTNERS_INTELLIGENCE.md): their 2026 predictions report tells clients to invest in *trust infrastructure* (10–15% of budgets, rising to 20–30% by 2027) to escape the "AI Productivity Paradox" (20–30% dev acceleration that fails to convert to ROI). This platform is that trust infrastructure made concrete — a repeatable, billable evaluation their consultants can run for clients making adoption decisions. Delivery reality, stated up front: ~2 days to write a client spec, one recorded session per candidate tool, analyzers unattended; the platform is a validated prototype, and a pilot is how productization gets scoped. The internal-QA angle (they build with Claude for clients) is raised in the room as a question, never asserted in writing.
- **Enterprise pilots** — custom specs reflecting a client's own governance rules.
- **Self-serve** — CLI and dashboard for engineering teams running internal audits.

### 8. Roadmap priorities
Short term: presentation-ready demo (live + screen-recorded backup), live multi-session re-capture of the two IDE-bound vendors (closing the replay limitation), hallucination inter-rater validation (Cohen's kappa), independent blinded human reference sessions.
Medium term: severity-weighted security companion metric, reusable enterprise evaluation templates, guided workflows, richer executive reporting.
Long term: the broader AI assurance platform for software delivery — the trust layer for AI-assisted engineering.

### Key message
"This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."
