# Communications — drafts for you to send/post

> These are **drafts for the researcher (Dominic Rume) to send and post personally.**
> Nothing here has been or will be sent or published automatically. Review, edit,
> and send/post yourself. All figures are drawn from the project's real captured
> data (`data/reports/main_001.csv`, the `human_session_*` CSVs, and
> `notebooks/statistical_analysis.ipynb`).

---

## 1. Supervisor update (email to Julien Barney & Kate Sugden)

**Subject:** JBKS1 — main study complete + human baseline captured; Results & stats written up

Dear Julien and Kate,

A progress update on the AI Code Quality Auditor dissertation (JBKS1).

**Data collection is complete.** The main study (`run_001`) captured the full
four-tool × three-spec × ten-rep matrix for the agentic conditions — 600 metric
observations across the five metrics — and I have now also captured the
`human_control` baseline (one completed hand-coded session per specification,
all six features implemented and verified to run).

**Headline findings (four AI conditions, N = 30 per condition):**
- Four of five metrics differ significantly across tools (Kruskal–Wallis,
  Bonferroni α = 0.01), with effect sizes from medium (complexity, η² = 0.10) to
  very large (duplication, η² = 0.50).
- The condition × specification interaction is significant for every metric —
  i.e. tool quality is **task-dependent**, which is the study's central
  external-validity result and the justification for using three specs.
- The most consequential single finding: under a clean, isolated workspace with
  an explicit instruction prohibiting pipeline output, **Replit Agent shipped a
  data-pipeline CLI when asked for a command-line tool, in every replication** —
  a measured "architectural-prior dominance" that I frame as a governance
  (scope-containment) failure.

**Write-up status.** Chapters 3 (Methods) and 4 (Results) are updated with the
real numbers; the statistical notebook reproduces all of them end-to-end. I have
assembled a full draft dissertation (~10.7k words, Harvard referencing) that I
will continue to refine toward the final word count.

**Two points I'd value your steer on:**
1. The human baseline was executed as N = 1 per spec (not the pre-registered
   N = 10/60-min sessions) for time reasons; I've logged this as a formal
   deviation and frame the human condition as a single-rep reference point,
   excluded from the inferential tests. Is that treatment acceptable, or would
   you prefer I expand it?
2. The hallucination heuristic's inter-rater reliability (Cohen's κ) is currently
   reported as a *planned* validation — I have not yet hand-labelled the 30-run
   sample. I can complete the labelling before submission if you'd like κ
   reported; otherwise the metric stands as exploratory, with the key finding
   triangulated by direct code inspection.

Happy to share the draft chapters and the dashboard at your convenience.

Best regards,
Dominic

---

## 2. LinkedIn post (draft)

> Tone: professional, factual, no overclaiming. Trim hashtags to taste.

For my MSc AI dissertation at Aston University, I built an instrument that audits
*agentic AI coding tools* — not on "does the code run?", which existing
benchmarks already cover, but on the questions that decide whether you can
actually govern these tools in production: is the code secure, maintainable,
free of redundant scaffolding, and — most importantly — **does it build what was
specified, and nothing more?**

I ran four leading tools (Claude Code, Cursor, Replit Agent, Google Antigravity)
across three task types, ten times each — 600 measured data points — plus a
hand-coded human baseline.

A few things stood out:
→ Tool quality is **task-dependent** — the differences between tools change
  significantly depending on what you ask them to build. There is no single
  "best" tool.
→ The most striking result: given a clean workspace and an explicit instruction
  *not* to, one tool repeatedly shipped a data pipeline when asked for a
  command-line tool — every single time. Its architectural habits overrode the
  specification.
→ "Functional correctness" benchmarks would never catch this, because the wrong
  thing still passes its own tests.

My takeaway for anyone adopting these tools in a serious engineering org:
**measure specification fidelity before you adopt, not after.** Treat
"did it stay in scope?" as a first-class quality gate alongside your functional
tests.

Grateful to my supervisors Julien Barney and Kate Sugden, and to the
Aston–Capgemini Centre of Excellence for Enterprise AI.

#AI #SoftwareEngineering #LLM #AIGovernance #MSc #AstonUniversity

---

## 3. Notes before you post/send

- **Verify the Replit framing** reads fairly — it is a measured behaviour under
  stated controls (analytical note 001), not a vendor accusation; keep the
  "architectural prior" language rather than anything pejorative.
- **Do not state κ or any unverified figure** in public until/unless the
  hand-labelling is done.
- **Confirm supervisor names/titles** before sending the email.
- These drafts are yours to send; I have not contacted anyone.
