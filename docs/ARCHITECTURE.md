# Architecture

## The data flow (one audit run)
```
specs/*.yaml  ──►  core/runner.py  ──►  adapter (one AI workflow)
                                              │
                                              ▼
                                   generated code + interaction log
                                              │
                                              ▼
            analyzers/ (security · complexity · duplication ·
                        hallucination · keystroke)
                                              │
                                              ▼
                              models/AuditResult (Pydantic)
                                              │
                                              ▼
                       reporting/ ─► data/reports/*.csv  *.json
```

## Why this shape
- The **runner** does not know which model produced the code. It only knows
  the spec, the adapter to call, and which analyzers to run. This is what
  lets a new AI workflow be evaluated by writing one file.
- The **analyzers** do not know which workflow produced the code. They take a
  codebase + interaction log and emit numbers. Each analyzer is a function
  with a clear contract — easy to test, easy to extend.
- The **spec** is YAML, not Python. A peer reviewer can read it and rerun.

## Backend-style layering inside `auditor/`
```
core/        engine, configuration, command-line entry
analyzers/   one file per metric
adapters/    one file per workflow
governance/  KYA compliance scoring layer
models/      Pydantic shapes (AuditResult, MetricScore, RunMetadata)
reporting/   CSV/JSON emitters
```

## How to add a new metric
1. Add the metric to `docs/METRICS.md` (definition + formula).
2. Add a file in `auditor/analyzers/` with one function: `analyze(codebase, log) -> MetricScore`.
3. Register it in `auditor/core/runner.py`'s analyzer list.
4. Add a synthetic fixture in `tests/fixtures/` and a test.
5. Re-run the experiment.

## How to add a new AI workflow
1. Add a file in `auditor/adapters/` extending `BaseAdapter`.
2. Implement `generate(spec) -> (codebase, interaction_log)`.
3. Register in the CLI.
4. Run a control comparison and document in `data/reports/`.
