# Metrics — definitions and formulas

Each metric lives in its own analyzer file. This document is the contract.

## 1. Security vulnerability density
- **Definition:** count of CWE-tagged Bandit findings normalised per 1000
  lines of Python. This is a **per-language density** (Bandit scans Python
  only), and it is **severity-unweighted** — every finding contributes 1
  regardless of severity, because severity weighting would conflate the
  independent variable with the dependent variable. It is not a
  whole-project security score; a total-CWE companion metric is the
  documented extension (dissertation §6.4).
- **Tool:** local `bandit -r -f json` over the captured codebase, wired in
  `analyzers/security_analyzer.py`. Only findings with a non-null
  `issue_cwe.id` are counted (preserving the OWASP/CWE framing).
- **History:** the original design queried SonarQube/SonarCloud
  (`SONARQUBE_URL`/`SONARQUBE_TOKEN` in `.env`). It was abandoned during
  the pilot because per-project scoping shared one numerator across
  conditions while denominators varied, producing artefactually large
  per-kLOC figures — see PILOT_RESULTS.md §4.1. Local Bandit scoping
  restores per-condition isolation, determinism, and version-pinning.
  SonarQube remains in CI for the host repo's own quality signal only.
- **Exclusion — assertions in test files.** `B101` fires on every `assert`,
  because assertions are stripped when Python runs under `-O` and a check
  written as an assertion would silently disappear from a shipped build. That
  reasoning does not apply to a test file, where the assertion *is* the test.
  Counting them makes the metric reward untested code: on this repository
  alone, B101 in `tests/` produced 291 findings and raised the density from
  3.27 to 47.05 per kLOC. Assertions are therefore not counted in files named
  `test_*.py`, `*_test.py`, `conftest.py`, or living under a `tests/`
  directory. Assertions in production code still count.
- **Output:** `MetricScore(name="security_density", value=float, unit="per_kloc")`.

## 2. Cyclomatic complexity
- **Definition:** McCabe cyclomatic complexity per function; aggregated as
  the unweighted **mean** across all functions in the codebase. Reports
  `complexity_mean` as the headline metric (used by the experiment CSV);
  the per-function detail is preserved alongside in the raw artefacts.
- **Tool:** `radon.complexity.cc_visit` — AST-based, language-aware. Only
  Python (`.py`) files are scored in the MSc scope; other languages are
  skipped and logged. This is documented as a scope limitation.
- **Aggregation:** if a codebase has zero scorable functions the metric is
  reported as 0.0 with `unit="cc"`. A file that fails to parse is logged
  and excluded — never silently counted as zero.
- **Output:** `MetricScore(name="complexity_mean", value=float, unit="cc")`.

## 3. Code duplication
- **Definition:** percentage of source lines that appear inside at least one
  duplicated block. A "block" is a window of **k=6 consecutive non-blank,
  whitespace-normalised lines** that appears identically in two or more
  locations across the codebase.
- **Method:** token-free, language-agnostic shingle detection. Each file is
  reduced to a list of non-blank stripped lines; every k-line shingle is
  hashed; shingles seen ≥2 times mark all their constituent lines as
  duplicated. The metric is `100 * duplicated_lines / total_lines`.
- **Rationale:** the original SonarQube duplication metric uses a similar
  k-line shingle approach; reimplementing in-tree keeps duplication
  measurable for non-Java codebases without a SonarQube round-trip, and
  removes one external dependency from the metric.
- **Output:** `MetricScore(name="duplication_pct", value=float, unit="%")`.

## 4. Hallucination frequency
- **Definition:** count of features present in the codebase manifest but
  **NOT** declared in the spec — i.e. things the agent shipped that nobody
  asked for. Spec-declared features that were *not* implemented are a
  different metric (completeness) and are out of scope here.
- **Method:** parse the spec features (`spec["features"][*]["id"]`), parse
  the codebase manifest (`codebase["manifest"]`), compute set-difference
  `manifest \ spec`. Each adapter is responsible for producing an accurate
  manifest (see docs/METHODOLOGY.md capture contract). When an adapter emits
  no manifest (the agentic conditions), the analyzer falls back to an
  auto-derived manifest from `analyzers/manifest_deriver.py`, which scans the
  produced code for token evidence of each spec feature plus off-spec web
  routes and CLI subcommands (the CLI-subcommand detector was added in
  response to the main-study Replit observation and is logged as analytical
  note 001 in PROTOCOL_DEVIATIONS.md). The heuristic is exploratory pending
  blind hand-label validation (Cohen's κ, dissertation §4.7); headline
  findings are additionally confirmed by direct code inspection.
- **Output:** `MetricScore(name="hallucinations", value=float, unit="count")`.

## 5. Keystroke dynamics (correction frequency)
- **Definition:** count of `backspace` + `delete` events per 1000
  `keystroke` events in the interaction log.
- **Source:** the interaction log produced by each adapter, conforming to
  the capture contract in docs/METHODOLOGY.md. For agent conditions where
  every event is `agent_action`, the metric evaluates to 0 by construction
  — this is the intended behaviour and is what makes keystroke dynamics
  meaningful only as a differentiator for the human-control baseline.
- **Output:** `MetricScore(name="correction_freq", value=float, unit="per_kkey")`.
