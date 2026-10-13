"""Rebuild every Study 1 figure from the raw run records.

    python paper/figures/make_figures.py --phase pilot

Reads learners/results/<phase>.jsonl (via learners.analysis) and writes PNG and
PDF files to paper/figures/<phase>/. Nothing here is hand-edited: rerunning
this script on the same records gives the same figures.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from learners.analysis import analyse, load, outcome, table  # noqa: E402

# Okabe–Ito colour-blind-safe palette; each arm keeps its colour everywhere.
COLORS = {
    "IMMORTAL": "#222222", "RESET": "#CC79A7", "RESTART": "#56B4E9", "TEACH": "#D55E00",
    "CLONE": "#0072B2", "GENES": "#009E73", "RANDOM": "#E69F00", "SCRATCH": "#999999",
}
ARMS = ["IMMORTAL", "RESET", "RESTART", "TEACH", "CLONE", "GENES", "RANDOM"]
LABELS = {
    "IMMORTAL": "Immortal", "RESET": "Reset (shrink & perturb)", "RESTART": "Restart (nothing inherited)",
    "TEACH": "Teach a fresh child", "CLONE": "Clone (population, weights)",
    "GENES": "Genes (population, settings only)", "RANDOM": "Random search (population)",
    "SCRATCH": "Fresh network",
}

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#e6e6e6", "grid.linewidth": 0.6, "lines.linewidth": 1.6,
    "savefig.dpi": 200, "figure.dpi": 100,
})


def save(fig, out, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)


def regime_title(reg):
    return f"new skill every {reg['R']} eras · lifespan {reg['L']}"


def fig_online(s, out):
    regs = s["regimes"]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.0), sharex=True, sharey=True)
    for ax, reg in zip(axes.flat, regs):
        for arm in ARMS:
            row = reg["arms"].get(arm)
            if not row or "online_curve" not in row:
                continue
            y = np.convolve(row["online_curve"], np.ones(5) / 5, mode="valid")
            ax.plot(np.arange(len(y)) + 5, 100 * y, color=COLORS[arm], label=LABELS[arm])
        ax.set_title(regime_title(reg))
        ax.set_ylim(0, 100)
    for ax in axes[1]:
        ax.set_xlabel("era")
    for ax in axes[:, 0]:
        ax.set_ylabel("accuracy on the current task (%)")
    axes[0, 0].legend(loc="lower left", frameon=False)
    fig.suptitle("Performance on the stream (mean over seeds, 5-era moving average)", y=1.0)
    save(fig, out, "fig1_online")


def fig_trajectories(s, out):
    regs = s["regimes"]
    rows = [("frontier_by_cp", "FRONTIER: learning the next skills (%)", 100),
            ("knowledge_by_cp", "KNOWLEDGE: skills known (%)", 100),
            ("depth_by_cp", "deepest skill known (bits)", 1),
            ("novel_by_cp", "NOVEL: learning unrelated skills (%)", 100)]
    fig, axes = plt.subplots(len(rows), len(regs), figsize=(9.5, 8.6), sharex=True, sharey="row")
    for j, reg in enumerate(regs):
        for i, (key, label, scale) in enumerate(rows):
            ax = axes[i, j]
            for arm in ["SCRATCH"] + ARMS:
                row = reg["arms"].get(arm)
                if not row or key not in row:
                    continue
                cps = sorted(int(c) for c in row[key])
                ys = [scale * row[key][c if c in row[key] else str(c)] for c in cps]
                ax.plot(cps, ys, color=COLORS[arm], marker="o", markersize=3,
                        linestyle="--" if arm == "SCRATCH" else "-", label=LABELS[arm])
            if i == 0:
                ax.set_title(regime_title(reg))
            if j == 0:
                ax.set_ylabel(label)
            if i == len(rows) - 1:
                ax.set_xlabel("era")
    axes[0, 0].legend(loc="best", frameon=False, fontsize=7)
    fig.suptitle("What each life history knows and can still learn (mean over seeds)", y=1.0)
    fig.tight_layout()
    save(fig, out, "fig2_trajectories")


def fig_paired(phase, s, out):
    """Every seed's difference for the headline comparisons."""
    t = table(load(phase))
    comps = [("TEACH", "IMMORTAL", "FINAL_FRONTIER"), ("TEACH", "IMMORTAL", "ONLINE"),
             ("TEACH", "RESET", "FINAL_FRONTIER"), ("TEACH", "RESTART", "FINAL_KNOWLEDGE"),
             ("IMMORTAL", "RESTART", "FINAL_KNOWLEDGE"), ("CLONE", "IMMORTAL", "FINAL_FRONTIER")]
    regs = s["regimes"]
    fig, axes = plt.subplots(1, len(regs), figsize=(10, 3.4), sharey=True)
    for ax, reg in zip(np.atleast_1d(axes), regs):
        for i, (a, b, name) in enumerate(comps):
            A, B = t[(a, reg["R"], reg["L"])], t[(b, reg["R"], reg["L"])]
            seeds = sorted(set(A) & set(B))
            d = np.array([outcome(A[k], name) - outcome(B[k], name) for k in seeds]) * 100
            jitter = np.linspace(-0.18, 0.18, len(d)) if len(d) > 1 else [0]
            ax.scatter(d, i + np.asarray(jitter), s=10, color=COLORS[a], alpha=0.8, zorder=3)
            ax.plot([d.mean()] * 2, [i - 0.3, i + 0.3], color="#111111", linewidth=2, zorder=4)
        ax.axvline(0, color="#888888", linewidth=0.8)
        ax.set_title(regime_title(reg))
        ax.set_xlabel("difference (accuracy points)")
    ax0 = np.atleast_1d(axes)[0]
    ax0.set_yticks(range(len(comps)))
    ax0.set_yticklabels([f"{a} − {b}\n{n.replace('FINAL_', '')}" for a, b, n in comps], fontsize=7)
    ax0.invert_yaxis()
    fig.suptitle("Paired differences, one dot per seed (bar = mean)", y=1.02)
    save(fig, out, "fig3_paired_differences")


