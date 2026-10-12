"""Analysis: discovery on one seed pool, confirmation on a disjoint pool.

The design deliberately separates *finding* an effect from *confirming* it:

  observation  -> candidate (significant on the discovery pool)
               -> replicated (same-direction, significant on the fresh pool)
               -> robust     (replicated AND survives Bonferroni across all
                              comparisons made in the study)

Reports always carry effect size, a bootstrap confidence interval, the number
of comparisons made, and failed replications. No bare "confidence %" labels.
Standard library only: significance uses a permutation test, so no distribution
assumptions and no third-party stats packages.
"""

from __future__ import annotations

import json
import os
import random
import statistics
from typing import Dict, List, Optional, Tuple

from . import records

ALPHA = 0.05
PERM = 8000
BOOT = 4000
_RNG = random.Random(20261012)   # fixed so analysis is reproducible

# Pairwise comparisons the study makes, and the metric each targets.
COMPARISONS = [
    ("related", "none", "recovery_ratio"),
    ("related", "unrelated", "recovery_ratio"),
    ("unrelated", "none", "recovery_ratio"),
    ("related", "none", "R_lifetime"),
    ("related", "none", "extinct"),
    ("related", "none", "memory_trust_end"),
]


# ---- metric extraction ---------------------------------------------------
def _metric(row, metric: str) -> Optional[float]:
    if metric == "extinct":
        return float(row["extinct"])
    if metric in ("R_lifetime", "recovery_ratio", "final_population"):
        v = row[metric]
        return None if v is None else float(v)
    if metric == "memory_trust_end":
        result = json.loads(row["result_json"])
        end = result.get("trait_means_by_phase", {}).get("end", {})
        if end.get("n", 0) == 0:
            return None
        return float(end.get("memory_trust"))
    raise ValueError(metric)


def _values(conn, study: str, condition: str, seed_pool: str, metric: str) -> List[float]:
    rows = records.fetch(conn, study, condition=condition, seed_pool=seed_pool)
    vals = [_metric(r, metric) for r in rows]
    return [v for v in vals if v is not None]


# ---- statistics (stdlib only) --------------------------------------------
def _mean(xs: List[float]) -> float:
    return statistics.fmean(xs) if xs else float("nan")


def permutation_p(a: List[float], b: List[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 1.0
    obs = abs(_mean(a) - _mean(b))
    pooled = a + b
    na = len(a)
    hits = 0
    for _ in range(PERM):
        _RNG.shuffle(pooled)
        diff = abs(_mean(pooled[:na]) - _mean(pooled[na:]))
        if diff >= obs - 1e-12:
            hits += 1
    return (hits + 1) / (PERM + 1)


def cliffs_delta(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    gt = sum(1 for x in a for y in b if x > y)
    lt = sum(1 for x in a for y in b if x < y)
    return (gt - lt) / (len(a) * len(b))


def cohens_d(a: List[float], b: List[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    va, vb = statistics.pvariance(a), statistics.pvariance(b)
    pooled = (((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2)) ** 0.5
    if pooled == 0:
        return 0.0
    return (_mean(a) - _mean(b)) / pooled


def boot_ci_diff(a: List[float], b: List[float]) -> Tuple[float, float]:
    if len(a) < 2 or len(b) < 2:
        return (float("nan"), float("nan"))
    diffs = []
    for _ in range(BOOT):
        ra = [a[_RNG.randrange(len(a))] for _ in a]
        rb = [b[_RNG.randrange(len(b))] for _ in b]
        diffs.append(_mean(ra) - _mean(rb))
    diffs.sort()
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs)) - 1]
    return (round(lo, 4), round(hi, 4))


# ---- discovery -> confirmation protocol ----------------------------------
def _compare(conn, study, cond_a, cond_b, metric, seed_pool) -> Dict:
    a = _values(conn, study, cond_a, seed_pool, metric)
    b = _values(conn, study, cond_b, seed_pool, metric)
    return {
        "metric": metric,
        "a": cond_a,
        "b": cond_b,
        "seed_pool": seed_pool,
        "n_a": len(a),
        "n_b": len(b),
        "mean_a": round(_mean(a), 4) if a else None,
        "mean_b": round(_mean(b), 4) if b else None,
        "diff": round(_mean(a) - _mean(b), 4) if a and b else None,
        "p": round(permutation_p(a, b), 5),
        "cohens_d": round(cohens_d(a, b), 4),
        "cliffs_delta": round(cliffs_delta(a, b), 4),
        "ci95_diff": boot_ci_diff(a, b),
    }


def analyze_study(conn, study: str) -> Dict:
    comparisons = []
    n_comparisons = len(COMPARISONS)
    bonferroni = ALPHA / n_comparisons

    for cond_a, cond_b, metric in COMPARISONS:
        disc = _compare(conn, study, cond_a, cond_b, metric, "discovery")
        conf = _compare(conn, study, cond_a, cond_b, metric, "confirmation")

        candidate = disc["p"] is not None and disc["p"] < ALPHA and disc["diff"] not in (None, 0)
        same_direction = (
            candidate
            and conf["diff"] is not None
            and (disc["diff"] > 0) == (conf["diff"] > 0)
        )
        replicated = same_direction and conf["p"] < ALPHA
        robust = replicated and conf["p"] < bonferroni

        if robust:
            status = "ROBUST"
        elif replicated:
            status = "REPLICATED"
        elif candidate:
            status = "CANDIDATE"
        else:
            status = "NOT SUPPORTED"

        comparisons.append({
            "label": f"{cond_a} vs {cond_b} on {metric}",
            "status": status,
            "discovery": disc,
            "confirmation": conf,
        })

    return {
        "study": study,
        "n_comparisons": n_comparisons,
        "alpha": ALPHA,
        "bonferroni_alpha": round(bonferroni, 5),
        "note": (
            f"{n_comparisons} comparisons were made; 'ROBUST' requires the "
            f"confirmation-pool p to clear the Bonferroni threshold "
            f"{round(bonferroni, 5)}. Candidates that did not replicate on the "
            f"fresh seed pool are retained and shown, not discarded."
        ),
        "comparisons": comparisons,
    }


def main() -> None:
    conn = records.connect()
    found = records.studies(conn)
    if not found:
        print("No runs in the database yet. Run: python -m experiments.study_inheritance")
        return
    os.makedirs("experiments/snapshots", exist_ok=True)
    for study in found:
        report = analyze_study(conn, study)
        path = f"experiments/snapshots/{study}.json"
        with open(path, "w") as fh:
            json.dump(report, fh, indent=2)
        print(f"\n=== {study} ===")
        print(report["note"])
        for c in report["comparisons"]:
            d, f = c["discovery"], c["confirmation"]
            print(
                f"  [{c['status']:>13}] {c['label']:<40} "
                f"disc diff={d['diff']} p={d['p']}  "
                f"conf diff={f['diff']} p={f['p']} d={f['cohens_d']} CI={f['ci95_diff']}"
            )
        print(f"  snapshot -> {path}")


if __name__ == "__main__":
    main()
