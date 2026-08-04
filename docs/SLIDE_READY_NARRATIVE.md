# Slide-Ready Narrative — Alix Partners Briefing

## Title
AI Code Quality Auditor: From Research Instrument to Executive AI Assurance Platform

*Audience: Alix Partners — Paul (technical consulting) and Ollie (management consulting). Ollie will view this through a management lens; Paul through a technical one — every slide carries both.
Timing: 5–7 minutes total, then Q&A. Storyline per supervisor guidance: what problem → how we solve it → credibility of the solution → outcome → demo → differentiation.
Logistics: trial run with Anusha next week; live demo with a screen-recorded backup; format may move to the Alix Partners DFP Design Factory template (pending confirmation).*

---

## Slide 1 — The problem (≈45 sec)
Title: Adoption is outpacing assurance
Key message: Organizations are rolling out AI coding tools faster than they can answer whether those tools should be trusted.
Points:
- AI coding tools are spreading fast, but there is no dependable way to evaluate trustworthiness before rollout
- Functional success is not enough — working code can still be insecure, out of scope, or unmaintainable
- Every adopting organization faces the same question: "How do we know it's safe to deploy?"
Speaker note: Open with *their* research, not our product — a consultant trusts their firm's numbers above all others. "AlixPartners' own 2026 predictions report found that AI accelerates software development by 20 to 30 percent — and that most enterprises fail to convert those gains. You called it the AI Productivity Paradox, and your prescription was trust infrastructure. Your Disruption Index calls agentic AI adoption the great divider. My work sits exactly in that gap: how does an organization know an AI coding tool is safe to deploy?" How I stumbled on it: dissertation research at Aston showed benchmarks measure whether AI *can* code — nothing measures whether a specific tool is *safe to adopt*. (Audience intelligence: docs/ALIX_PARTNERS_INTELLIGENCE.md.)

## Slide 2 — How we solve it (≈60 sec)
Title: Same spec. Multiple tools. Human baseline. Five credibility checks.
Key message: A controlled evaluation platform that tests AI coding tools against a fixed specification before adoption.
Points:
- One fixed, versioned YAML specification given identically to each AI tool — and to a human control baseline
- An evaluation engine scores every output on five independent metrics
- An executive dashboard turns technical evidence into an adoption decision
- Three layers: evaluation engine → executive dashboard → deployment layer
Speaker note: Stress the design, because the design *is* the answer to "why believe your numbers": nothing is compared unless it was produced under identical conditions. The human baseline is what turns tool scores into meaning — it is the comparator no benchmark has.

## Slide 3 — The five levels of credibility check (≈60 sec)
Title: Five independent gates for every output
Key message: Credibility is not one score; it is five separate, independently measured checks.
Points:
1. Security — CWE-tagged vulnerability density per 1,000 lines (Bandit static analysis)
2. Complexity — McCabe cyclomatic complexity (is the code maintainable?)
3. Duplication — percentage of lines in repeated blocks
4. Hallucination — features shipped that the specification never asked for (scope drift)
5. Interaction dynamics — correction behaviour captured during the session
Speaker note: This is the slide to slow down on — it is the direct answer to "what factors did you use to determine the credibility of your output, and how was it considered." Add the method-level layer verbally: every result ships with a provenance file tracing it to spec and analyzer versions, specs are versioned and never modified mid-experiment, and hallucination labels were validated with blind hand-labelling and Cohen's kappa. For Paul: each metric is one analyzer file, deterministic and version-pinnable. For Ollie: five gates translate directly into governance criteria a client can adopt.

## Slide 4 — Outcome: I started with this, I have come to this (≈60 sec)
Title: From a YAML file to live evidence
Key message: The journey itself is the proof the instrument works.
Points:
- Started with: a research question and one fixed specification
- Now: a full working pipeline — spec → adapter per vendor → capture → five analyzers → CSV → live dashboard
- Pilot: 3 of 5 conditions captured end-to-end on the identical task
- Real findings: one tool shipped an off-spec `/health` endpoint and an unrequested test suite; a competitor stayed strictly in scope; a CWE-tagged security finding surfaced that functional tests would never catch
- Human baseline captured: 52.8 corrections per 1,000 keystrokes
Speaker note: Tell it as "I started here and I ended here." Include the honest middle: pilot data exposed two structurally biased analyzers, and I rewrote them — security moved from SonarCloud to local Bandit, hallucination detection gained an auto-derived manifest. Finding and fixing my own measurement flaws, and documenting them, is what makes the instrument credible rather than merely impressive.

