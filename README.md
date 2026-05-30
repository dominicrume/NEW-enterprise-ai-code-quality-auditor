# AI Code Quality Auditor — the Referee Tool

> An empirical Safety Harness for agentic AI coding systems.
> Quantifies where AI-assisted development fails at governance, security,
> and ethical alignment — *before* the code reaches production.

This is the experimental instrument for the MSc dissertation
**"AI-Assisted Coding Assessment Tool: Evaluating LLM Performance, Governance,
and Security in an Agent Education System"** (Aston University, MSc AI &
Business Strategy). The same instrument is the working prototype for the
PhD extension at the Aston-Capgemini Centre of Excellence for Enterprise AI.

---

## What it does
Given a fixed specification (the "spec box"), the Auditor:
1. Runs five experimental conditions against the same task (human control,
   visualisation→Claude→Replit, Cursor IDE, autonomous agent).
2. Captures every output and every interaction event.
3. Scores each result on five empirical metrics: security vulnerability
   density, cyclomatic complexity, code duplication, hallucination frequency
   (features outside spec), and keystroke dynamics (correction frequency).
4. Emits CSV/JSON reports for statistical comparison.

## Quick start
```bash
cp .env.example .env
pip install -e .
auditor run --spec specs/agent_education_system.yaml --workflow human_control
auditor report --out data/reports/
```

## Read in this order
1. `docs/ARCHITECTURE.md` — how the pieces fit
2. `docs/METHODOLOGY.md` — how an experiment is run
3. `docs/METRICS.md` — what each metric means and how it's computed
4. `docs/ETHICS.md` — GDPR, synthetic data, academic integrity
5. `docs/DISSERTATION_LINKAGE.md` — which folder serves which proposal section
6. `docs/ROADMAP.md` — the PhD extension (API security + enterprise risk)

## Principles
- One analyzer per metric. One adapter per AI workflow. Single responsibility.
- The spec is data, not code — externalised in `specs/` for reproducibility.
- Synthetic data only. No PII, no proprietary corporate records, ever.
- Every analyzer has a test. Green tests = trustable experiment.
