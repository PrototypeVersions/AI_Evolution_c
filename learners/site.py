"""Build the website's data file for Study 1 from the raw run records.

    python -m learners.site            # confirmation if it exists, else pilot
    python -m learners.site --phase pilot

Writes docs/study1.json. Every number on the site comes from here, and this
reads only learners/results/<phase>.jsonl (through learners.analysis), so
the site can always be rebuilt from the records.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List

from .analysis import analyse, load
from .run import ARM_ORDER, RESULTS_DIR, load_protocol, protocol_hash

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "study1.json")
ARMS = ["SCRATCH"] + ARM_ORDER


def r(x, n=4):
    if isinstance(x, list):
        return [r(v, n) for v in x]
    if isinstance(x, dict):
        return {k: r(v, n) for k, v in x.items()}
    return round(x, n) if isinstance(x, float) else x


def regime_block(reg: Dict) -> Dict:
    arms = {}
    for arm in ARMS:
        row = reg["arms"].get(arm)
        if not row:
            continue
        keep = {k: row[k] for k in ("n", "FINAL_FRONTIER", "FINAL_KNOWLEDGE", "FINAL_NOVEL", "ONLINE",
                                    "FINAL_DEPTH", "KNOWLEDGE_MEAN", "RECENT_KNOWLEDGE",
                                    "NOVEL_FIXED_LR", "FRONTIER_FIXED_LR", "frontier_by_cp",
                                    "knowledge_by_cp", "novel_by_cp", "depth_by_cp", "dead_by_cp",
                                    "online_curve") if k in row}
        # a NaN mean marks a measure these records do not have
        arms[arm] = {k: v for k, v in keep.items() if not (isinstance(v, list) and v and v[0] != v[0])}
    tests = [{"id": m["id"], "label": m["label"], "predicted": m["predicted"], "verdict": m["verdict"],
              "p": m["p"], "p_holm": m["p_holm"],
              "parts": [{k: p[k] for k in ("a", "b", "outcome", "diff", "ci", "dz", "per_seed", "direction_ok")}
                        for p in m["parts"]]}
             for m in reg["family"] + reg.get("secondary", [])]
    return {"R": reg["R"], "L": reg["L"], "arms": r(arms), "tests": r(tests)}


def world_block(recs: List[Dict], R: int, L: int) -> Dict:
    """One world's skill tree, and which skills each arm could read out at each
    checkpoint (for the skill-tree picture)."""
    scratch = sorted((x for x in recs if x["arm"] == "SCRATCH" and x["R"] == R), key=lambda x: x["seed"])
    if not scratch:
        return {}
    seed = scratch[0]["seed"]
    w = scratch[0]["world"]
    n_stream = min(w["reserved"]) if w["reserved"] else len(w["degrees"])
    known = {}
    for x in recs:
        if x["seed"] == seed and x["R"] == R and x["L"] in (0, L) and x["arm"] != "SCRATCH":
            known[x["arm"]] = {cp: p["knowledge"] for cp, p in x["probes"].items()}
    return {"seed": seed, "R": R, "L": L, "parents": w["parents"][:n_stream],
            "degrees": w["degrees"][:n_stream],
            "arrives": [0 if k < 4 else (k - 3) * R for k in range(n_stream)],
            "tasks": scratch[0]["tasks"],
            "knowledge": r(known, 3)}


def difficulty(recs: List[Dict], R: int) -> List[float]:
    """Mean size (bits) of the two skills in each era's task, over worlds."""
    curves = [[(x["world"]["degrees"][a] + x["world"]["degrees"][b]) / 2 for a, b in x["tasks"]]
              for x in recs if x["arm"] == "SCRATCH" and x["R"] == R]
    return [round(sum(c[e] for c in curves) / len(curves), 3) for e in range(len(curves[0]))] if curves else []


def build(phase: str) -> Dict:
    s = analyse(phase)
    recs = load(phase)
    proto = load_protocol()
    lin = {}
    for x in recs:
        if x["arm"] in ("TEACH4", "RESTART", "CLONE") and x["seed"] == s["seeds"][0] and x["R"] == 6 \
                and x["L"] == 20:
            lin[x["arm"]] = x["lineage"]
    return {
        "phase": phase, "exploratory": s["exploratory"], "seeds": [s["seeds"][0], s["seeds"][-1]],
        "n_seeds": len(s["seeds"]), "n_records": s["n_records"], "protocol_hash": s["protocol_hash"],
        "frozen_protocol_hash": protocol_hash(proto) if proto.get("frozen") else None,
        "code_commits": s["code_commits"], "family_size": s["family_size"],
        "secondary_family_size": s.get("secondary_family_size"),
        "eras": proto["n_eras"], "steps_per_era": proto["steps_per_era"], "batch": proto["batch"],
        "regimes": [regime_block(reg) for reg in s["regimes"]],
        "worlds": [world_block(recs, R, 20) for R in proto["regimes"]["novelty_interval"]],
        "difficulty": {str(R): difficulty(recs, R) for R in proto["regimes"]["novelty_interval"]},
        "lineages": lin,
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase")
    args = ap.parse_args(argv)
    phase = args.phase or ("confirmation" if os.path.exists(os.path.join(RESULTS_DIR, "confirmation.jsonl"))
                           else "pilot")
    data = build(phase)
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB) from {phase}")


if __name__ == "__main__":
    main()
