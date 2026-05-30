# Dissertation Linkage

Every folder maps to a section of the MSc proposal.

| Proposal section                              | Where it lives                                   |
|-----------------------------------------------|--------------------------------------------------|
| §3 Research Aim & Objectives                  | `README.md`, `docs/METHODOLOGY.md`               |
| §4 Lit review — security & governance         | `auditor/analyzers/security_analyzer.py`, `auditor/governance/` |
| §4 Lit review — keystroke dynamics            | `auditor/analyzers/keystroke_analyzer.py`        |
| §4 Lit review — hallucination                 | `auditor/analyzers/hallucination_analyzer.py`    |
| §5 Methodology — experimental conditions      | `auditor/adapters/` (five adapters; see note)    |
| §5 Methodology — automated metrics            | `auditor/analyzers/`                             |
| §6 Ethics — synthetic data, no PII            | `docs/ETHICS.md`, `tests/fixtures/`              |
| §7 Risks — backups, scope                     | `data/` (gitignored, daily backup), `specs/`     |
| PhD extension (Beyond Pilots)                 | `docs/ROADMAP.md` Stage 2                        |

## Note on the five-condition refinement
The submitted proposal (March 2026) listed four conditions. During scaffolding
we identified that "Claude Code" (Anthropic) and "Replit Agent" (Replit) are
distinct vendor products and must be tested independently to produce a
defensible comparison. The corrected design has five conditions. Supervisors
Julien Barney and Kate Sugden to be notified before experimental execution
begins.
