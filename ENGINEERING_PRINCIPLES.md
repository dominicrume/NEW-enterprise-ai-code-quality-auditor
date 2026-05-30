# Engineering Principles — AI Code Quality Auditor

Short rules. They are what make this a defensible *empirical instrument*
rather than a script.

1. **One analyzer per metric.** Each metric lives in its own file under
   `auditor/analyzers/`. Add a metric = add a file. Never bundle.
2. **One adapter per AI workflow.** All workflow-specific code is isolated in
   `auditor/adapters/`. The engine doesn't know which model produced the code.
3. **The spec is data, not code.** Specifications live in `specs/*.yaml`.
   This is what lets a peer reviewer rerun the experiment exactly.
4. **Reproducibility over cleverness.** Every audit run has a deterministic
   run ID. Same spec + same adapter + same fixture = same numbers.
5. **Synthetic data only.** No PII, no real corporate records ever touch the
   pipeline. The Auditor is a measurement instrument, not a data sink.
6. **Every analyzer has a test.** Test fixtures are stored in
   `tests/fixtures/` and version-controlled. Real experiment outputs are not.
7. **Secrets in `.env`, never in code.** API keys, tokens, hosts.
8. **Reports are immutable.** A report written to `data/reports/` is never
   edited — re-run if you need new numbers.
9. **Small, reversible steps.** One analyzer, one PR, tests green.
10. **Documents lead, code follows.** The proposal and the linkage doc are the
    source of truth for *what* this instrument measures and *why*.
