"""The pre-registered analysis for Study 1b (PREREGISTRATION_1b.md §7).

    python -m learners.analysis_1b --phase pilot_1b
    python -m learners.analysis_1b --phase confirmation_1b

Uses Study 1's statistics unchanged (learners/analysis.py): per-seed paired
differences, a two-sided sign-flip permutation test, a 95% bootstrap CI and
paired Cohen's d_z, with Holm-Bonferroni across the whole family. Writes
paper/results/<phase>_summary.json and <phase>_summary.md.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
from typing import Dict, List

import numpy as np

from . import analysis as A
from .arms_1b import ARM_ORDER_1B

# (id, label, a, b, outcome, counted per, predicted direction, prior)
HYPOTHESES = [
    ("B1", "Copying helps, with default settings", "COPY4", "SOLO4", "FINAL_FRONTIER", "condition", "lean yes", 0.55),
    ("B2", "Copying helps, with varied settings", "COPY4P", "SOLO4P", "FINAL_FRONTIER", "condition", "lean yes", 0.55),
    ("B3", "Fewer updates keep the next step open", "QUARTER", "IMMORTAL", "FINAL_FRONTIER", "world", "yes", 0.60),
    ("B4", "Measuring the best of four helps", "SOLO4", "QUARTER", "FINAL_FRONTIER", "world", "lean yes", 0.60),
    ("B5", "Varied starting settings help", "SOLO4P", "SOLO4", "FINAL_FRONTIER", "world", "lean yes", 0.55),
    ("B6", "Learning-rate mutation helps", "CLONE", "COPY4P", "FINAL_FRONTIER", "condition", "lean yes", 0.55),
    ("B7", "Study 1's H3c replicates", "CLONE", "IMMORTAL", "FINAL_FRONTIER", "condition", "yes", 0.90),
    ("B8", "Fewer updates preserve plasticity", "QUARTER", "IMMORTAL", "FINAL_NOVEL", "world", "yes", 0.70),
    ("B9", "Copying preserves plasticity", "COPY4", "SOLO4", "FINAL_NOVEL", "condition", "uncertain", 0.50),
]
# The decomposition path of §7, in its pre-registered order.
PATH = ["IMMORTAL", "QUARTER", "SOLO4", "SOLO4P", "COPY4P", "CLONE"]
LEARNED = 0.9
EXTRA = ("FRONTIER_LEARNED", "FRONTIER_FIXED_LR", "NOVEL_FIXED_LR")


def outcome(rec: Dict, name: str) -> float:
    if name == "FRONTIER_LEARNED":
        last = max(rec["probes"], key=int)
        return float(np.mean([a >= LEARNED for a in rec["probes"][last]["frontier"]]))
    return A.outcome(rec, name)


def paired(t, a, b, R, L, name, rng) -> Dict:
    """Study 1's paired comparison (analysis.paired), able to read FRONTIER_LEARNED."""
    X, Y = t[(a, R, L)], t[(b, R, L)]
    seeds = sorted(set(X) & set(Y))
    d = np.array([outcome(X[s], name) - outcome(Y[s], name) for s in seeds])
    sd = d.std(ddof=1) if len(d) > 1 else 0.0
    lo, hi = A.bootstrap_ci(d, rng)
    return {"a": a, "b": b, "outcome": name, "n": len(d), "diff": float(d.mean()),
            "ci": [lo, hi], "dz": float(d.mean() / sd) if sd > 0 else None,
            "p": A.signflip_p(d, rng), "per_seed": [round(float(v), 4) for v in d]}


def spearman(x: List[float], y: List[float]) -> float:
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def analyse(phase: str) -> Dict:
    recs = A.load(phase)
    t = A.table(recs)
    rng = np.random.default_rng(20261013)
    Rs = sorted({r["R"] for r in recs})
    Ls = sorted({r["L"] for r in recs if r["L"]})
    cps = sorted({int(k) for r in recs for k in r["probes"]})
    arms = ["SCRATCH"] + ARM_ORDER_1B
    members, regimes = [], []
    for hid, label, a, b, name, per, predicted, prior in HYPOTHESES:
        # comparisons among arms that never reproduce count once per world:
        # their records are the same at every lifespan
        for R, L in itertools.product(Rs, Ls if per == "condition" else Ls[:1]):
            c = paired(t, a, b, R, L, name, rng)
            members.append({"id": hid, "label": f"{label}: {name} {a} > {b}", "parts": [c],
                            "p": c["p"], "direction_ok": bool(c["diff"] > 0), "predicted": predicted,
                            "prior": prior, "regime": {"R": R, "L": L if per == "condition" else None}})
    A.holm(members)
    for m in members:
        m["verdict"] = A.verdict(m)
    for R, L in itertools.product(Rs, Ls):
        desc = A.descriptives(t, R, L, arms, cps)
        for arm, row in desc.items():
            for name in EXTRA:
                v = [outcome(r, name) for r in t[(arm, R, L)].values()]
                row[name] = [float(np.nanmean(v)), float(np.nanstd(v, ddof=1)) if len(v) > 1 else 0.0]
        means = [desc[a]["FINAL_FRONTIER"][0] for a in PATH]
        steps = [{"from": PATH[i], "to": PATH[i + 1], "diff": means[i + 1] - means[i]}
                 for i in range(len(PATH) - 1)]
        seeds = sorted(t[("SOLO4P", R, L)])
        reps = [t[("SOLO4P", R, L)][s]["diag"][str(cps[-1])]["rep"] for s in seeds]
        front = [outcome(t[("SOLO4P", R, L)][s], "FINAL_FRONTIER") for s in seeds]
        settings = {k: spearman([np.log(r[k]) if k != "init_scale" else r[k] for r in reps], front)
                    for k in ("lr", "wd", "init_scale")}
        regimes.append({"R": R, "L": L, "arms": desc,
                        "decomposition": {"total": means[-1] - means[0], "steps": steps},
                        "exploratory_settings_spearman": settings,
                        "family": [m for m in members if m["regime"]["R"] == R
                                   and m["regime"]["L"] in (L, None)]})
    return {"phase": phase, "n_records": len(recs), "protocol_hash": recs[0]["protocol_hash"],
            "code_commits": sorted({r["code_commit"] for r in recs}),
            "seeds": sorted({r["seed"] for r in recs}), "family_size": len(members),
            "family": members, "regimes": regimes,
            "exploratory": not phase.startswith("confirmation")}


