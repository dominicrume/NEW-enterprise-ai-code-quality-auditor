"""Precise numbers for the corrected Chapter 4 statistical analysis."""
import pandas as pd
from scipy import stats

df = pd.read_csv("/Users/dominicorumeuririe/Downloads/NEW-enterprise-ai-code-quality-auditor/data/reports/main_001.csv")
METRICS = ["duplication_pct", "security_density", "hallucinations", "complexity_mean"]

print("LIVE-CONDITION COMPARISON: claude_code vs cursor_agent (N=30 each, real replication)")
print(f"{'metric':20s} {'U':>8s} {'p':>10s} {'rank-biserial':>14s}  {'claude':>8s} {'cursor':>8s}")
for m in METRICS:
    a = df[(df.condition == "claude_code") & (df.metric == m)]["value"]
    b = df[(df.condition == "cursor_agent") & (df.metric == m)]["value"]
    U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    n1, n2 = len(a), len(b)
    rb = 1 - (2 * U) / (n1 * n2)          # rank-biserial correlation
    print(f"{m:20s} {U:8.1f} {p:10.4f} {rb:14.3f}  {a.mean():8.2f} {b.mean():8.2f}")

print()
print("Bonferroni thresholds across 4 metrics: a=0.05 -> 0.0125 ; a=0.01 -> 0.0025")

print()
print("CELL-MEAN OMNIBUS (all 4 conditions, N=3 cells each — pseudoreplication removed)")
for m in METRICS:
    groups = [df[(df.condition == c) & (df.metric == m)].groupby("spec_name")["value"].mean().tolist()
              for c in ["claude_code", "cursor_agent", "replit_agent", "antigravity"]]
    H, p = stats.kruskal(*groups)
    print(f"  {m:20s} H={H:6.2f}  p={p:.4f}")

print()
print("DESCRIPTIVE RANGES (cell means across conditions) — what the design CAN support")
for m in METRICS:
    piv = df[df.metric == m].pivot_table(index="condition", columns="spec_name",
                                         values="value", aggfunc="mean")
    piv = piv.loc[["claude_code", "cursor_agent", "replit_agent", "antigravity"]]
    overall = piv.mean(axis=1)
    print(f"  {m:20s} min={overall.min():7.3f} ({overall.idxmin()})  "
          f"max={overall.max():7.3f} ({overall.idxmax()})")

print()
print("HUMAN vs AI (for Table 4.4) — per spec, human value vs AI mean across 4 conditions")
h = pd.read_csv("/Users/dominicorumeuririe/Downloads/NEW-enterprise-ai-code-quality-auditor/data/reports/human_vs_ai_comparison.csv")
h["ai_mean"] = h[["claude_code(mean)", "cursor_agent(mean)",
                  "antigravity(mean)", "replit_agent(mean)"]].mean(axis=1)
for spec, g in h.groupby("spec"):
    print(f"\n  {spec}")
    for _, r in g.iterrows():
        print(f"    {r['metric']:18s} human={r['human_control(n=1)']:9.2f}   AI mean={r['ai_mean']:9.2f}")
