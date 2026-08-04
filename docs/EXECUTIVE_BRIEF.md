# Executive Brief

## AI Code Quality Auditor — due diligence for AI coding tools
*The leave-behind for the Alix Partners briefing (Paul — technical consulting; Ollie — management consulting). Structure per supervisor guidance: what problem, how we solve it, the credibility of the solution, and the outcome.*

### 1. The problem we are solving
Enterprise adoption of AI coding tools is outpacing assurance. Before rollout, organizations need an answer to the question procurement can't outsource to a security questionnaire: **will this tool's output be safe, in-scope, and maintainable on our work?**

Functional success is not enough. A tool can pass every functional test and still:
- drift outside the requested scope (shipping features nobody asked for)
- introduce security-relevant patterns
- produce unmaintainable, redundant code

We found this gap through MSc dissertation research at Aston University: benchmarks tell you whether AI *can* write code; nothing on the market tells an organization whether a specific tool is *trustworthy on their own specification*.

### 2. How we solve it
The same fixed specification is given to multiple AI tools **and a human reference**, and every output is scored on five separately measured checks:

| Credibility check | What it measures | How |
|---|---|---|
| Security | Severity-unweighted, CWE-tagged findings per 1,000 lines of Python (per-language density, not a whole-project score) | Bandit static analysis, deterministic and version-pinned |
| Complexity | Structural density per function — read paired with duplication ("denser, not worse") | AST-based analysis (radon) |
| Duplication | % of lines in repeated blocks — repeated-block detection, works in any language | k-line shingle detection |
| Hallucination | Features shipped that the spec never asked for (scope drift) | Spec-vs-codebase comparison + direct code inspection |
| Rework | Correction behaviour — the human-vs-agent differentiator (zero for agents by construction) | Keystroke/agent-event capture |

Risk thresholds are client-configurable policy; the dashboard ships sensible default bands, not hard-coded verdicts. The platform is three layers: an **evaluation engine** (one analyzer per metric), an **executive dashboard** (live, clickable), and a **deployment layer** (CLI, reproducible runs, provenance-stamped reports).

### 3. The credibility of the solution
Every claim below is backed by a completed, pre-registered study — the analysis plan was locked before any data existed.

- **Real scale, honestly stated.** 66 captured tool sessions — 60 live CLI runs (two vendors × three tasks × ten runs) and 6 controlled IDE sessions (two IDE-bound vendors, captured once per task and replayed) — plus 3 human reference sessions, each scored on five checks: 600 metric rows.
- **The headline finding.** In a controlled, contamination-checked session, a leading agent was given a CLI specification with an explicit instruction prohibiting pipeline output — and shipped a data-pipeline application, confirmed by direct code inspection. A functional benchmark would have passed it: **the wrong product, built well.** Live multi-session re-capture is the immediate next step to establish stability.
- **Statistically supported, honestly framed.** All four testable metrics differ significantly between tools (Kruskal–Wallis, α = 0.01), and the winner flips with task type. Given the replay design, we treat the tests as supporting evidence; the structural findings rest on absolute gaps and code inspection.
- **The instrument audits itself.** One tool scored a perfect 0.0 on security; the instrument flagged the zero as a blind spot — the tool wrote almost none of the code the scanner reads — and reported it as an artefact, not a win.
- **Live evidence.** https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human

### 4. The outcome — where we started, where we are
- **Started with:** a research question and a YAML spec.
- **Now have:** a completed pre-registered study, a full dissertation, and a deployed end-to-end pipeline (spec → adapter → capture → five analyzers → CSV → live dashboard). The commercially decisive result: **no tool wins on every check** — adoption should be profile-based selection per task type, not a leaderboard.
- **Already distributed:** the instrument ships as a public CLI — `pip install ai-code-quality-auditor` (MIT-licensed, on PyPI) — with ~1,600 downloads since its May release, ≈250 in the past 30 days. Read honestly: raw pip counts include CI traffic, so this is a distribution signal, not a user count.
- **Honest delivery picture.** One evaluation today: ~2 days to write a client spec, one recorded session per candidate tool, analyzers run unattended. The platform is a validated prototype, not a product; a pilot is how productization gets scoped. The human reference is currently single-developer, author-executed (disclosed as a reference point, not a comparison); independent blinded participants, live re-capture of the IDE-bound vendors, and hallucination inter-rater validation (Cohen's kappa, protocol prepared) are the stated next steps.

### 5. How this differs from what is already in the market
- **SonarQube / Bandit / static analysis** score *a codebase*. We score *the tool that produced it* — under controlled, comparable conditions. Static analyzers are instruments inside our experiment, not competitors to it.
- **Benchmarks (SWE-bench, HumanEval)** measure functional success on public tasks — never your specification, and blind to scope drift and governance behaviour.
- **Post-adoption analytics** measure impact after the risk is already taken. We provide evidence *before* the decision.
- In our market scan we found no tool that measures **hallucination as scope drift against a fixed specification** with a human reference for comparison.

### 6. Why this fits Alix Partners
This lands on ground AlixPartners has already mapped: your 2026 predictions report prescribes trust infrastructure (10–15% of budgets, rising to 20–30% by 2027) to escape the AI Productivity Paradox — and this platform is that infrastructure made concrete for AI-assisted engineering. As a repeatable, spec-driven evaluation it packages naturally as a partner-led advisory offering: a consultant runs it against a client's own governance rules and returns evidence, not opinion. And a question rather than a claim: you build AI solutions for clients — is there an evidence gate you'd want on that output?

### The ask
One pilot: one engagement team, one specification written to a client's governance rules, four tools evaluated — results in six weeks. IP and productization are conversations that should follow a successful pilot, not precede it.

### Final message
"This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."
*(Hallway version: benchmarks measure whether AI can code; this measures whether you can trust it.)*
