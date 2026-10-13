"""The staircase world: a never-ending stream of skills that build on each other.

Inputs are 32 random ±1 bits. A *skill* is the parity (product) of a set of
input bits. The world starts with a few two-bit skills; every R eras a new
skill appears that extends an existing skill by one more bit. Learning a
high-order parity from scratch is very hard for gradient descent, but learning
it one bit at a time is easy (the "staircase" property: Abbe, Boix-Adsera and
Misiakiewicz, 2022). So in this world knowledge compounds: a learner that keeps
what it knew can climb, and one that starts over cannot.

Each era presents one task: an ordered pair of skills (a, b) with label
2·[a] + [b] (4 classes). A new skill is always part of the task in the era it
arrives, and afterwards the newest skill is included with probability 1/2. Reserved two-bit skills never appear in the stream;
they probe plasticity. Skills the stream has not introduced yet probe the
ability to take the next step.

One seed fixes the whole world, so every arm sees the same task sequence.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

N_BITS = 32
N_ROOTS = 4          # two-bit skills available from era 0
MAX_DEGREE = 16      # a skill never covers more than half the input bits
N_RESERVED = 8       # two-bit skills never streamed: NOVEL probe material
N_PROBE = 6          # probe tasks of each kind per checkpoint
P_EXTEND_NEWEST = 0.5
P_TASK_NEWEST = 0.5

Task = Tuple[int, int]


class SkillWorld:
    def __init__(self, seed: int, novelty_interval: int, n_eras: int):
        self.seed, self.novelty_interval, self.n_eras = seed, novelty_interval, n_eras
        rng = np.random.default_rng([seed, 0, novelty_interval])
        n_skills = N_ROOTS + n_eras // novelty_interval + 4 * N_PROBE
        self.supports: List[Tuple[int, ...]] = []
        self.parents: List[int] = []
        used = set()
        while len(self.supports) < N_ROOTS:
            s = tuple(sorted(int(v) for v in rng.choice(N_BITS, 2, replace=False)))
            if s not in used:
                used.add(s)
                self.supports.append(s)
                self.parents.append(-1)
        while len(self.supports) < n_skills:
            k = len(self.supports)
            parent = k - 1 if rng.random() < P_EXTEND_NEWEST else int(rng.integers(0, k))
            if len(self.supports[parent]) >= MAX_DEGREE:
                continue
            free = [b for b in range(N_BITS) if b not in self.supports[parent]]
            s = tuple(sorted(self.supports[parent] + (int(rng.choice(free)),)))
            if s in used:
                continue
            used.add(s)
            self.supports.append(s)
            self.parents.append(parent)
        reserved = []
        while len(reserved) < N_RESERVED:
            s = tuple(sorted(int(v) for v in rng.choice(N_BITS, 2, replace=False)))
            if s not in used:
                used.add(s)
                reserved.append(s)
        self.reserved = list(range(len(self.supports), len(self.supports) + N_RESERVED))
        self.supports.extend(reserved)
        self.parents.extend([-1] * N_RESERVED)
        self.degrees = [len(s) for s in self.supports]
        self._index = [np.array(s) for s in self.supports]
        self.tasks = self._stream(np.random.default_rng([seed, 1, novelty_interval]))

    def n_introduced(self, era: int) -> int:
        return N_ROOTS + era // self.novelty_interval

    def _stream(self, rng: np.random.Generator) -> List[Task]:
        tasks = []
        for era in range(self.n_eras):
            n = self.n_introduced(era)
            arrived = era > 0 and n > self.n_introduced(era - 1)
            # a new skill is always presented in the era it arrives
            newest = arrived or rng.random() < P_TASK_NEWEST
            a = n - 1 if newest else int(rng.integers(0, n))
            b = int(rng.integers(0, n - 1))
            b = b + 1 if b >= a else b
            tasks.append((a, b) if rng.random() < 0.5 else (b, a))
        return tasks

    def probes(self, checkpoint: int) -> Dict[str, List[int]]:
        """Skills probed after `checkpoint` eras of training; they depend only
        on the seed and checkpoint, never on the arm.

        novel:    reserved two-bit skills the stream never shows (plasticity).
        frontier: the next skills the stream will introduce whose parent is
                  already introduced (the ability to take the next step)."""
        n = self.n_introduced(checkpoint - 1)
        rng = np.random.default_rng([self.seed, 2, checkpoint])
        novel = [int(v) for v in rng.choice(self.reserved, N_PROBE, replace=False)]
        frontier = [k for k in range(n, len(self.supports) - N_RESERVED)
                    if self.parents[k] < n][:N_PROBE]
        return {"novel": novel, "frontier": frontier}

    def signs(self, x: np.ndarray, skills) -> np.ndarray:
        """(n, len(skills)) array of each skill's parity sign (+1/-1)."""
        return np.stack([np.prod(x[:, self._index[k]], axis=1) for k in skills], axis=1)

    def batch(self, task: Task, rng: np.random.Generator, n: int):
        x = random_inputs(rng, n)
        s = self.signs(x, task) > 0
        return x, (2 * s[:, 0] + s[:, 1]).astype(np.int64)

    def skill_batch(self, skill: int, rng: np.random.Generator, n: int):
        """A single-skill task (labels 0/1), used by the probes."""
        x = random_inputs(rng, n)
        return x, (self.signs(x, [skill])[:, 0] > 0).astype(np.int64)

    def describe(self) -> Dict:
        return {"supports": [list(s) for s in self.supports], "parents": self.parents,
                "degrees": self.degrees, "reserved": self.reserved}


def random_inputs(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.integers(0, 2, size=(n, N_BITS)).astype(np.float64) * 2.0 - 1.0
