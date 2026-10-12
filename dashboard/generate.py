"""Build docs/data.json from the local results database.

The dashboard under docs/ is static (GitHub Pages cannot run experiments). This
script summarises the raw records into the small JSON file the page reads, so
the published site shows results without publishing the raw history.
"""

from __future__ import annotations

import json
import os
import statistics
import time
from typing import Dict, List

from experiments import records
from experiments.analysis import analyze_study
from sim import __version__

OUT = "docs/data.json"


def _pad(series: List[int], length: int) -> List[int]:
    """Extinct runs stop early; their population after extinction is 0."""
    return series + [0] * (length - len(series))


def _trajectories(rows, max_steps: int) -> Dict:
    padded = [_pad(json.loads(r["result_json"])["population_by_step"], max_steps) for r in rows]
    mean, q1, q3 = [], [], []
    for step in range(max_steps):
        col = sorted(p[step] for p in padded)
        mean.append(round(statistics.fmean(col), 2))
        q = statistics.quantiles(col, n=4) if len(col) >= 2 else [col[0]] * 3
        q1.append(round(q[0], 2))
        q3.append(round(q[2], 2))
    return {"mean": mean, "q1": q1, "q3": q3}


def build(conn) -> Dict:
    studies = []
    total_runs = 0
    commits = set()
    for study in records.studies(conn):
        rows = records.fetch(conn, study)
        total_runs += len(rows)
        commits.update(r["code_commit"] for r in rows)
        params = json.loads(rows[0]["params_json"])
        max_steps = params["max_steps"]
        conditions = sorted({r["condition"] for r in rows})

        per_condition = {}
        for cond in conditions:
            crow = [r for r in rows if r["condition"] == cond]
            per_condition[cond] = {
                "n_runs": len(crow),
                "extinction_rate": round(sum(r["extinct"] for r in crow) / len(crow), 4),
                "trajectory": _trajectories(crow, max_steps),
                "recovery": [
                    {"seed": r["seed"], "pool": r["seed_pool"], "value": r["recovery_ratio"]}
                    for r in crow if r["recovery_ratio"] is not None
                ],
            }

        studies.append({
            "study": study,
            "engine": rows[0]["engine"],
            "params": params,
            "conditions": conditions,
            "per_condition": per_condition,
            "analysis": analyze_study(conn, study),
        })

    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "simulator_version": __version__,
        "code_commits": sorted(commits),
        "total_runs": total_runs,
        "studies": studies,
    }


def main() -> None:
    conn = records.connect()
    data = build(conn)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print(f"Wrote {OUT}: {data['total_runs']} runs across {len(data['studies'])} studies.")


if __name__ == "__main__":
    main()
