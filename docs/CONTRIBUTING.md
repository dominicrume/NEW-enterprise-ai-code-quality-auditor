# Contributing

## Branch, build, test, review, merge
```bash
git checkout -b feature/short-name
# make change
pytest -q                          # tests must pass
git commit -m "Add X analyzer"
git push origin feature/short-name  # then open a PR
```

## Where my change goes
- New metric  -> `auditor/analyzers/<name>_analyzer.py` + `docs/METRICS.md`
- New workflow -> `auditor/adapters/<name>_adapter.py`
- New data shape -> `auditor/models/`
- New CLI command -> `auditor/core/cli.py`

## Definition of "done"
Works · has a test · tests pass · another engineer can read it without asking.
