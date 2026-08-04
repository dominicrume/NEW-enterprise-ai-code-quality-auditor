# Slide-Ready Narrative — Alix Partners Briefing

## Title
AI Code Quality Auditor: Due Diligence for AI Coding Tools

*Audience: Alix Partners — Paul (technical consulting) and Ollie (management consulting). Slide numbers match docs/ONE_PAGE_DECK_OUTLINE.md 1:1.
Timing: ~6:15 spoken against a 7-minute maximum — the slack is deliberate; transitions and demo page-loads eat it. Word budgets assume ~145 words/minute spoken.
Logistics: trial run with Anusha next week; live demo with a screen-recorded backup; format may move to the Alix Partners DFP Design Factory template (pending confirmation). Audience research: docs/ALIX_PARTNERS_INTELLIGENCE.md.*

---

## Slide 1 — Title (15 sec, ~30 words)
Say: "I'm Dominic. What I'm going to show you is due diligence for AI coding tools — before an organization adopts one, we test it against their own specification and show where it breaks their rules."

## Slide 2 — The problem (40 sec, ~90 words)
Title: Adoption is outpacing assurance
Say: "Your firm's 2026 predictions report found AI accelerates software development twenty to thirty percent — and that most enterprises fail to convert the gains. Your prescription was trust infrastructure. My dissertation research at Aston found the missing piece: benchmarks measure whether AI *can* code. Nothing measures whether a specific tool is *safe to adopt* — whether working code is also secure, in scope, and maintainable. Every adopting organization faces the same question: how do we know it's safe to deploy? That's the problem I built for."
Speaker note: This is the single AlixPartners citation in the talk — once is insight, four times is pandering. Let the slide bullets sit silently; don't read them.

## Slide 3 — How we solve it (55 sec, ~125 words)
Title: Same spec. Multiple tools. Human reference. Five checks.
Say: "The design is the answer to 'why believe your numbers.' One fixed specification — versioned, never modified mid-experiment — is given identically to each AI tool, and to a human reference who builds the same thing by hand. Nothing is compared unless it was produced under identical conditions. An evaluation engine then scores every output on five separately measured checks, and an executive dashboard turns that into an adoption decision. Three layers: the evaluation engine, the dashboard you'll see in a moment, and a deployment layer — command line, reproducible runs, exportable reports. The human reference is what turns tool scores into meaning: it's the comparator benchmarks don't have."
Speaker note: For Paul: one analyzer file per metric, deterministic, version-pinnable. For Ollie: the five checks map onto governance criteria a client can adopt. Deliver these only if asked.

## Slide 4 — The five levels of credibility check (55 sec, ~125 words)
Title: Five checks; each one flags risk
Say: "Check one: security — industry-standard weakness categories per thousand lines, a raw finding density, deliberately not severity-weighted. Two: structural complexity — read alongside duplication, because denser isn't automatically worse. Three: duplication — how much of the output is repeated boilerplate, in any language. Four — the one nobody else measures — hallucination: features the tool shipped that the specification never asked for. And five: rework — the correction behaviour that separates human effort from agent output. Thresholds aren't hard-coded verdicts; they're client-configurable policy, and the dashboard ships sensible defaults. Every result carries provenance back to the exact spec and analyzer versions that produced it."
Speaker note: This answers "what factors did you use to determine credibility of your output." Say "checks," never "gates" — there are no pass/fail constants in the instrument. Don't mention kappa here; it lives in Q&A with the honest "prepared, not collected" status.

## Slide 5 — The finding (50 sec, ~115 words — the beat of the talk)
Title: "Do not build a pipeline." It built a pipeline.
Say: "Here's the moment this stopped being an academic exercise. We gave a leading agent a command-line-tool specification. Six subcommands. A clean, contamination-checked workspace. And one explicit instruction: do not build a data pipeline. [pause] It built a data pipeline. We confirmed it by reading the code — the spec's subcommands aren't there; a pipeline runner is. And here is the part that matters to your clients: every functional test would have passed it. The wrong product, built well. Now picture that repo at a client: it passes CI, it ships, and six months later a security review asks who commissioned the streaming pipeline inside their command-line tool — and who signed it off."
Speaker note: Slow down. The pause after "do not build a data pipeline" is the whole talk. Do NOT say "ten times out of ten" — the replications of that cell are replays of one captured session (Deviation 001); if asked about reproduction, use the prepared Q&A answer honestly. The contrast line if time allows: "The most disciplined tool shipped zero off-spec features across thirty live runs."

