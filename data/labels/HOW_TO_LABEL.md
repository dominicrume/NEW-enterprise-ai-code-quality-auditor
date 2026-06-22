# How to hand-label the 30 runs (for Cohen's κ)

You are the human checker. For each of the 30 runs in
`hallucination_handlabels.csv`, you decide **how many off-specification features
the AI shipped** — i.e. things in the code that the spec did **not** ask for.
The notebook then compares your counts to the auditor's counts and reports
Cohen's κ (agreement). Higher κ = the auditor agrees with a human = trustworthy.

This is a **blind** label: the file deliberately does **not** show you the
auditor's number. Judge for yourself, then let the notebook compare.

## The 3 specs and their ALLOWED features

Anything the code does that maps to a feature below is **on-spec** (not a
hallucination). Anything extra — an unrequested web route, an extra CLI
subcommand, a whole extra module/endpoint — is a **hallucination**.

**agent_education_system** (a web app): `auth.register`, `auth.login`,
`course.list`, `course.view`, `training.module.corporate`,
`training.module.academic`

**data_pipeline** (an ETL job): `ingest.csv`, `validate.schema`,
`transform.normalise`, `load.sqlite`, `schedule.daily`, `report.run_summary`

**internal_tool_cli** (a CLI): `cli.init`, `cli.add`, `cli.list`, `cli.export`,
`cli.validate`, `cli.help`

## Step by step (≈ 1–2 min per run)

1. Open `hallucination_handlabels.csv`. Each row has a `code_path`.
2. Open that folder and read the code (in VS Code, or:
   `open data/raw/<run_id>/<condition>/code`).
3. Look at the spec for that row's `spec_name` (lists above). Ask:
   **"Did the AI add anything that isn't one of the 6 allowed features?"**
   - Extra HTTP routes (e.g. `/health`, `/metrics`, `/admin`) → count each.
   - Extra CLI subcommands not in the list → count each.
   - A whole different app shape (e.g. a data pipeline when a CLI was asked
     for) → count the off-spec commands/endpoints it added.
4. Put the **number** you counted in the `n_hallucinated_handlabel` column.
   - If it added nothing off-spec, put **0**.
   - If you're only deciding yes/no, that's fine too: **0** = clean,
     **1** = it added something. (The κ calculation only uses "any vs none".)
5. Save the file. Leave the helper columns alone.

## When you're done — compute κ

Open `notebooks/statistical_analysis.ipynb`, run all cells, and look at the
**last cell** ("Inter-rater reliability"). It will print:

```
Cohen's κ (any-hallucination presence) = 0.XX  on N=30
Interpretation:  <0.4 poor · 0.4-0.6 moderate · 0.6-0.8 good · >0.8 very good
```

If **κ ≥ 0.6**, you can upgrade Chapter 4 §4.7 from "planned validation" to a
reported result and treat the hallucination metric as *inferential*. Tell me the
number and I'll update the dissertation text for you.

## Notes for the write-up
- Sample = 30 of 120 runs, drawn with a fixed random seed (42) for
  reproducibility, per pre-registration §9.
- Keep it honest: label what you actually see. A lower κ is still a valid,
  reportable result (and itself motivates the structural-shape-detection
  extension in §6.4).
