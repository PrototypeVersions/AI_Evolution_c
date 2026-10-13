"""The arms of Study 1b (PREREGISTRATION_1b.md §3): what keeps a weight-copying
population able to learn?

Each arm differs from its neighbour in one way: fewer updates per network
(QUARTER), the best of four networks (SOLO4), varied starting settings
(SOLO4P), copying the best into the worst (COPY4, COPY4P), and learning-rate
mutation (CLONE). IMMORTAL and CLONE run Study 1's algorithms unchanged.

Pairing. Three random streams replace Study 1's single one per run:

- founders come from a stream shared by every arm with the same starting
  settings, so SOLO4P, COPY4P and CLONE start from identical networks, and
  IMMORTAL, QUARTER and the first member of SOLO4 and COPY4 start from the
  same network;
- training batches come from a stream keyed by (era, member slot) and shared
  by every arm, so QUARTER's 200 batches in an era are the first 200 of
  IMMORTAL's 800, and arms that differ only by copying train on identical
  batches until their first birth;
- anything an arm does at a birth (CLONE's mutation) draws from the arm's own
  stream, so it cannot shift the other two.
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from .arms import FWD, Arm, Clone, _Population

ARM_ORDER_1B = ["IMMORTAL", "QUARTER", "SOLO4", "COPY4", "SOLO4P", "COPY4P", "CLONE"]
# Arms that never reproduce: one run per world serves every lifespan.
NO_BIRTHS = ("IMMORTAL", "QUARTER", "SOLO4", "SOLO4P")
# Arms with the same starting settings share their founders.
FOUNDERS = {"IMMORTAL": 0, "QUARTER": 0, "SOLO4": 0, "COPY4": 0,
            "SOLO4P": 1, "COPY4P": 1, "CLONE": 1}


class _Paired(Arm):
    share = 1.0  # the part of the per-era budget the arm may spend

    def __init__(self, proto: Dict, founders: np.random.Generator,
                 own: np.random.Generator, data_key: Tuple, lifespan: int):
        super().__init__(proto, founders, lifespan)  # members are drawn from the shared stream
        self.rng, self.data_key = own, tuple(data_key)

    def era(self, world, era: int) -> None:
        start = self.macs
        if era > 0 and era % self.lifespan == 0:
            self.lifecycle(world, era)
        step_cost = self.batch * 3 * FWD
        steps = (int(self.budget * self.share) - (self.macs - start)) // step_cost // self.pop
        task = world.tasks[era]
        for slot, m in enumerate(self.members):
            data = np.random.default_rng(self.data_key + (era, slot))
            for _ in range(int(steps)):
                x, y = world.batch(task, data, self.batch)
                m.recent.append(m.net.train_step(x, y))
            self.macs += int(steps) * step_cost
        assert self.macs - start <= self.budget

    def _copy_best(self, era: int) -> None:
        """CLONE's copying without the mutation: the worst half are replaced by
        copies (weights and optimiser state) of the best half."""
        ranked = self._ranked()
        half = self.pop // 2
        survivors = ranked[:half]
        children = [self._member(survivors[i % half].net.copy(with_optimizer=True), era,
                                 survivors[i % half].id, "copy")
                    for i in range(self.pop - half)]
        self.members = survivors + children


class Immortal(_Paired):
    name = "IMMORTAL"


class Quarter(_Paired):
    """A control, not a strategy: one network that trains a quarter as much as
    IMMORTAL and leaves the rest of the budget unspent."""
    name = "QUARTER"
    share = 0.25


class Solo4(_Paired):
    """Four default networks that never interact; the fittest is measured."""
    name = "SOLO4"
    pop = 4


class Copy4(Solo4):
    name = "COPY4"

    def lifecycle(self, world, era):
        self._copy_best(era)


class Solo4P(_Paired, _Population):
    """Four networks with settings drawn from CLONE's prior; never interact."""
    name = "SOLO4P"


class Copy4P(Solo4P):
    name = "COPY4P"

    def lifecycle(self, world, era):
        self._copy_best(era)


class Clone1b(_Paired, Clone):
    """Study 1's CLONE (copying plus learning-rate mutation), on paired streams."""
    name = "CLONE"


ARMS_1B = {cls.name: cls for cls in (Immortal, Quarter, Solo4, Copy4, Solo4P, Copy4P, Clone1b)}


def make(arm: str, seed: int, R: int, L: int, proto: Dict) -> Arm:
    founders = np.random.default_rng([seed, 11, R, FOUNDERS[arm]])
    own = np.random.default_rng([seed, 13, R, L, ARM_ORDER_1B.index(arm)])
    return ARMS_1B[arm](proto, founders, own, (seed, 12, R), L if L else 10 ** 9)