## Slide 6 — Outcome: I started with this, I have come to this (45 sec, ~100 words)
Title: From a YAML file to live evidence
Say: "I started with a research question and one YAML file. Today: a completed, pre-registered study — the analysis plan was locked before any data existed — sixty-six captured tool sessions across four leading agents and three task domains, each scored on all five checks. Two results carry the story: the finding you just saw, and this — no tool won on every check. Which tool to trust depends on the task, and the instrument shows which. It even caught its own blind spot: one tool's perfect zero on security was flagged as an artefact — it simply wrote almost none of the code our scanner reads — not a win. And the instrument is already out in the world: pip install ai-code-quality-auditor — about sixteen hundred downloads since May."
Speaker note: The self-audit beat in plain words — never say "denominator artefact" out loud. The honest-middle (analyzer rewrites) lives in Q&A, not here; it was cut for time.

## Slide 7 — Demo (75 sec — live, screen-recorded backup ready)
Title: Input → evaluation → evidence
Demo script (mentor's shape: land on page → inputs → flow → output):
1. **Land on the dashboard** — "This is the platform, live."
2. **Show the input** — "This is the specification: six features, three governance rules. This is everything every tool was told."
3. **Explain the flow** — "The spec goes in, each tool builds against it, five analyzers score what comes out."
4. **Show the output** — "And this is the evidence. Here's the hallucination check catching the pipeline nobody asked for. Here's duplication exposing one tool's copy-pasted boilerplate. And every number links back to the exact spec and analyzer version that produced it — that's the provenance."
Live URL: https://auditor-dashboard-rume.fly.dev/report/main_001_plus_human
Speaker note: Rehearse to 75 seconds flat. If the live site misbehaves, switch to the recording without comment.

## Slide 8 — Differentiation + the ask (60 sec, ~135 words)
Title: Why not just use what exists — and what I'm asking for
Say: "Fair question: doesn't this exist? SonarQube scores a codebase — it can't compare tools under controlled conditions; we use static analyzers as instruments inside the experiment. Benchmarks like SWE-bench test public tasks for functional success — never your specification, and blind to scope drift. Post-adoption analytics measure impact after the risk is already taken. In our market scan we found no tool that measures scope drift against a fixed specification with a human reference. So my ask is one pilot: one engagement team, one specification written to a client's governance rules, four tools evaluated, results in six weeks. [pause] This is not another AI benchmark. It is a practical assurance platform for trusted AI-assisted engineering that helps organizations decide whether an AI coding tool is safe, governable, and worthy of adoption."
Speaker note: The closing message is delivered verbatim, once, then stop talking. If a partner wants the hallway version afterwards: "Benchmarks measure whether AI can code. This measures whether you can trust it."

---

## Anticipated Q&A
*Preparation principle from the mentor: "When you see those outputs, what questions do you ask yourself? Those similar questions they will ask." The full prepared answers live in docs/ONE_PAGE_DECK_OUTLINE.md §Anticipated Q&A — rehearse from there. The five that matter most:*

1. **"Was the pipeline behaviour reproduced?"** — One controlled, contamination-checked session, confirmed by code inspection; the listed replications are replays (disclosed as Deviation 001). Live multi-session re-capture is the immediate next step. Never bluff this one — the honest answer is strong.
2. **"Which agent?"** — Replit Agent, on the CLI task; the study is pre-registered and the dashboard public. The vendor isn't the point — any tool's priors can override a spec; the instrument catches when.
3. **"Who was the human?"** — Me, disclosed as a single-developer reference point, not a comparison. Independent blinded participants are the stated next step.
4. **"42 security findings per 1,000 lines?"** — Severity-unweighted Bandit finding density on Python only — not "42 exploitable vulnerabilities." Severity-weighted companion metric is the documented next step.
5. **"Which tool should we buy?"** — Wrong question: no tool wins everywhere and the winner flips with the task. "Which tool for which task, under which governance gates" is what the instrument answers.
