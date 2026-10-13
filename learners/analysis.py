"""The pre-registered analysis for Study 1 (PREREGISTRATION_v2.md §6 and §9).

    python -m learners.analysis --phase pilot
    python -m learners.analysis --phase confirmation

Reads learners/results/<phase>.jsonl and writes paper/results/<phase>_summary.json
and a readable table, <phase>_summary.md. Every comparison uses per-seed
paired differences: a two-sided sign-flip permutation test, a 95% bootstrap CI,
and paired Cohen's d_z. Holm-Bonferroni runs across the whole family.
"""

from __future__ import annotations

import argparse
import collections
import itertools
import json
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(ROOT, "paper", "results")
N_PERM = 10_000
N_BOOT = 10_000
ALPHA = 0.05


# ---- loading ---------------------------------------------------------------
def load(phase: str, protocol_hash: Optional[str] = None) -> List[Dict]:
    path = os.path.join(HERE, "results", f"{phase}.jsonl")
    recs = [json.loads(line) for line in open(path)]
    hashes = collections.Counter(r["protocol_hash"] for r in recs)
    want = protocol_hash or hashes.most_common(1)[0][0]
    return [r for r in recs if r["protocol_hash"] == want]


def table(recs: List[Dict]) -> Dict[Tuple[str, int, int], Dict[int, Dict]]:
    """(arm, R, L) -> {seed: record}. IMMORTAL and SCRATCH (L = 0) are copied
    into every lifespan, since they do not depend on it."""
    lifespans = sorted({r["L"] for r in recs if r["L"]})
    t = collections.defaultdict(dict)
    for r in recs:
        for L in (lifespans if r["L"] == 0 else [r["L"]]):
            t[(r["arm"], r["R"], L)][r["seed"]] = r
    return t


PRIMARY = ("FINAL_FRONTIER", "FINAL_KNOWLEDGE", "FINAL_NOVEL", "ONLINE")


def outcome(rec: Dict, name: str) -> float:
    """A named outcome; "KIND@cp" reads a probe at a checkpoint."""
    if "@" in name:
        kind, cp = name.split("@")
        p = rec["probes"][cp]
        return float(p["known_share"]) if kind == "KNOWLEDGE" else float(np.mean(p[kind.lower()]))
    return float(rec[name])


# ---- statistics ------------------------------------------------------------
def signflip_p(d: np.ndarray, rng: np.random.Generator, shift: float = 0.0,
               one_sided: bool = False) -> float:
    """Permutation p-value for mean(d) - shift. Exact when 2^n <= N_PERM."""
    x = d - shift
    n = len(x)
    obs = x.mean()
    if 2 ** n <= N_PERM:
        signs = np.array(list(itertools.product([-1.0, 1.0], repeat=n)))
    else:
        signs = rng.choice([-1.0, 1.0], size=(N_PERM, n))
    null = (signs * np.abs(x)).mean(axis=1)
    if one_sided:
        return float((np.sum(null >= obs - 1e-12) + 1) / (len(null) + 1))
    return float((np.sum(np.abs(null) >= abs(obs) - 1e-12) + 1) / (len(null) + 1))


