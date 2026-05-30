# Ethics

Maps to Section 6 of the MSc proposal.

## Data
- **Synthetic only.** All Agent Education System content (mock Tesco/Asda
  staff, mock students) is fabricated. No real PII enters the pipeline.
- **No proprietary corporate data.** Ever.
- **No human-subject data.** This study does not require Research Ethics
  Approval as it does not collect human-subject data.

## AI use and authorship
- AI tools generate code as the **subject of the experiment**.
- The dissertation manuscript is authored independently by the researcher.
- All AI prompts and raw outputs are logged in `data/raw/` for audit.

## Cloud / data leakage
- No real customer or organisational data is uploaded to any LLM.
- `.env` is never committed. API keys are personal.

## Keystroke capture (human_control condition)
The `human_control` adapter relies on a `pynput` global keyboard listener
behind an explicit `--record` flag (`auditor/adapters/human_control_recorder.py`).

- The developer being recorded is the same person initiating the recording
  — a self-experiment design, not a study on third parties.
- The recorder logs only the **event type** (`keystroke`, `backspace`,
  `delete`). No character payload, no key codes, no inter-keystroke
  timings finer than what the capture contract requires. This is enforced
  in the recorder; the contract is documented in `docs/METHODOLOGY.md`.
- Captured sessions are stored under `data/raw/<run_id>/human_control/`,
  which is `.gitignored`.

## Reproducibility and report immutability
A report written to `data/reports/<run_id>.csv` is never edited
(engineering principle 8). If the methodology changes, a new `run_id` is
used. Published results therefore trace back to the exact spec, adapter
code, and analyzer code that produced them.

## Vendor neutrality
The experiment CSV is either complete (all five conditions present) or
refuses to write. Partial publication of results — e.g. "Vendor X loses
on metric Y" without the comparable rows for the other four conditions —
is excluded by construction.

## Disclosure of AI assistance in building the instrument
Parts of the Auditor itself were drafted with agentic coding assistants.
This is disclosed in the MSc methodology section. The Auditor is the
measuring instrument, not one of the measured artefacts — at experiment
time each vendor implements the fixed spec independently, so AI
involvement in the instrument's construction does not bias the measured
outputs of the five conditions.