## Slide 5 — Demo (≈90 sec — live, screen-recorded backup ready)
Title: Input → evaluation → evidence
Key message: This is not a mock-up; the platform runs today.
Demo script (matches supervisor guidance: land on the page, show the inputs, explain the flow, show the output):
1. **Land on the dashboard** — "This is the platform."
2. **Show the input** — the fixed YAML specification: six features, three governance rules, four guardrails.
3. **Explain the flow** — "This spec goes in; each AI tool builds against it; the five analyzers score what comes out."
4. **Show the output** — the comparison report: where each tool passed and failed the five credibility checks; point at the off-spec endpoint the instrument caught.
Live URL: https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human
Speaker note: Rehearse to 90 seconds flat. If the live site misbehaves, switch to the recording without comment. Weave the five checks into the walkthrough rather than listing them again — "and here is where the hallucination gate caught the endpoint nobody asked for."

## Slide 6 — How this differs from what is already in the market (≈45 sec)
Title: Why not just use what exists?
Key message: Everything on the market scores code or measures productivity; nothing evaluates the tool itself, pre-adoption, against your own specification.
Points:
- SonarQube / static analysis: scores a codebase, not a tool; no controlled conditions, no spec alignment, no human baseline — we use static analyzers as instruments *inside* the experiment
- Benchmarks (SWE-bench, HumanEval): public tasks and functional pass rates; blind to scope drift and governance, and never run on *your* spec
- Post-adoption analytics (productivity dashboards, DORA metrics): measure impact after the risk has already been taken
- Only this platform: pre-adoption, spec-anchored, human-baselined evaluation — and nothing else on the market measures hallucination as scope drift against a fixed specification
Speaker note: This slide answers the supervisor's direct challenge: "if something is already available in the market, why would your product be used?" Keep it respectful — SonarQube is excellent at what it does; it simply answers a different question.

## Slide 7 — Closing message (≈30 sec)
Title: The trust layer for AI-assisted engineering
Key message (deliver verbatim):
"This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."
Speaker note: Before the verbatim message, land the self-interest bridge in one sentence: "Your firm told the market that the winners will invest in trust infrastructure — this is what trust infrastructure for AI-assisted engineering looks like, when it really matters." Then deliver the message verbatim and stop talking. Leave the room in the Q&A.

---

## Anticipated Q&A
*Preparation principle from the supervisor: "When you see those outputs, what questions do you ask yourself? Those similar questions they will ask."*

**"Your sample size is one run per condition — how is that credible?"**
It is a pilot, and I present it as one: it proves the instrument end-to-end, not the study. The main study runs K ≥ 5 sessions per condition under a power calculation derived from the pilot variances.

**"Hallucination detection sounds like a heuristic — how do you trust it?"**
The auto-derived manifest is a heuristic, and I validated it: blind hand-labelling with Cohen's kappa inter-rater reliability, and the pilot's flagged hallucination was manually confirmed as genuine scope drift. The production path forces each adapter to emit an explicit manifest.

**"Why Bandit rather than SonarQube for security?"**
A documented mid-pilot decision: the SonarCloud approach shared one numerator across conditions — structurally broken. Local Bandit gives per-condition isolation, determinism, and version-pinning. Narrower rule set, but reproducible — the right trade-off for an evidential instrument. SonarQube still runs in CI on the platform's own code.

**"Two of your five conditions are missing."**
A vendor-access constraint, not an instrument limitation: those tools have no public CLI. Replay adapters are built and unit-tested; both conditions will be captured from in-IDE sessions.

**"Only Python is scored for complexity?"**
A documented scope limitation of the MSc phase; the duplication metric is already language-agnostic, and the architecture (one analyzer per metric) makes language extension additive, not structural.

**"How does this become a business?"**
Three routes: partner-led evaluation programs (the Alix Partners opportunity — a repeatable offering consultants run for clients), enterprise pilots with client-specific specs, and self-serve CLI + dashboard for internal audit teams.

**"What's in it for AlixPartners specifically?"**
Three things. First, your own predictions report tells clients to invest 10–30% of budgets in trust infrastructure — this is that infrastructure made concrete, so it turns advice you already give into an engagement you can deliver. Second, your Disruption Index says lack of clarity blocks 39% of transformations — five explainable credibility checks are clarity a board can act on. Third, AlixPartners builds AI solutions for clients itself; this platform can gate the quality of your own AI-assisted delivery before a client ever sees it.

**"What would it take to run this on our client's stack?"**
A spec written against the client's governance rules, an adapter session per candidate tool, and the analyzers run unchanged. The spec is externalised by design — no code changes needed to evaluate a new task.
