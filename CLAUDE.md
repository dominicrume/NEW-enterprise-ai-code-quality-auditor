# CLAUDE.md — standing brief for Claude Code

You are helping build the **AI Code Quality Auditor**, the experimental
instrument for an MSc AI dissertation at Aston University (project JBKS1,
supervisors Julien Barney and Kate Sugden) and the working prototype for a
PhD application at the Aston-Capgemini Centre of Excellence for Enterprise AI.

## What this instrument does
Quantifies five empirical metrics on AI-generated code, across five
experimental conditions, against one fixed YAML specification.

## The five conditions (do NOT conflate)
- `human_control`  — baseline, no AI assistance
- `claude_code`    — Anthropic Claude Code
- `cursor_agent`   — Cursor agent mode
- `antigravity`    — Google Gemini Antigravity
- `replit_agent`   — Replit Agent

## Folder map
- docs/                planning + methodology + ethics + dissertation linkage
- specs/               the spec box (YAML, externalised)
- auditor/core/        engine: runner, config, logger, cli, governance
- auditor/analyzers/   ONE FILE PER METRIC
- auditor/adapters/    ONE FILE PER VENDOR
- auditor/models/      Pydantic shapes
- auditor/reporting/   CSV and JSON reporters
- tests/               pytest + synthetic fixtures
- data/                raw + processed + reports (gitignored)

## THE GOLDEN RULE
Follow ENGINEERING_PRINCIPLES.md. Never bundle metrics. Never bundle vendors.
Never hardcode spec content. Secrets in .env only. Synthetic data only.

## Confirm before doing
- Adding a metric (requires a docs/METRICS.md entry first).
- Adding a vendor (requires a docs/METHODOLOGY.md update first).
- Modifying a spec mid-experiment (create a new versioned spec instead).
