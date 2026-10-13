"""Calibration (PREREGISTRATION.md §7): fix the default learning rate, steps
per era and probe steps by watching *fresh* networks learn single tasks.
No arm is run here, so no comparison between arms can influence the choices.

    python -m learners.calibrate      # writes calibration.json and protocol.json
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from .net import MLP  # noqa: E402
from .world import N_STREAM, SkillWorld  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAL_SEEDS = list(range(1, 21))          # calibration worlds, disjoint from pilot and confirmation
LRS = [3e-4, 1e-3, 3e-3]
STEP_CHOICES = [100, 200, 300, 500, 800]
PROBE_CHOICES = [25, 50, 100, 200]
MAX_STEPS, CHECK_EVERY, TARGET = 3000, 25, 0.90
BATCH, EVAL_N = 32, 2000

FIXED = {  # pre-registered values that calibration does not touch
    "batch": BATCH, "n_eras": 120, "checkpoints": [20, 40, 60, 80, 100, 120],
    "eval_n": EVAL_N, "pop": 4, "teach_share": 0.5, "reset_shrink": 0.8,
    "reset_noise": 0.1, "fitness_window": 20,
    "regimes": {"novelty_interval": [2, 6], "lifespan": [5, 20]},
}


def stream_task(world: SkillWorld, rng):
    while True:
        a, b = (int(v) for v in rng.choice(N_STREAM, 2, replace=False))
        if (a, b) not in world.heldout:
            return a, b


def steps_to_target(seed: int, lr: float) -> int:
    world = SkillWorld(seed, 2, 1)
    rng = np.random.default_rng([seed, 100])
    task = stream_task(world, rng)
    net = MLP(np.random.default_rng([seed, 101]), lr=lr)
    ex, ey = world.batch(task, np.random.default_rng([seed, 102]), EVAL_N)
    for step in range(1, MAX_STEPS + 1):
        x, y = world.batch(task, rng, BATCH)
        net.train_step(x, y)
        if step % CHECK_EVERY == 0 and net.accuracy(ex, ey) >= TARGET:
            return step
    return MAX_STEPS + 1  # did not reach the target


def novel_curve(seed: int, lr: float):
    """Accuracy of fresh networks on NOVEL probe tasks after each candidate K."""
    world = SkillWorld(seed, 2, 120)
    _, novel = world.probes(120)
    accs = {k: [] for k in PROBE_CHOICES}
    for i, task in enumerate(novel):
        net = MLP(np.random.default_rng([seed, 103, i]), lr=lr)
        rng = np.random.default_rng([seed, 104, i])
        ex, ey = world.batch(task, np.random.default_rng([seed, 105, i]), EVAL_N)
        for step in range(1, max(PROBE_CHOICES) + 1):
            x, y = world.batch(task, rng, BATCH)
            net.train_step(x, y)
            if step in accs:
                accs[step].append(net.accuracy(ex, ey))
    return accs


def main() -> None:
    by_lr = {lr: [steps_to_target(s, lr) for s in CAL_SEEDS] for lr in LRS}
    medians = {lr: float(np.median(v)) for lr, v in by_lr.items()}
    lr = min(LRS, key=lambda v: (medians[v], v))
    reached = by_lr[lr]
    S = next((s for s in STEP_CHOICES
              if np.mean([r <= s for r in reached]) >= 0.9), STEP_CHOICES[-1])
    curves = {k: [] for k in PROBE_CHOICES}
    for s in CAL_SEEDS:
        for k, v in novel_curve(s, lr).items():
            curves[k].extend(v)
    novel_means = {k: float(np.mean(v)) for k, v in curves.items()}
    K = min(PROBE_CHOICES, key=lambda k: (abs(novel_means[k] - 0.6), k))

    cal = {"seeds": CAL_SEEDS, "target": TARGET, "steps_to_target": {str(k): v for k, v in by_lr.items()},
           "median_steps": {str(k): v for k, v in medians.items()},
           "chosen": {"lr": lr, "steps_per_era": S, "probe_steps": K},
           "share_within_S": float(np.mean([r <= S for r in reached])),
           "novel_probe_mean_by_K": {str(k): v for k, v in novel_means.items()}}
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(cal, f, indent=2)
    proto = {**FIXED, "lr": lr, "steps_per_era": S, "probe_steps": K, "frozen": False}
    with open(os.path.join(HERE, "protocol.json"), "w") as f:
        json.dump(proto, f, indent=2)
    print(json.dumps(cal, indent=2))


if __name__ == "__main__":
    main()
