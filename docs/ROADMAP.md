# Roadmap

## Stage 1 — MSc dissertation (in progress)
Five analyzers, **five** adapters (refined from the four-condition design
in the submitted proposal — see `docs/DISSERTATION_LINKAGE.md` for the
note to supervisors), one spec, statistical comparison across the five
conditions. Submitted as the MSc thesis. The Referee Tool exists.

**Currently built (the instrument):**
- Five adapters (`human_control`, `claude_code`, `cursor_agent`,
  `antigravity`, `replit_agent`), each isolated per the engineering
  principles.
- Five analyzers: SonarQube security density, radon McCabe complexity,
  k-line shingle duplication, spec-manifest hallucination, keystroke
  correction frequency.
- KYA governance compliance checker (`auditor/governance/`) with a
  JSON-stable `ComplianceVerdict` ready for Stage 3 chain attestation.
- `auditor experiment` CLI: one spec → five conditions → one immutable
  CSV report.
- Statistical analysis notebook: Kruskal-Wallis omnibus +
  Bonferroni-corrected pairwise Mann-Whitney.

**Outstanding for Stage 1:**
- Execute the five-condition experiment against
  `specs/agent_education_system.yaml` on the developer's own machine using
  the real vendor CLIs/IDEs. Pilot data exists in `data/reports/` clearly
  labelled `pilot_*` — these exercise the pipeline but do not constitute
  the dissertation result set.
- Justify final replication count per condition (likely 3-5 runs) for
  non-parametric statistical power.

## Stage 2 — PhD extension (the "Beyond Pilots" answer)
The Capgemini Centre's Beyond Pilots framework identifies a proof-of-concept
trap: pilots that never reach production-grade. The auditor extends to close
that gap:

- **API security testing.** Add an analyzer that probes the deployed AI
  application's API surface (auth, rate-limit, injection) — beyond static
  code analysis.
- **Enterprise risk quantification.** Translate raw metric counts into a
  monetised risk score using sector benchmarks (e.g. average cost per
  data-breach incident class). The output a board can read.
- **Continuous audit mode.** The auditor runs against a live AI agent in
  production, not just against a one-shot generation.

## Stage 3 — KYA proof layer
Write each audit verdict to an immutable on-chain record (the patented KYA
framework, GB2611754.9). This is what makes audit results *provable* to a
regulator months or years later. Out of MSc scope; in PhD scope.
