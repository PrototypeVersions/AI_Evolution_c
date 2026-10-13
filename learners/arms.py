"""The seven life histories compared in Study 1 (PREREGISTRATION.md §4).

Every arm gets the same training compute per era, counted in multiply-
accumulates (MACs). A training example costs 3x the forward MACs and a
forward-only example (a teacher's pass) costs 1x. Each arm records every
birth so the lineage can be drawn later.
"""

from __future__ import annotations

import collections
import math
from typing import Dict, List, Optional

import numpy as np

from .net import MLP, forward_macs
from .world import SkillWorld, random_inputs

FWD = forward_macs()


class Member:
    __slots__ = ("id", "net", "recent", "born")

    def __init__(self, uid: int, net: MLP, born: int, window: int):
        self.id, self.net, self.born = uid, net, born
        self.recent = collections.deque(maxlen=window)

    @property
    def fitness(self) -> float:
        return float(np.mean(self.recent)) if self.recent else 0.0

    def genome(self) -> Dict[str, float]:
        return {"lr": self.net.lr, "wd": self.net.wd, "init_scale": self.net.init_scale}


class Arm:
    name = ""
    pop = 1

    def __init__(self, proto: Dict, rng: np.random.Generator, lifespan: int):
        self.p, self.rng, self.lifespan = proto, rng, lifespan
        self.batch = proto["batch"]
        self.budget = proto["steps_per_era"] * self.batch * 3 * FWD
        self.macs = 0
        self.next_id = 0
        self.lineage: List[Dict] = []
        self.members: List[Member] = [self._initial() for _ in range(self.pop)]

    # ---- helpers -------------------------------------------------------
    def _member(self, net: MLP, era: int, parent: Optional[int], kind: str) -> Member:
        m = Member(self.next_id, net, era, self.p["fitness_window"])
        self.lineage.append({"id": m.id, "parent": parent, "era": era, "kind": kind,
                             **{k: round(v, 8) for k, v in m.genome().items()}})
        self.next_id += 1
        return m

    def _default_net(self) -> MLP:
        return MLP(self.rng, lr=self.p["lr"])

    def _initial(self) -> Member:
        return self._member(self._default_net(), 0, None, "founder")

    def _prior(self) -> Dict[str, float]:
        lr = self.p["lr"] * math.exp(self.rng.uniform(-math.log(3), math.log(3)))
        wd = math.exp(self.rng.uniform(math.log(1e-6), math.log(1e-3)))
        return {"lr": lr, "wd": wd, "init_scale": float(self.rng.uniform(0.5, 2.0))}

    def _mutate(self, g: Dict[str, float]) -> Dict[str, float]:
        step = lambda: 0.8 if self.rng.random() < 0.5 else 1.25
        lr = float(np.clip(g["lr"] * step(), 1e-5, 1e-1))
        wd = float(np.clip(g["wd"] * step(), 1e-8, 1e-2))
        init = float(np.clip(g["init_scale"] + (0.1 if self.rng.random() < 0.5 else -0.1), 0.25, 3.0))
        return {"lr": lr, "wd": wd, "init_scale": init}

    def _net_from(self, g: Dict[str, float]) -> MLP:
        return MLP(self.rng, lr=g["lr"], wd=g["wd"], init_scale=g["init_scale"])

    def _ranked(self) -> List[Member]:
        return sorted(self.members, key=lambda m: (-m.fitness, m.id))

    # ---- one era -------------------------------------------------------
    def era(self, world: SkillWorld, era: int) -> None:
        start = self.macs
        if era > 0 and era % self.lifespan == 0:
            self.lifecycle(world, era)
        step_cost = self.batch * 3 * FWD
        steps = (self.budget - (self.macs - start)) // step_cost // self.pop
        task = world.tasks[era]
        for m in self.members:
            for _ in range(int(steps)):
                x, y = world.batch(task, self.rng, self.batch)
                m.recent.append(m.net.train_step(x, y))
            self.macs += int(steps) * step_cost
        assert self.macs - start <= self.budget

    def lifecycle(self, world: SkillWorld, era: int) -> None:
        """What happens at a birth era (every `lifespan` eras)."""

    def representative(self) -> Member:
        return self._ranked()[0]


class Immortal(Arm):
    name = "IMMORTAL"


class Reset(Arm):
    """Shrink-and-perturb (Ash & Adams 2020): the network lives on, partly
    scrambled; its optimiser state is reset."""
    name = "RESET"

    def lifecycle(self, world, era):
        net = self.members[0].net
        net.shrink_perturb(self.rng, self.p["reset_shrink"], self.p["reset_noise"])
        net.reset_optimizer()
        self.lineage.append({"id": self.members[0].id, "parent": self.members[0].id,
                             "era": era, "kind": "reset"})


