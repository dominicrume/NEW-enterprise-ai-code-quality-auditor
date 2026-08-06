# One-Page Deck Outline — Alix Partners Briefing

*Timing target: ~6:15 spoken, leaving real slack inside the 7-minute maximum + Q&A. One idea per slide; at most three numbers on any slide. Slide numbers match docs/SLIDE_READY_NARRATIVE.md 1:1. Format note: content is template-ready for the Alix Partners DFP Design Factory format once Anusha confirms.*

## Slide 1 — Title (15 sec)
**AI Code Quality Auditor**
Due diligence for AI coding tools
*Before you adopt one, we run it against your own spec — and show you where it breaks your rules.*

## Slide 2 — The problem (40 sec)
**Adoption is outpacing assurance.**
- AI accelerates development 20–30%, but the gains fail to convert — the "AI Productivity Paradox"; the prescription: trust infrastructure (10–15% of budgets, rising to 20–30% by 2027) *(AlixPartners 2026 predictions — cited once, here)*
- Functional success is not enough — code that "works" can still be insecure, out of scope, or unmaintainable
- The unanswered question in every adoption decision: *"How do we know it's safe to deploy?"*

## Slide 3 — How we solve it (55 sec)
**Same spec. Multiple tools. Human reference. Five credibility checks.**
- One fixed, versioned specification given identically to each AI tool — and to a human reference
- The evaluation engine scores every output on five separately measured checks
- An executive dashboard turns the evidence into an adoption decision
- Three layers: evaluation engine → executive dashboard → deployment layer

## Slide 4 — The five levels of credibility check (55 sec)
**Every output is scored on five checks; each check flags risk:**
1. **Security** — CWE-tagged findings per 1,000 lines of Python (each finding tagged with its industry-standard weakness category; severity-unweighted density, not a whole-project score)
2. **Complexity** — structural density (read *paired with* duplication: denser is not automatically worse)
3. **Duplication** — repeated-block detection, works in any language
4. **Hallucination** — features shipped that the spec never asked for (scope drift)
5. **Rework** — correction behaviour; the human-vs-agent differentiator (zero for agents by construction)
*Risk thresholds are client-configurable policy — the dashboard ships sensible default bands, not hard-coded verdicts.*

## Slide 5 — The finding (50 sec — the beat of the talk)
**"Do not build a pipeline."**
**It built a pipeline.**
- In a controlled, contamination-checked session, a leading agent shipped a data-pipeline app against a CLI spec that explicitly forbade it — confirmed by direct code inspection
- **Every functional test would have passed it: the wrong product, built well.**
- The most disciplined tool shipped zero off-spec features and zero duplication across thirty live runs

## Slide 6 — Outcome: I started with this, I have come to this (45 sec)
**Started:** a research question and a YAML spec.
**Now:** a completed pre-registered study (analysis plan locked before any data) and a live platform.
- 66 captured tool sessions — four leading agents × three task domains — plus human reference sessions, each scored on all five checks
- No tool won every check; which tool to trust **depends on the task** — and we can show which
- Shipped and public: `pip install ai-code-quality-auditor` — ~1.6k PyPI downloads since the May release
- Every result carries provenance back to spec and analyzer versions

## Slide 7 — Demo (75 sec — live, with screen-recorded backup)
**Input → evaluation → evidence.**
1. Land on the dashboard: this is the platform
2. Show the input: the fixed YAML specification
3. Explain the flow: spec goes in → each AI tool builds against it → five analyzers score the output
4. Show the output: the comparison report — where each check flagged risk; point at the hallucination check catching the pipeline nobody asked for, and duplication exposing one tool's copy-pasted boilerplate
Live: https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human

