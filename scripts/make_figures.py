#!/usr/bin/env python3
"""Generate the dissertation's conceptual figures.

Chapter 4's empirical figures (forest, violin) come from the statistical
notebook. These four are the conceptual and interpretive figures: they
explain the instrument's design and make two dense tables legible at a
glance. Regenerate with:

    PYTHONPATH=. .venv/bin/python scripts/make_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from auditor.core.calibration import BANDS

OUT = Path(__file__).resolve().parent.parent / "docs" / "dissertation" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# Print-safe palette: distinguishable in greyscale, colour-blind friendly.
INK, TEAL, TEAL_L = "#1A1F1D", "#0F766E", "#D6E7E4"
GREY, GREY_L = "#6B7671", "#EDEFEC"
AMBER, AMBER_L = "#B07D2E", "#F3E7D0"
RED, RED_L = "#A8443A", "#F2DAD6"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "figure.dpi": 300, "savefig.dpi": 300,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.14,
})


def save(fig, stem):
    for ext in ("png", "pdf"):          # PDF keeps vector quality for print
        fig.savefig(OUT / f"{stem}.{ext}", facecolor="white")
    plt.close(fig)
    print(f"  wrote figures/{stem}.png + .pdf")


def box(ax, x, y, w, h, label, sub=None, fc=GREY_L, ec=GREY, bold=True,
        fs=9, sub_fs=7.2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.016",
        facecolor=fc, edgecolor=ec, linewidth=1.1, zorder=2))
    cx, cy = x + w / 2, y + h / 2
    if sub:
        gap = 0.032 * (label.count("\n") + 1) + 0.026 * (sub.count("\n") + 1)
        ax.text(cx, cy + gap / 2, label, ha="center", va="center", zorder=3,
                fontsize=fs, fontweight="bold" if bold else "normal",
                linespacing=1.25)
        ax.text(cx, cy - gap / 2 - 0.010, sub, ha="center", va="center",
                fontsize=sub_fs, color=GREY, zorder=3, style="italic",
                linespacing=1.35)
    else:
        ax.text(cx, cy, label, ha="center", va="center", zorder=3,
                fontsize=fs, fontweight="bold" if bold else "normal",
                linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color=INK):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=10, linewidth=0.9,
                                 color=color, zorder=1, shrinkA=1, shrinkB=1))


# ---------------------------------------------- Figure 3.1 -- architecture
def fig_architecture():
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    SPEC_X, SPEC_W = 0.008, 0.130
    ADP_X, ADP_W = 0.188, 0.174
    CAP_X, CAP_W = 0.412, 0.130
    ANL_X, ANL_W = 0.594, 0.194
    REP_X, REP_W = 0.846, 0.146
    ROW_H, ROW_GAP, BASE = 0.112, 0.040, 0.085
    MID = BASE + 2 * (ROW_H + ROW_GAP) + ROW_H / 2

    def row_y(i):
        return BASE + (4 - i) * (ROW_H + ROW_GAP)

    box(ax, SPEC_X, MID - 0.100, SPEC_W, 0.200, "Specification",
        "fixed\nversioned", fc=TEAL_L, ec=TEAL, fs=9.3)

    conds = ["human_control", "claude_code", "cursor_agent",
             "antigravity", "replit_agent"]
    for i, c in enumerate(conds):
        y = row_y(i)
        box(ax, ADP_X, y, ADP_W, ROW_H, c, fc="white", ec=GREY,
            bold=False, fs=8.3)
        arrow(ax, SPEC_X + SPEC_W + 0.005, MID, ADP_X - 0.005,
              y + ROW_H / 2, color=GREY)
    ax.text(ADP_X + ADP_W / 2, row_y(0) + ROW_H + 0.032,
            "ONE ADAPTER PER VENDOR", ha="center", fontsize=7.2,
            color=TEAL, fontweight="bold")

    box(ax, CAP_X, MID - 0.175, CAP_W, 0.350, "Capture\ncontract",
        "codebase +\ninteraction log", fc=TEAL_L, ec=TEAL, fs=9.3)
    for i in range(5):
        arrow(ax, ADP_X + ADP_W + 0.005, row_y(i) + ROW_H / 2,
              CAP_X - 0.005, MID, color=GREY)

    metrics = ["security_density", "complexity_mean", "duplication_pct",
               "hallucinations", "correction_freq"]
    for i, m in enumerate(metrics):
        y = row_y(i)
        box(ax, ANL_X, y, ANL_W, ROW_H, m, fc="white", ec=GREY,
            bold=False, fs=8.3)
        arrow(ax, CAP_X + CAP_W + 0.005, MID, ANL_X - 0.005,
              y + ROW_H / 2, color=GREY)
    ax.text(ANL_X + ANL_W / 2, row_y(0) + ROW_H + 0.032,
            "ONE ANALYSER PER METRIC", ha="center", fontsize=7.2,
            color=TEAL, fontweight="bold")

    pad = 0.018
    ax.add_patch(Rectangle(
        (ANL_X - pad, BASE - pad), ANL_W + 2 * pad,
        5 * ROW_H + 4 * ROW_GAP + 2 * pad, fill=False, edgecolor=TEAL,
        linewidth=0.9, linestyle=(0, (4, 3)), zorder=1))
    ax.text(ANL_X + ANL_W / 2, BASE - pad - 0.034,
            "analysers are blind to condition identity", ha="center",
            fontsize=7, color=TEAL, style="italic")

    box(ax, REP_X, MID - 0.100, REP_W, 0.200, "Report",
        "CSV +\nprovenance", fc=TEAL_L, ec=TEAL, fs=9.3)
    for i in range(5):
        arrow(ax, ANL_X + ANL_W + 0.005, row_y(i) + ROW_H / 2,
              REP_X - 0.005, MID, color=GREY)

    save(fig, "fig_3_1_architecture")


# ------------------------------------------ Figure 3.2 -- capture contract
def fig_capture_contract():
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    box(ax, 0.010, 0.615, 0.270, 0.250, "Human types in an editor",
        "keypress / backspace / delete", fc="white", ec=GREY, fs=8.6,
        sub_fs=7.0)
    box(ax, 0.010, 0.155, 0.270, 0.250, "Agent streams tool-calls",
        "write_file / edit / run", fc="white", ec=GREY, fs=8.6, sub_fs=7.0)

    box(ax, 0.370, 0.330, 0.230, 0.360, "Normalisation",
        "one typed\nevent schema", fc=TEAL_L, ec=TEAL, fs=9.3)
    arrow(ax, 0.285, 0.740, 0.365, 0.570)
    arrow(ax, 0.285, 0.280, 0.365, 0.450)

    box(ax, 0.690, 0.560, 0.300, 0.220, "codebase",
        "{path: source}", fc=TEAL_L, ec=TEAL, fs=9.3)
    box(ax, 0.690, 0.235, 0.300, 0.220, "interaction_log",
        "[{type, ...}]", fc=TEAL_L, ec=TEAL, fs=9.3)
    arrow(ax, 0.605, 0.545, 0.685, 0.670)
    arrow(ax, 0.605, 0.475, 0.685, 0.345)

    ax.text(0.5, 0.045,
            "Heterogeneous workflows are forced into one comparable shape "
            "before any metric sees them.",
            ha="center", fontsize=7.6, color=GREY, style="italic")
    save(fig, "fig_3_2_capture_contract")


# -------------------------------------------- Figure 3.3 -- metric bands
def fig_metric_bands():
    labels = {
        "security_density": "Security density  (per kLOC)",
        "complexity_mean": "Cyclomatic complexity  (cc)",
        "duplication_pct": "Duplication  (%)",
        "hallucinations": "Hallucinations  (count)",
        "correction_freq": "Correction frequency  (per 1k)",
    }
    order = list(labels)
    fig, axes = plt.subplots(len(order), 1, figsize=(6.6, 3.4), sharex=False)

    for ax, metric in zip(axes, order):
        warn, crit = BANDS[metric]["warning"], BANDS[metric]["critical"]
        top = crit * 1.4
        ax.barh(0, warn, height=1.0, color=TEAL_L, edgecolor=TEAL, lw=.7)
        ax.barh(0, crit - warn, left=warn, height=1.0,
                color=AMBER_L, edgecolor=AMBER, lw=.7)
        ax.barh(0, top - crit, left=crit, height=1.0,
                color=RED_L, edgecolor=RED, lw=.7)
        ax.text(warn / 2, 0, "acceptable", ha="center", va="center",
                fontsize=6.6, color=TEAL)
        ax.text((warn + crit) / 2, 0, "warning", ha="center", va="center",
                fontsize=6.6, color=AMBER)
        ax.text((crit + top) / 2, 0, "concern", ha="center", va="center",
                fontsize=6.6, color=RED)
        ax.set_xlim(0, top)
        ax.set_xticks([0, warn, crit])
        ax.set_xticklabels([f"{v:g}" for v in (0, warn, crit)], fontsize=6.8)
        ax.set_yticks([])
        ax.tick_params(axis="x", length=2, pad=1.5, colors=GREY)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GREY)
        ax.spines["bottom"].set_linewidth(0.6)
        ax.set_ylabel(labels[metric], rotation=0, ha="right", va="center",
                      fontsize=8, labelpad=8)

    axes[-1].set_xlabel("metric value  (lower is better for every metric)",
                        fontsize=7.4, color=GREY, labelpad=4)
    fig.subplots_adjust(hspace=0.9)
    save(fig, "fig_3_3_metric_bands")


# ------------------------------------ Figure 4.3 -- hallucination heatmap
def fig_hallucination_heatmap():
    conds = ["claude_code", "cursor_agent", "antigravity", "replit_agent"]
    data = [[0.00, 0.00, 0.00],
            [0.50, 0.00, 0.00],
            [1.00, 0.00, 0.00],
            [0.00, 0.00, 3.00]]

    fig, ax = plt.subplots(figsize=(5.8, 3.1))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "drift", ["#FFFFFF", TEAL_L, AMBER_L, "#E4B49B", RED])
    im = ax.imshow(data, cmap=cmap, vmin=0, vmax=3, aspect="auto")

    for i in range(len(conds)):
        for j in range(3):
            v = data[i][j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=10.5, fontweight="bold" if v > 0 else "normal",
                    color="white" if v >= 2.4 else INK)

    ax.set_xticks(range(3))
    ax.set_xticklabels(["web app\n(agent_education)", "data\npipeline",
                        "CLI tool\n(internal_tool_cli)"], fontsize=8)
    ax.set_yticks(range(len(conds)))
    ax.set_yticklabels(conds, fontsize=8.5)
    ax.set_xticks([x - .5 for x in range(1, 3)], minor=True)
    ax.set_yticks([y - .5 for y in range(1, len(conds))], minor=True)
    ax.grid(which="minor", color="white", linewidth=2.2)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(which="major", length=0, pad=4)
    for s in ax.spines.values():
        s.set_edgecolor(GREY)

    cb = fig.colorbar(im, ax=ax, shrink=.85, pad=.035)
    cb.set_label("off-spec features per run", fontsize=7.4, color=GREY)
    cb.ax.tick_params(labelsize=7, length=2)
    cb.outline.set_edgecolor(GREY)
    ax.set_title("Off-spec features by tool and task domain",
                 fontsize=9.5, fontweight="bold", pad=10)
    save(fig, "fig_4_3_hallucination_heatmap")


if __name__ == "__main__":
    print("generating dissertation figures...")
    fig_architecture()
    fig_capture_contract()
    fig_metric_bands()
    fig_hallucination_heatmap()
    print(f"done -> {OUT}")