def bootstrap_ci(d: np.ndarray, rng: np.random.Generator) -> Tuple[float, float]:
    idx = rng.integers(0, len(d), size=(N_BOOT, len(d)))
    means = d[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired(t, a: str, b: str, R: int, L: int, name: str, rng, **kw) -> Dict:
    """Compare arm a with arm b (a - b) on outcome `name` in one regime."""
    A, B = t[(a, R, L)], t[(b, R, L)]
    seeds = sorted(set(A) & set(B))
    d = np.array([outcome(A[s], name) - outcome(B[s], name) for s in seeds])
    sd = d.std(ddof=1) if len(d) > 1 else 0.0
    lo, hi = bootstrap_ci(d, rng)
    return {"a": a, "b": b, "outcome": name, "n": len(d), "diff": float(d.mean()),
            "ci": [lo, hi], "dz": float(d.mean() / sd) if sd > 0 else None,
            "p": signflip_p(d, rng, **kw), "per_seed": [round(float(v), 4) for v in d]}


def within(t, arm: str, R: int, L: int, later: str, earlier: str, rng) -> Dict:
    """Change within one arm between two measurements (later - earlier)."""
    A = t[(arm, R, L)]
    seeds = sorted(A)
    d = np.array([outcome(A[s], later) - outcome(A[s], earlier) for s in seeds])
    sd = d.std(ddof=1) if len(d) > 1 else 0.0
    lo, hi = bootstrap_ci(d, rng)
    return {"a": f"{arm} {later}", "b": f"{arm} {earlier}", "outcome": later.split("@")[0],
            "n": len(d), "diff": float(d.mean()), "ci": [lo, hi],
            "dz": float(d.mean() / sd) if sd > 0 else None, "p": signflip_p(d, rng),
            "per_seed": [round(float(v), 4) for v in d]}


# ---- the pre-registered family ---------------------------------------------
def family(t, R: int, L: int, last: int, first: int, rng) -> List[Dict]:
    """Eleven family members per regime, each with its predicted direction."""
    F = []

    def part(c, sign):
        c["direction_ok"] = bool(np.sign(c["diff"]) == sign)
        return c

    def member(hid, label, parts, predicted):
        # A member passes only when every part is in its hypothesised direction;
        # its p-value is the largest of its parts' p-values.
        F.append({"id": hid, "label": label, "parts": parts, "predicted": predicted,
                  "p": max(p["p"] for p in parts),
                  "direction_ok": all(p["direction_ok"] for p in parts)})

    cmp = lambda a, b, name: part(paired(t, a, b, R, L, name, rng), 1)
    member("H1", "IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint",
           [part(within(t, "IMMORTAL", R, L, f"NOVEL@{last}", f"NOVEL@{first}", rng), -1)], "yes")
    member("H2a", "Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART",
           [cmp("IMMORTAL", "RESTART", "FINAL_KNOWLEDGE")], "yes")
    member("H2b", "Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES",
           [cmp("CLONE", "GENES", "FINAL_KNOWLEDGE")], "yes")
    member("H3a", "Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL",
           [cmp("TEACH", "IMMORTAL", "FINAL_FRONTIER")], "yes")
    member("H3b", "Teaching performs better on the stream: ONLINE TEACH > IMMORTAL",
           [cmp("TEACH", "IMMORTAL", "ONLINE")], "yes")
    member("H3c", "Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL",
           [cmp("CLONE", "IMMORTAL", "FINAL_FRONTIER")], "no")
    member("H4a", "Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET",
           [cmp("TEACH", "RESET", "FINAL_FRONTIER")], "lean yes")
    member("H4b", "Teaching is more than a reset: ONLINE TEACH > RESET",
           [cmp("TEACH", "RESET", "ONLINE")], "lean yes")
    member("H5", "Selection on learning settings helps: ONLINE GENES > RANDOM",
           [cmp("GENES", "RANDOM", "ONLINE")], "yes")
    member("H6", "Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM",
           [cmp("IMMORTAL", b, "ONLINE") for b in ("CLONE", "GENES", "RANDOM")], "yes")
    member("H7", "Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART",
           [cmp("TEACH", "RESTART", "FINAL_KNOWLEDGE")], "yes")
    return F


def holm(members: List[Dict]) -> None:
    order = sorted(range(len(members)), key=lambda i: members[i]["p"])
    m = len(members)
    running = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, (m - rank) * members[i]["p"])
        running = max(running, adj)
        members[i]["p_holm"] = running


def verdict(mem: Dict) -> str:
    sig = mem["p_holm"] < ALPHA
    if sig and mem["direction_ok"]:
        return "SUPPORTED"
    if sig and not mem["direction_ok"]:
        return "REVERSED"
    return "NOT SUPPORTED"


def descriptives(t, R: int, L: int, arms: List[str], cps: List[int]) -> Dict:
    out = {}
    for arm in arms:
        recs = list(t.get((arm, R, L), {}).values())
        if not recs:
            continue
        row = {"n": len(recs)}
        for name in PRIMARY + ("FINAL_DEPTH",):
            if name in recs[0]:
                v = [outcome(r, name) for r in recs]
                row[name] = [float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0]
        for kind in ("NOVEL", "FRONTIER", "KNOWLEDGE"):
            row[kind.lower() + "_by_cp"] = {cp: float(np.mean([outcome(r, f"{kind}@{cp}") for r in recs]))
                                            for cp in cps}
        row["depth_by_cp"] = {cp: float(np.mean([r["probes"][str(cp)]["deepest_known"] for r in recs]))
                              for cp in cps}
        if "online" in recs[0]:
            row["online_curve"] = [float(v) for v in np.mean([r["online"] for r in recs], axis=0)]
        if "diag" in recs[0]:
            row["dead_by_cp"] = {cp: float(np.mean([r["diag"][str(cp)]["dead"] for r in recs])) for cp in cps}
            row["wnorm_by_cp"] = {cp: float(np.mean([r["diag"][str(cp)]["weight_norm"] for r in recs])) for cp in cps}
            row["rep_lr_end"] = float(np.median([r["diag"][str(cps[-1])]["rep"]["lr"] for r in recs]))
        out[arm] = row
    return out