class Restart(Arm):
    name = "RESTART"

    def lifecycle(self, world, era):
        parent = self.members[0]
        self.members = [self._member(self._default_net(), era, parent.id, "fresh")]


class Teach(Arm):
    """A fresh child learns to reproduce its parent's last-hidden-layer
    features and outputs on random inputs, using half of the birth era's
    budget. Weights are never copied."""
    name = "TEACH"

    def lifecycle(self, world, era):
        parent = self.members[0]
        child = self._default_net()
        teach_cost = self.batch * 4 * FWD  # teacher forward + student train
        steps = int(self.budget * self.p["teach_share"]) // teach_cost
        for _ in range(steps):
            child.teach_step(parent.net, random_inputs(self.rng, self.batch))
        self.macs += steps * teach_cost
        self.members = [self._member(child, era, parent.id, "taught")]


class _Childhood(Arm):
    """Secondary arms (PREREGISTRATION_v2 deviation 3): a longer childhood.

    Every `lifespan` eras a fresh child is born. For the next `childhood`
    eras the parent keeps living and training on the stream with half of each
    era's budget (it stays the representative), while the other half teaches
    the child exactly as TEACH does. When the childhood ends, the parent
    retires and the child takes over. No weights are copied."""
    childhood = 4

    def __init__(self, proto, rng, lifespan):
        super().__init__(proto, rng, lifespan)
        self.child: Optional[Member] = None
        self.graduates = None

    def era(self, world: SkillWorld, era: int) -> None:
        start = self.macs
        if self.child is not None and era == self.graduates:
            self.members, self.child = [self.child], None  # the parent retires
        if era > 0 and era % self.lifespan == 0 and self.child is None:
            self.child = self._member(self._default_net(), era, self.members[0].id, "taught")
            self.graduates = era + self.childhood
        parent = self.members[0]
        if self.child is not None:
            teach_cost = self.batch * 4 * FWD
            steps = int(self.budget * self.p["teach_share"]) // teach_cost
            for _ in range(steps):
                self.child.net.teach_step(parent.net, random_inputs(self.rng, self.batch))
            self.macs += steps * teach_cost
        step_cost = self.batch * 3 * FWD
        steps = (self.budget - (self.macs - start)) // step_cost
        task = world.tasks[era]
        for _ in range(int(steps)):
            x, y = world.batch(task, self.rng, self.batch)
            parent.recent.append(parent.net.train_step(x, y))
        self.macs += int(steps) * step_cost
        assert self.macs - start <= self.budget


class Teach4(_Childhood):
    name = "TEACH4"
    childhood = 4


class Teach16(_Childhood):
    name = "TEACH16"
    childhood = 16


class _Population(Arm):
    pop = 4

    def _initial(self) -> Member:
        return self._member(self._net_from(self._prior()), 0, None, "founder")


class Clone(_Population):
    """Population-based training: the bottom half are overwritten with copies
    of the top half (weights and optimiser state), learning rate mutated."""
    name = "CLONE"

    def lifecycle(self, world, era):
        ranked = self._ranked()
        half = self.pop // 2
        survivors = ranked[:half]
        children = []
        for i, loser in enumerate(ranked[half:]):
            parent = survivors[i % half]
            net = parent.net.copy(with_optimizer=True)
            net.lr = float(np.clip(net.lr * (0.8 if self.rng.random() < 0.5 else 1.25), 1e-5, 1e-1))
            children.append(self._member(net, era, parent.id, "clone"))
        self.members = survivors + children


class Genes(_Population):
    """Darwinian: every member is replaced by a fresh network whose learning
    settings are inherited, with mutation, from the top half."""
    name = "GENES"

    def lifecycle(self, world, era):
        ranked = self._ranked()
        half = self.pop // 2
        self.members = [self._member(self._net_from(self._mutate(ranked[i % half].genome())),
                                     era, ranked[i % half].id, "genes")
                        for i in range(self.pop)]


class Random(_Population):
    """Random search: every member is replaced by a fresh network with freshly
    drawn learning settings; nothing is inherited."""
    name = "RANDOM"

    def lifecycle(self, world, era):
        self.members = [self._member(self._net_from(self._prior()), era, None, "random")
                        for _ in range(self.pop)]


ARMS = {cls.name: cls for cls in (Immortal, Reset, Restart, Teach, Clone, Genes, Random, Teach4, Teach16)}
SECONDARY = ("TEACH4", "TEACH16")
