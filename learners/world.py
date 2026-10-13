"""The skill world: a never-ending stream of learning problems.

Inputs are 32 random ±1 bits. A *skill* is the XOR (product) of a fixed pair
of input bits, so detecting it needs a hidden unit and a learned skill is
reusable knowledge. A *task* is an ordered pair of distinct skills (a, b) with
label 2·[a] + [b] (4 classes). The stream introduces new skills over time and
recombines old ones; some skill pairs are held out of the stream for probing
reuse, and some skills are reserved (never streamed) for probing plasticity.

One seed fixes the whole world, so every arm sees the same task sequence.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

N_BITS = 32
N_STREAM = 64        # skills that appear in the stream (see PREREGISTRATION deviations)
N_RESERVED = 8       # skills never streamed: material for the NOVEL probe
N_INITIAL = 4        # skills available from era 0
HOLDOUT_FRAC = 0.2   # share of ordered stream pairs kept out of the stream
N_PROBE = 6          # probe tasks of each kind per checkpoint

Task = Tuple[int, int]


class SkillWorld:
    def __init__(self, seed: int, novelty_interval: int, n_eras: int):
        self.seed, self.novelty_interval, self.n_eras = seed, novelty_interval, n_eras
        rng = np.random.default_rng([seed, 0])
        pairs = [(i, j) for i in range(N_BITS) for j in range(i + 1, N_BITS)]
        pick = rng.choice(len(pairs), N_STREAM + N_RESERVED, replace=False)
        self.skill_bits = np.array([pairs[k] for k in pick])
        self.reserved = list(range(N_STREAM, N_STREAM + N_RESERVED))
        ordered = [(a, b) for a in range(N_STREAM) for b in range(N_STREAM) if a != b]
        held = rng.choice(len(ordered), int(HOLDOUT_FRAC * len(ordered)), replace=False)
        self.heldout = {ordered[k] for k in held}
        self.tasks = self._stream(np.random.default_rng([seed, 1, novelty_interval]))

    def n_introduced(self, era: int) -> int:
        return min(N_STREAM, N_INITIAL + era // self.novelty_interval)

    def _stream(self, rng: np.random.Generator) -> List[Task]:
        tasks = []
        for era in range(self.n_eras):
            n = self.n_introduced(era)
            task = None
            if rng.random() < 0.5:
                newest = n - 1
                for _ in range(20):
                    other = int(rng.integers(0, newest))
                    cand = (newest, other) if rng.random() < 0.5 else (other, newest)
                    if cand not in self.heldout:
                        task = cand
                        break
            while task is None:
                a, b = (int(v) for v in rng.choice(n, 2, replace=False))
                if (a, b) not in self.heldout:
                    task = (a, b)
            tasks.append(task)
        return tasks

    def probes(self, checkpoint: int) -> Tuple[List[Task], List[Task]]:
        """REUSE and NOVEL probe tasks after `checkpoint` eras of training.
        They depend only on the seed and checkpoint, never on the arm."""
        n = self.n_introduced(checkpoint - 1)
        known = sorted(p for p in self.heldout if p[0] < n and p[1] < n)
        rng = np.random.default_rng([self.seed, 2, checkpoint])
        k = min(N_PROBE, len(known))
        reuse = [known[i] for i in rng.choice(len(known), k, replace=False)]
        novel_all = [(a, b) for a in self.reserved for b in self.reserved if a != b]
        novel = [novel_all[i] for i in rng.choice(len(novel_all), N_PROBE, replace=False)]
        return reuse, novel

    def batch(self, task: Task, rng: np.random.Generator, n: int):
        x = rng.integers(0, 2, size=(n, N_BITS)).astype(np.float64) * 2.0 - 1.0
        a, b = self.skill_bits[task[0]], self.skill_bits[task[1]]
        sa = x[:, a[0]] * x[:, a[1]] > 0
        sb = x[:, b[0]] * x[:, b[1]] > 0
        return x, (2 * sa + sb).astype(np.int64)


def random_inputs(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.integers(0, 2, size=(n, N_BITS)).astype(np.float64) * 2.0 - 1.0
