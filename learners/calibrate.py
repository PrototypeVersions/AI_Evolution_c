"""Calibration (PREREGISTRATION_v2.md §7): fix the default learning rate,
steps per era and probe steps by watching single learners, never by comparing
arms.

    python -m learners.calibrate      # writes calibration.json and protocol.json
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from .net import MLP  # noqa: E402
from .world import N_ROOTS, SkillWorld  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAL_SEEDS = list(range(1, 21))          # calibration worlds, disjoint from pilot and confirmation
LRS = [3e-4, 1e-3, 3e-3]
STEP_CHOICES = [100, 200, 300, 500, 800]
PROBE_CHOICES = [25, 50, 100, 200]
CLIMB_ERAS = 32
CLIMB_PACE = 2       # the fastest novelty interval in the grid
MAX_STEPS, CHECK_EVERY, TARGET = 3000, 25, 0.90
BATCH, EVAL_N = 32, 2000
PROBE_TARGET = 0.75  # fresh-network NOVEL accuracy the probe length aims for (chance = 0.5)

FIXED = {  # pre-registered values that calibration does not touch
    "batch": BATCH, "n_eras": 120, "checkpoints": [20, 40, 60, 80, 100, 120],
    "eval_n": EVAL_N, "pop": 4, "teach_share": 0.5, "reset_shrink": 0.8,
    "reset_noise": 0.1, "fitness_window": 20,
    "regimes": {"novelty_interval": [2, 6], "lifespan": [5, 20]},
}


def steps_to_target(net: MLP, world: SkillWorld, task, rng, key) -> int:
    ex, ey = world.batch(task, np.random.default_rng(key), EVAL_N)
    for step in range(1, MAX_STEPS + 1):
        net.train_step(*world.batch(task, rng, BATCH))
        if step % CHECK_EVERY == 0 and net.accuracy(ex, ey) >= TARGET:
            return step
    return MAX_STEPS + 1  # did not reach the target


def fresh_steps(seed: int, lr: float) -> int:
    """A fresh network learning a pair of root (two-bit) skills."""
    world = SkillWorld(seed, 1, 1)
    rng = np.random.default_rng([seed, 100])
    a, b = (int(v) for v in rng.choice(N_ROOTS, 2, replace=False))
    net = MLP(np.random.default_rng([seed, 101]), lr=lr)
    return steps_to_target(net, world, (a, b), rng, [seed, 102])


def climb_steps(seed: int, lr: float):
    """One learner with unlimited compute follows the first CLIMB_ERAS eras of
    a stream at the grid's fastest pace, training each era's task to the
    target. Returns the steps each era needed after the first."""
    world = SkillWorld(seed, CLIMB_PACE, CLIMB_ERAS)
    rng = np.random.default_rng([seed, 103])
    net = MLP(np.random.default_rng([seed, 104]), lr=lr)
    return [steps_to_target(net, world, task, rng, [seed, 105, e])
            for e, task in enumerate(world.tasks)][1:]


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
    by_lr = {lr: [fresh_steps(s, lr) for s in CAL_SEEDS] for lr in LRS}
    medians = {lr: float(np.median(v)) for lr, v in by_lr.items()}
    lr = min(LRS, key=lambda v: (medians[v], v))
    climbs = [c for s in CAL_SEEDS for c in climb_steps(s, lr)]
    S = next((s for s in STEP_CHOICES if np.mean([c <= s for c in climbs]) >= 0.9),
             STEP_CHOICES[-1])
    curves = {k: [] for k in PROBE_CHOICES}
    for s in CAL_SEEDS:
        for k, v in novel_curve(s, lr).items():
            curves[k].extend(v)
    novel_means = {k: float(np.mean(v)) for k, v in curves.items()}
    K = min(PROBE_CHOICES, key=lambda k: (abs(novel_means[k] - PROBE_TARGET), k))

    cal = {"seeds": CAL_SEEDS, "target": TARGET,
           "fresh_steps_to_target": {str(k): v for k, v in by_lr.items()},
           "fresh_median_steps": {str(k): v for k, v in medians.items()},
           "climb_steps_to_target": climbs,
           "climb_share_within": {str(s): float(np.mean([c <= s for c in climbs])) for s in STEP_CHOICES},
           "novel_probe_mean_by_K": {str(k): v for k, v in novel_means.items()},
           "chosen": {"lr": lr, "steps_per_era": S, "probe_steps": K}}
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(cal, f, indent=2)
    proto = {**FIXED, "lr": lr, "steps_per_era": S, "probe_steps": K, "frozen": False}
    with open(os.path.join(HERE, "protocol.json"), "w") as f:
        json.dump(proto, f, indent=2)
    print(json.dumps({k: v for k, v in cal.items() if k != "climb_steps_to_target"}, indent=2))


if __name__ == "__main__":
    main()
