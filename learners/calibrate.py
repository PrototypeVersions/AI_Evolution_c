"""Calibration (PREREGISTRATION_v2.md §7 as amended by deviation 2): fix the
default learning rate, steps per era and probe steps by watching single
learners, never by comparing arms.

    python -m learners.calibrate      # writes calibration.json and protocol.json
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from .net import MLP  # noqa: E402
from .world import SkillWorld  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAL_SEEDS = list(range(1, 9))           # calibration worlds, disjoint from pilot and confirmation
LRS = [3e-4, 1e-3, 3e-3]
STEP_CHOICES = [200, 400, 800]
EARLY_ERAS, EARLY_TARGET = 40, 0.85
PROBE_CHOICES = [25, 50, 100, 200]
CLIMB_PACE = 2       # the fastest novelty interval in the grid
BATCH, EVAL_N = 32, 2000
PROBE_TARGET = 0.75  # fresh-network NOVEL accuracy the probe length aims for (chance = 0.5)

FIXED = {  # pre-registered values that calibration does not touch
    "batch": BATCH, "n_eras": 120, "checkpoints": [20, 40, 60, 80, 100, 120],
    "eval_n": EVAL_N, "pop": 4, "teach_share": 0.5, "reset_shrink": 0.8,
    "reset_noise": 0.1, "fitness_window": 20,
    "regimes": {"novelty_interval": [2, 6], "lifespan": [5, 20]},
}


def early_accuracy(args) -> float:
    """One continually trained learner follows the first EARLY_ERAS eras of a
    stream at the grid's fastest pace with S steps per era. Returns its mean
    end-of-era accuracy: can a learner that keeps up climb this world?"""
    seed, lr, S = args
    world = SkillWorld(seed, CLIMB_PACE, EARLY_ERAS)
    rng = np.random.default_rng([seed, 103])
    net = MLP(np.random.default_rng([seed, 104]), lr=lr)
    accs = []
    for e, task in enumerate(world.tasks):
        for _ in range(S):
            net.train_step(*world.batch(task, rng, BATCH))
        accs.append(net.accuracy(*world.batch(task, np.random.default_rng([seed, 105, e]), EVAL_N)))
    return float(np.mean(accs))


def novel_curve(seed: int, lr: float):
    """Fresh networks on single reserved-skill tasks after each candidate K."""
    world = SkillWorld(seed, 2, 120)
    novel = world.probes(120)["novel"]
    accs = {k: [] for k in PROBE_CHOICES}
    for i, skill in enumerate(novel):
        net = MLP(np.random.default_rng([seed, 106, i]), lr=lr)
        rng = np.random.default_rng([seed, 107, i])
        ex, ey = world.skill_batch(skill, np.random.default_rng([seed, 108, i]), EVAL_N)
        for step in range(1, max(PROBE_CHOICES) + 1):
            net.train_step(*world.skill_batch(skill, rng, BATCH))
            if step in accs:
                accs[step].append(net.accuracy(ex, ey))
    return accs


def main() -> None:
    import multiprocessing as mp
    grid = [(seed, lr, S) for S in STEP_CHOICES for lr in LRS for seed in CAL_SEEDS]
    with mp.get_context("fork").Pool(os.cpu_count() or 1) as pool:
        scores = dict(zip(grid, pool.map(early_accuracy, grid)))
    mean = {(lr, S): float(np.mean([scores[(s, lr, S)] for s in CAL_SEEDS]))
            for S in STEP_CHOICES for lr in LRS}
    best = {S: max(LRS, key=lambda lr: (mean[(lr, S)], -lr)) for S in STEP_CHOICES}
    ok = [S for S in STEP_CHOICES if mean[(best[S], S)] >= EARLY_TARGET]
    S = ok[0] if ok else max(STEP_CHOICES, key=lambda v: mean[(best[v], v)])
    lr = best[S]

    curves = {k: [] for k in PROBE_CHOICES}
    for s in CAL_SEEDS:
        for k, v in novel_curve(s, lr).items():
            curves[k].extend(v)
    novel_means = {k: float(np.mean(v)) for k, v in curves.items()}
    K = min(PROBE_CHOICES, key=lambda k: (abs(novel_means[k] - PROBE_TARGET), k))

    cal = {"seeds": CAL_SEEDS, "pace": CLIMB_PACE, "early_eras": EARLY_ERAS,
           "early_target": EARLY_TARGET,
           "early_accuracy": {f"lr={lr} S={S}": v for (lr, S), v in mean.items()},
           "early_accuracy_per_seed": {f"lr={lr} S={S} seed={sd}": v for (sd, lr, S), v in scores.items()},
           "target_met": bool(ok),
           "novel_probe_mean_by_K": {str(k): v for k, v in novel_means.items()},
           "chosen": {"lr": lr, "steps_per_era": S, "probe_steps": K}}
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(cal, f, indent=2)
    proto = {**FIXED, "lr": lr, "steps_per_era": S, "probe_steps": K, "frozen": False}
    with open(os.path.join(HERE, "protocol.json"), "w") as f:
        json.dump(proto, f, indent=2)
    print(json.dumps({k: v for k, v in cal.items() if k != "early_accuracy_per_seed"}, indent=2))


if __name__ == "__main__":
    main()