def to_markdown(s: Dict) -> str:
    pct = lambda v: f"{100 * v:.1f}"
    lines = [f"# Study 1b — {s['phase']} summary", ""]
    if s["exploratory"]:
        lines += ["**Exploratory.** These are pilot seeds. Verdicts use the pre-registered tests, "
                  "but only confirmation seeds can support a claim.", ""]
    lines += [f"Records: {s['n_records']} · seeds: {s['seeds'][0]}–{s['seeds'][-1]} "
              f"({len(s['seeds'])}) · protocol {s['protocol_hash']} · "
              f"Holm–Bonferroni across {s['family_size']} family members", "",
              "## Hypotheses", "",
              "| # | Hypothesis | World | Lifespan | Predicted | Difference (pts, 95% CI) | d_z | p | p (Holm) | Verdict |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for m in s["family"]:
        p = m["parts"][0]
        dz = f"{p['dz']:.2f}" if p["dz"] is not None else "—"
        L = m["regime"]["L"] or "any"
        lines.append(f"| {m['id']} | {m['label']} | R={m['regime']['R']} | {L} | {m['predicted']} "
                     f"({int(100 * m['prior'])}%) | {pct(p['diff'])} [{pct(p['ci'][0])}, {pct(p['ci'][1])}] | "
                     f"{dz} | {m['p']:.4f} | {m['p_holm']:.4f} | {m['verdict']} |")
    lines.append("")
    for reg in s["regimes"]:
        lines += [f"## New skill every {reg['R']} eras, lifespan {reg['L']} eras", "",
                  "| Arm | FRONTIER | fully learned | FRONTIER at default lr | NOVEL | KNOWLEDGE | ONLINE | dead units |",
                  "|---|---|---|---|---|---|---|---|"]
        for arm, row in reg["arms"].items():
            cell = lambda k: f"{pct(row[k][0])} ± {pct(row[k][1])}" if k in row and row[k][0] == row[k][0] else "—"
            dead = f"{pct(row['dead_by_cp'][max(row['dead_by_cp'])])}%" if "dead_by_cp" in row else "—"
            lines.append(f"| {arm} | {cell('FINAL_FRONTIER')} | {cell('FRONTIER_LEARNED')} | "
                         f"{cell('FRONTIER_FIXED_LR')} | {cell('FINAL_NOVEL')} | {cell('FINAL_KNOWLEDGE')} | "
                         f"{cell('ONLINE')} | {dead} |")
        d = reg["decomposition"]
        lines += ["", f"Decomposition of CLONE − IMMORTAL in FRONTIER ({pct(d['total'])} pts), "
                  "along the pre-registered path (descriptive): "
                  + "; ".join(f"{st['from']} → {st['to']} {pct(st['diff'])}" for st in d["steps"]),
                  "", "Exploratory: within SOLO4P, Spearman correlation of the representative's settings "
                  "with FRONTIER: " + ", ".join(f"{k} {v:.2f}" for k, v in reg["exploratory_settings_spearman"].items()),
                  ""]
    return "\n".join(lines)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    args = ap.parse_args(argv)
    s = analyse(args.phase)
    os.makedirs(A.OUT_DIR, exist_ok=True)
    with open(os.path.join(A.OUT_DIR, f"{args.phase}_summary.json"), "w") as f:
        json.dump(s, f, indent=1)
    md = to_markdown(s)
    with open(os.path.join(A.OUT_DIR, f"{args.phase}_summary.md"), "w") as f:
        f.write(md)
    print(md)


if __name__ == "__main__":
    main()
