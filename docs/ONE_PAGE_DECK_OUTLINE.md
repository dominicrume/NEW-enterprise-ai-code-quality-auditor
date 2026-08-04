# One-Page Deck Outline — Alix Partners Briefing

*Timing target: 5–7 minutes total + Q&A (per supervisor guidance). One idea per slide. Format note: may need to move into the Alix Partners DFP Design Factory template — Anusha is confirming; content below is template-ready.*

## Slide 1 — Title (15 sec)
**AI Code Quality Auditor**
From research instrument to executive AI assurance platform
*A practical system for deciding whether AI coding tools are safe, governable, and worthy of enterprise adoption.*

## Slide 2 — The problem (45 sec)
**Adoption is outpacing assurance — AlixPartners' own research says so.**
- AlixPartners' 2026 predictions: AI accelerates development 20–30%, but the gains fail to convert — the **"AI Productivity Paradox"**; the prescription is **trust infrastructure** (10–30% of budgets)
- AlixPartners' 2026 Disruption Index: agentic AI adoption is **"the great divider"** (51% of growth leaders vs 14% of the rest); "lack of clarity or consensus" is a top blocker
- Functional success is not enough — code that "works" can still be insecure, out of scope, or unmaintainable
- The unanswered question in every adoption decision: *"How do we know it's safe to deploy?"*

## Slide 3 — How we solve it (60 sec)
**Same spec. Multiple tools. Human baseline. Five credibility checks.**
- One fixed, versioned specification given identically to each AI tool and a human control
- Evaluation engine scores every output on five independent metrics
- Executive dashboard turns the evidence into an adoption decision
- Three layers: evaluation engine → executive dashboard → deployment layer (CLI, reports, pilots)

## Slide 4 — The five levels of credibility check (60 sec)
**Every output passes through five independent gates:**
1. **Security** — CWE-tagged vulnerability density (Bandit static analysis)
2. **Complexity** — McCabe cyclomatic complexity (maintainability)
3. **Duplication** — repeated-block percentage
4. **Hallucination** — features shipped that the spec never asked for (scope drift)
5. **Interaction dynamics** — correction behaviour during the session
*Plus method-level credibility: provenance on every result, versioned specs, blind hand-labelled hallucination checks (Cohen's kappa).*

## Slide 5 — Outcome: I started with this, I have come to this (60 sec)
**Started:** a research question and a YAML spec.
**Now:** a working end-to-end pipeline and live pilot evidence.
- 3 of 5 conditions captured end-to-end on one identical task
- Caught real scope drift: one tool shipped an off-spec `/health` endpoint + unrequested tests; a competitor stayed strictly in scope
- Caught a CWE-tagged security finding functional tests would miss
- Human baseline captured (52.8 corrections per 1,000 keystrokes) — the comparator no benchmark has

## Slide 6 — Demo (90 sec — live, with screen-recorded backup)
**Input → evaluation → evidence.**
1. Land on the dashboard: this is the platform
2. Show the input: the fixed YAML specification
3. Explain the flow: spec goes in → each AI tool builds against it → five analyzers score the output
4. Show the output: the comparison report — where each tool passed and failed the five credibility checks
Live: https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human

## Slide 7 — How this differs from what's already in the market (45 sec)
- **SonarQube / static analysis:** scores a *codebase*; we score the *tool* — under controlled, comparable conditions (static analyzers are instruments inside our experiment)
- **Benchmarks (SWE-bench, HumanEval):** public tasks, functional pass rates; blind to scope drift, governance, and *your* specification
- **Post-adoption analytics:** measures impact after the risk is already taken
- **Only this platform:** pre-adoption, spec-anchored, human-baselined evaluation of the tool itself

## Slide 8 — Closing message (30 sec)
**This is not another AI benchmark.**
It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption.
*Contact: Dominic Rume — AI Code Quality Auditor*

---

## Anticipated Q&A (hold in reserve — "the questions you ask yourself about the outputs are the questions they will ask")
- **"Sample size?"** Pilot proves the instrument, not the study; main study runs K ≥ 5 sessions per condition under a power calculation.
- **"Isn't hallucination detection just a heuristic?"** Auto-derived manifest validated by blind hand-labelling with Cohen's kappa; production path forces adapters to emit explicit manifests.
- **"Why Bandit and not SonarQube?"** Deliberate, documented switch: deterministic, version-pinnable, per-condition isolation — reproducibility over rule-set breadth.
- **"Why would a client use this over existing tools?"** Existing tools score code or measure productivity; none evaluates the tool pre-adoption against the client's own spec with a human baseline.
- **"How does this become a business?"** Partner-led evaluation programs, enterprise pilots with custom specs, self-serve CLI + dashboard.
- **"Why should AlixPartners care?"** Your predictions report tells clients to buy trust infrastructure; this is trust infrastructure for AI-assisted engineering — a repeatable, billable evaluation your consultants can run, and a QA gate for your own Claude-based AI delivery work. (Full audience mapping: docs/ALIX_PARTNERS_INTELLIGENCE.md)