## Slide 8 — Differentiation + the ask (60 sec)
**Why not just use what exists?**
- Static analysis (SonarQube) scores a *codebase*; we score the *tool*, under controlled conditions — static analyzers are instruments inside our experiment
- Benchmarks (SWE-bench) test public tasks for functional success — never *your* spec, blind to scope drift
- Post-adoption analytics measure impact after the risk is taken
- In our market scan we found no tool that measures scope drift against a fixed specification with a human reference
**The ask: one pilot.** One engagement team, one client spec, four tools evaluated — results in six weeks.
**Close (verbatim):** *"This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."*
Hallway version: benchmarks measure whether AI can code; this measures whether you can trust it.

---

## Anticipated Q&A (hold in reserve — "the questions you ask yourself about the outputs are the questions they will ask")

- **"What's your sample size?"** 66 captured tool sessions: 60 live CLI runs (two vendors × three tasks × ten runs each) plus 6 controlled IDE sessions (two IDE-bound vendors × three tasks, captured once and replayed for CSV-shape consistency), plus 3 human sessions — 600 metric rows. Where inference is supported — the two vendors captured live with full replication — duplication and code density differ significantly. For the four-tool comparison I report descriptive gaps, not significance, because the two IDE-bound vendors contribute one session per task; treating replayed rows as independent observations would be pseudoreplication, and I say so in the dissertation rather than wait to be asked.
- **"Was the pipeline behaviour reproduced across sessions?"** Honest answer: it is one controlled, contamination-checked session — the workspace was verified clean and the prompt explicitly forbade the pipeline shape — confirmed by direct code inspection. Live multi-session re-capture is the immediate next step; if it reproduces, the claim strengthens further.
- **"Which agent built the pipeline?"** The study is pre-registered and the dashboard is public: it was Replit Agent, on the CLI task. But the vendor is not the point — any tool's pretrained priors can override a spec; the instrument exists to catch when.
- **"42 security findings per 1,000 lines for your best tools — really?"** That's a severity-unweighted density of Bandit findings (asserts, bind-all-interfaces, and similar patterns count equally), per 1,000 lines of *Python* — a raw finding density, not "42 exploitable vulnerabilities." A severity-weighted, whole-project companion metric is the documented next step. And note the instrument flagged one tool's headline 0.0 as a blind spot (almost no scannable Python in its output), not a security win — it audits its own metrics.
- **"Who was the human baseline?"** The author — one developer, one session per task, disclosed on the slide as a reference point, not a statistical comparison. Even that expert backtracked roughly once every twenty keystrokes; that continuous self-correction is the reference we hold every tool against. Independent, blinded participants are the stated next step.
- **"Isn't hallucination detection just a heuristic?"** The headline finding is confirmed by direct code inspection, independent of the heuristic; a blind hand-labelling protocol (Cohen's kappa) is prepared for formal validation, and the production path forces adapters to emit explicit manifests.
- **"Why Bandit and not SonarQube?"** A documented mid-pilot correction: the SonarCloud design shared one numerator across conditions — structurally broken. Local Bandit gives per-condition isolation, determinism, and version-pinning. SonarQube still runs in CI on the platform's own code.
- **"What doesn't this cover?"** Data residency, licensing/IP contamination, vendor risk, seat cost — the checks procurement already runs. We measure output trustworthiness; we slot alongside those checks, not instead of them.
- **"So which tool should we buy?"** The wrong question — no tool wins everywhere, and which tool wins flips with the task. The right question is "which tool for which task, under which governance gates" — precisely what this instrument answers. That's why it's an advisory asset, not a leaderboard.
- **"How does this become a business?"** One evaluation today: ~2 days to write the client spec, one recorded session per candidate tool, analyzers run unattended. The platform is a validated prototype; the pilot is how we jointly scope productization. IP sits with the research programme — a conversation I'd want to follow a successful pilot, not precede it.
- **"Are those PyPI downloads real users?"** Honest answer: raw pip counts include CI and mirror traffic, so I read ~1,600 total (≈250/month) as a distribution signal, not an adoption count. Adoption evidence is the pilot path and the dashboard waitlist — the download curve just says the packaging works and people are pulling it.