def analyse(phase: str) -> Dict:
    recs = load(phase)
    t = table(recs)
    rng = np.random.default_rng(20261013)
    Rs = sorted({r["R"] for r in recs})
    Ls = sorted({r["L"] for r in recs if r["L"]})
    cps = sorted({int(k) for r in recs for k in r["probes"]})
    arms = ["SCRATCH", "IMMORTAL", "RESET", "RESTART", "TEACH", "CLONE", "GENES", "RANDOM"]
    regimes, all_members = [], []
    for R, L in itertools.product(Rs, Ls):
        F = family(t, R, L, cps[-1], cps[0], rng)
        for mem in F:
            mem["regime"] = {"R": R, "L": L}
        all_members.extend(F)
        regimes.append({"R": R, "L": L, "arms": descriptives(t, R, L, arms, cps), "family": F})
    holm(all_members)
    for mem in all_members:
        mem["verdict"] = verdict(mem)
    return {"phase": phase, "n_records": len(recs),
            "protocol_hash": recs[0]["protocol_hash"],
            "code_commits": sorted({r["code_commit"] for r in recs}),
            "seeds": sorted({r["seed"] for r in recs}), "family_size": len(all_members),
            "regimes": regimes, "exploratory": phase != "confirmation"}


def to_markdown(s: Dict) -> str:
    pct = lambda v: f"{100 * v:.1f}"
    lines = [f"# Study 1 — {s['phase']} summary", ""]
    if s["exploratory"]:
        lines += ["**Exploratory.** These are pilot seeds. Verdicts use the pre-registered tests, "
                  "but only confirmation seeds can support a claim.", ""]
    lines += [f"Records: {s['n_records']} · seeds: {s['seeds'][0]}–{s['seeds'][-1]} "
              f"({len(s['seeds'])}) · protocol {s['protocol_hash']} · "
              f"Holm–Bonferroni across {s['family_size']} family members", ""]
    for reg in s["regimes"]:
        lines += [f"## Regime: new skill every {reg['R']} eras, lifespan {reg['L']} eras", "",
                  "| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |",
                  "|---|---|---|---|---|---|---|"]
        for arm, row in reg["arms"].items():
            cell = lambda k: f"{pct(row[k][0])} ± {pct(row[k][1])}" if k in row else "—"
            dead = f"{pct(row['dead_by_cp'][max(row['dead_by_cp'])])}%" if "dead_by_cp" in row else "—"
            depth = f"{row['FINAL_DEPTH'][0]:.1f}" if "FINAL_DEPTH" in row else "—"
            lines.append(f"| {arm} | {cell('FINAL_FRONTIER')} | {cell('FINAL_KNOWLEDGE')} | {depth} | "
                         f"{cell('FINAL_NOVEL')} | {cell('ONLINE')} | {dead} |")
        lines += ["", "| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |",
                  "|---|---|---|---|---|---|---|"]
        for m in reg["family"]:
            diffs = "; ".join(f"{p['a']} − {p['b']} {p['outcome']}: {pct(p['diff'])} "
                              f"[{pct(p['ci'][0])}, {pct(p['ci'][1])}]" for p in m["parts"])
            lines.append(f"| {m['id']} | {m['label']} | {m['predicted']} | {diffs} | "
                         f"{m['p']:.4f} | {m['p_holm']:.4f} | {m['verdict']} |")
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    args = ap.parse_args(argv)
    s = analyse(args.phase)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{args.phase}_summary.json"), "w") as f:
        json.dump(s, f, indent=1)
    md = to_markdown(s)
    with open(os.path.join(OUT_DIR, f"{args.phase}_summary.md"), "w") as f:
        f.write(md)
    print(md)


if __name__ == "__main__":
    main()
