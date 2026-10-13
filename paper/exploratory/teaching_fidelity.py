"""Exploratory check, 2026-10-13 (after the v2b pilot): how much of what a
parent knows does a TEACH child know right after teaching?

A parent trains continually for 20 eras (slow pace, 800 steps per era), then
a fresh child is taught exactly as in the TEACH arm (half an era's budget).
We compare per-skill linear readouts of parent and child, by skill size, and
also try a longer teaching budget. Seeds 60-64 are outside every pool.

    python paper/exploratory/teaching_fidelity.py
"""
import os
import sys
os.environ["OPENBLAS_NUM_THREADS"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import multiprocessing as mp  # noqa: E402

import numpy as np  # noqa: E402

from learners.arms import FWD  # noqa: E402
from learners.net import MLP  # noqa: E402
from learners.run import knowledge, load_protocol  # noqa: E402
from learners.world import SkillWorld, random_inputs  # noqa: E402


def job(seed):
    p = load_protocol()
    world = SkillWorld(seed, 6, 120)
    rng = np.random.default_rng([seed, 1])
    parent = MLP(np.random.default_rng([seed, 2]), lr=p["lr"])
    for era in range(20):
        for _ in range(p["steps_per_era"]):
            parent.train_step(*world.batch(world.tasks[era], rng, 32))
    n = world.n_introduced(19)
    kp = np.array(knowledge(parent, world, n, (seed, 9)))
    budget = p["steps_per_era"] * 32 * 3 * FWD
    out = {"seed": seed, "parent_known": int((kp >= 0.9).sum()), "n": n}
    for mult in (0.5, 2.0, 8.0):  # share of an era's budget spent teaching
        child = MLP(np.random.default_rng([seed, 3]), lr=p["lr"])
        steps = int(budget * mult) // (32 * 4 * FWD)
        for _ in range(steps):
            child.teach_step(parent, random_inputs(rng, 32))
        kc = np.array(knowledge(child, world, n, (seed, 9)))
        known_p = kp >= 0.9
        out[f"child_known_x{mult}"] = int((kc >= 0.9).sum())
        out[f"kept_of_parent_x{mult}"] = int(((kc >= 0.9) & known_p).sum())
        deg = np.array(world.degrees[:n])
        out[f"kept_by_degree_x{mult}"] = {int(d): f"{int(((kc >= 0.9) & known_p & (deg == d)).sum())}/{int((known_p & (deg == d)).sum())}"
                                         for d in sorted(set(deg[known_p]))}
    return out


if __name__ == "__main__":
    with mp.Pool(4) as pool:
        for r in pool.map(job, range(60, 65)):
            print(r, flush=True)
