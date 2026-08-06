"""Adversarial re-analysis of main_001.csv.

Question: which Chapter 4 claims survive when the replay design (Deviation 001)
is taken seriously as a unit-of-analysis problem?
"""
import pandas as pd
from scipy import stats
import itertools

df = pd.read_csv("/Users/dominicorumeuririe/Downloads/NEW-enterprise-ai-code-quality-auditor/data/reports/main_001.csv")
AI = ["claude_code", "cursor_agent", "replit_agent", "antigravity"]
METRICS = ["duplication_pct", "security_density", "hallucinations", "complexity_mean"]

print("=" * 72)
print("TEST 1 — Verify the replay claim: within-cell variance by condition")
print("=" * 72)
for cond in AI:
    sub = df[df.condition == cond]
    nuniq = sub.groupby(["spec_name", "metric"])["value"].nunique()
    print(f"  {cond:15s} max distinct values in any (spec×metric) cell = {nuniq.max()}"
          f"   -> {'REPLAY (N=1 effective)' if nuniq.max() == 1 else 'LIVE (real variance)'}")

print()
print("=" * 72)
print("TEST 2 — Reproduce reported Kruskal-Wallis (all 4 conditions, nominal N=30)")
print("=" * 72)


def kw(groups):
    groups = [g for g in groups if len(g) > 0]
    if len(groups) < 2 or all(len(set(g)) == 1 and g[0] == groups[0][0] for g in groups):
        pass
    try:
        H, p = stats.kruskal(*groups)
    except ValueError:
        return None, None, None
    n = sum(len(g) for g in groups)
    k = len(groups)
    eta2 = (H - k + 1) / (n - k) if n > k else float("nan")
    return H, p, eta2


for m in METRICS:
    groups = [df[(df.condition == c) & (df.metric == m)]["value"].tolist() for c in AI]
    H, p, e = kw(groups)
    print(f"  {m:18s} H={H:7.2f}  p={p:.2e}  eta2={e:.3f}  {'SIG' if p < 0.01 else 'ns'}")

print()
print("=" * 72)
print("TEST 3 — HONEST unit of analysis: one value per (condition x spec) cell")
print("         (cell means; N=3 per condition. Removes pseudoreplication.)")
print("=" * 72)
for m in METRICS:
    groups = []
    for c in AI:
        cell = df[(df.condition == c) & (df.metric == m)].groupby("spec_name")["value"].mean()
        groups.append(cell.tolist())
    H, p, e = kw(groups)
    print(f"  {m:18s} H={H:7.2f}  p={p:.4f}   {'SIG @0.01' if p < 0.01 else 'NOT SIGNIFICANT'}")

print()
print("=" * 72)
print("TEST 4 — Only the two genuinely-live conditions (claude vs cursor, N=30)")
print("=" * 72)
for m in METRICS:
    a = df[(df.condition == "claude_code") & (df.metric == m)]["value"].tolist()
    b = df[(df.condition == "cursor_agent") & (df.metric == m)]["value"].tolist()
    try:
        U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        print(f"  {m:18s} U={U:8.1f}  p={p:.4f}   "
              f"{'SIG @0.01' if p < 0.01 else 'ns'}   means {pd.Series(a).mean():.2f} vs {pd.Series(b).mean():.2f}")
    except ValueError as exc:
        print(f"  {m:18s} untestable ({exc})")

print()
print("=" * 72)
print("TEST 5 — Within-live-condition variance: is there real replication signal?")
print("=" * 72)
for c in ["claude_code", "cursor_agent"]:
    for m in METRICS:
        sub = df[(df.condition == c) & (df.metric == m)]
        per_cell_sd = sub.groupby("spec_name")["value"].std()
        print(f"  {c:13s} {m:18s} within-cell SD by spec: "
              + ", ".join(f"{v:.3f}" for v in per_cell_sd))

print()
print("=" * 72)
print("TEST 6 — The headline finding: Replit CLI hallucinations, raw values")
print("=" * 72)
sub = df[(df.condition == "replit_agent") & (df.metric == "hallucinations")]
for spec, g in sub.groupby("spec_name"):
    print(f"  {spec:26s} values={sorted(set(g.value.tolist()))}  n_rows={len(g)}  "
          f"distinct_durations={g.duration_s.nunique()}")

print()
print("=" * 72)
print("TEST 7 — Effect of pseudoreplication on the interaction claim")
print("         Reported: duplication F=283.8. Recompute honestly on cell means.")
print("=" * 72)
for m in ["duplication_pct", "hallucinations"]:
    piv = df[df.condition.isin(AI) & (df.metric == m)].pivot_table(
        index="condition", columns="spec_name", values="value", aggfunc="mean")
    print(f"\n  {m} — cell means (condition x spec):")
    print(piv.to_string(float_format=lambda x: f"{x:8.3f}"))
    print("  With 1 observation per cell, a condition x spec interaction has "
          "ZERO residual df -> F is undefined/untestable on this design.")
