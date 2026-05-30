# Methodology — how an experiment is run

Maps to Section 5 of the MSc proposal, with one refinement: the
experimental design distinguishes **five** independent conditions rather
than four, because Claude Code (Anthropic) and Replit Agent (Replit) are
separate vendor products and must not be conflated.

## Independent variables (five conditions)
| Condition       | Vendor / product             | Adapter file                       |
|-----------------|------------------------------|------------------------------------|
| Human control   | none (baseline)              | `human_control_adapter.py`         |
| Claude Code     | Anthropic — agentic IDE/CLI  | `claude_code_adapter.py`           |
| Cursor Agent    | Cursor — agentic IDE         | `cursor_agent_adapter.py`          |
| Antigravity     | Google Gemini — agent        | `antigravity_adapter.py`           |
| Replit Agent    | Replit — autonomous agent    | `replit_agent_adapter.py`          |

## Dependent variables (five metrics — all machine-recorded)
1. **Security vulnerability density** (OWASP/CWE per 1000 LOC).
2. **Cyclomatic complexity** (per function, mean and max).
3. **Code duplication** (% duplicate lines).
4. **Hallucination frequency** (features outside the spec, counted).
5. **Keystroke dynamics** (correction frequency per 1000 keystrokes).

## Run protocol
1. Load `specs/agent_education_system.yaml`.
2. For each of the five conditions, invoke its adapter against the same spec.
3. Capture codebase + interaction log to `data/raw/<run_id>/<condition>/`.
4. Run every analyzer over each captured codebase.
5. Emit one row per (run, condition, metric) into `data/reports/`.
6. Statistical comparison happens in a separate analysis notebook.

## Capture contract (every adapter must satisfy)
- Produce a `codebase` dict: `{"files": {path: content}, "manifest": [feature_ids]}`.
- Produce an `interaction_log` list: events with at minimum `{"type": str}`.
  Permitted types: `"keystroke"`, `"backspace"`, `"delete"`, `"agent_action"`.
- Persist both raw artefacts to `data/raw/<run_id>/<condition>/`.