def fig_skill_map(phase, out):
    """One world's skill tree, coloured by how well each arm's network can
    read out each skill at the end of the run."""
    recs = load(phase)
    scratch = [r for r in recs if r["arm"] == "SCRATCH" and "world" in r]
    if not scratch:
        return
    seed, R = scratch[0]["seed"], scratch[0]["R"]
    world = scratch[0]["world"]
    L = max(r["L"] for r in recs if r["L"])
    by_arm = {r["arm"]: r for r in recs if r["seed"] == seed and r["R"] == R and r["L"] in (0, L)
              and r["arm"] != "SCRATCH"}
    last = str(max(int(c) for c in scratch[0]["probes"]))
    n = len(by_arm[next(iter(by_arm))]["probes"][last]["knowledge"])
    degrees = world["degrees"][:n]
    order = sorted(range(n), key=lambda k: (degrees[k], k))
    arms = [a for a in ARMS if a in by_arm]
    grid = np.array([[by_arm[a]["probes"][last]["knowledge"][k] for k in order] for a in arms])
    fig, ax = plt.subplots(figsize=(9, 0.42 * len(arms) + 1.3))
    im = ax.imshow(100 * grid, aspect="auto", cmap="Blues", vmin=50, vmax=100, interpolation="nearest")
    ax.set_yticks(range(len(arms)))
    ax.set_yticklabels([LABELS[a] for a in arms])
    ticks = [i for i, k in enumerate(order) if i == 0 or degrees[k] != degrees[order[i - 1]]]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{degrees[order[i]]}-bit" for i in ticks], fontsize=7)
    ax.grid(False)
    ax.set_xlabel(f"skills introduced by era {last}, ordered by size (world {seed}, "
                  f"new skill every {R} eras, lifespan {L})")
    fig.colorbar(im, ax=ax, label="readout accuracy (%)", fraction=0.025)
    ax.set_title("Skill map: which skills each life history still knows at the end")
    save(fig, out, "fig4_skill_map")


def fig_diagnostics(s, out):
    regs = s["regimes"]
    fig, axes = plt.subplots(1, len(regs), figsize=(10, 2.8), sharey=True)
    for ax, reg in zip(np.atleast_1d(axes), regs):
        for arm in ARMS:
            row = reg["arms"].get(arm)
            if not row or "dead_by_cp" not in row:
                continue
            cps = sorted(int(c) for c in row["dead_by_cp"])
            ax.plot(cps, [100 * row["dead_by_cp"][c if c in row["dead_by_cp"] else str(c)] for c in cps],
                    color=COLORS[arm], marker="o", markersize=3, label=LABELS[arm])
        ax.set_title(regime_title(reg))
        ax.set_xlabel("era")
    np.atleast_1d(axes)[0].set_ylabel("dead hidden units (%)")
    np.atleast_1d(axes)[0].legend(frameon=False, fontsize=7)
    save(fig, out, "fig5_dead_units")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    args = ap.parse_args(argv)
    out = os.path.join(ROOT, "paper", "figures", args.phase)
    os.makedirs(out, exist_ok=True)
    s = analyse(args.phase)
    fig_online(s, out)
    fig_trajectories(s, out)
    fig_paired(args.phase, s, out)
    fig_skill_map(args.phase, out)
    fig_diagnostics(s, out)
    print("figures written to", out)


if __name__ == "__main__":
    main()
