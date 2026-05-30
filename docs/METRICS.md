# Metrics — definitions and formulas

Each metric lives in its own analyzer file. This document is the contract.

## 1. Security vulnerability density
- **Definition:** count of OWASP/CWE-flagged issues normalised per 1000 LOC.
- **Tool:** SonarQube (server URL and token from `.env` —
  `SONARQUBE_URL`, `SONARQUBE_TOKEN`). Wired in
  `analyzers/security_analyzer.py`.
- **Rule sets counted:** issues returned by SonarQube's
  `/api/issues/search` for the audited project where:
  - `type ∈ {VULNERABILITY, SECURITY_HOTSPOT}` — these are the two
    SonarQube issue types that map to OWASP/CWE-relevant findings;
    `BUG` and `CODE_SMELL` are intentionally excluded as they belong
    to the complexity / duplication metrics.
  - All severities are counted equally (BLOCKER, CRITICAL, MAJOR,
    MINOR, INFO each contribute 1). The metric is a count, not a
    severity-weighted score; severity weighting would conflate the
    independent variable with the dependent variable.
  - Only issues with at least one OWASP/CWE tag (any tag matching
    `cwe`, `cwe-*`, `owasp-a*`, `owasp-top10-*`) are included. This
    is what makes the count an *OWASP/CWE density*, not a generic
    SonarQube issue density.
  - Status `OPEN`, `CONFIRMED`, or `REOPENED` only — `RESOLVED` and
    `CLOSED` issues are excluded.
- **Project key:** `spec["sonar_project_key"]` if present, else
  `spec["name"]`. This is what lets the same analyzer score five
  different uploads of the same spec.
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
  manifest (see docs/METHODOLOGY.md capture contract).
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
