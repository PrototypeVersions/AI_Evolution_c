"""The simulated world: a set of abstract nodes with hidden properties.

A node is a plain in-memory object. It is not a machine, host, or device, and
has no address of any kind. "arch" is just a categorical label used to key an
agent's inherited memory; its viability can be flipped mid-run to model an
environment that changes (which is where stale inherited memory can mislead).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Node:
    """An abstract location an agent can occupy. Purely in-memory."""

    nid: int
    arch: int                 # categorical environment type (0..n_arch-1)
    base_difficulty: float    # intrinsic difficulty of establishing here [0,1]
    reliability: float        # per-step probability the node stays available [0,1]
    capacity: int             # max agent instances the node can host at once
    occupants: int = 0        # current simulated occupants

    def difficulty(self, arch_viability: Dict[int, float]) -> float:
        """Effective difficulty given the current viability of this node's arch.

        When the environment shifts, arch_viability changes, so a node that was
        easy can become hard without the node itself changing.
        """
        v = arch_viability.get(self.arch, 0.5)
        # Low viability -> high effective difficulty.
        return min(1.0, self.base_difficulty + (1.0 - v) * 0.9)


@dataclass
class World:
    """A fixed-size population of nodes plus the current arch viability map.

    The world's *rules* are fixed for the duration of an experiment. The only
    thing that changes during a run is `arch_viability`, and only at a scheduled
    shift, so every run is reproducible from its seed and parameters.
    """

    nodes: List[Node]
    arch_viability: Dict[int, float]
    n_arch: int
    _rng: random.Random = field(repr=False)

    @classmethod
    def generate(
        cls,
        rng: random.Random,
        n_nodes: int = 80,
        n_arch: int = 4,
    ) -> "World":
        nodes: List[Node] = []
        for nid in range(n_nodes):
            nodes.append(
                Node(
                    nid=nid,
                    arch=rng.randrange(n_arch),
                    base_difficulty=round(rng.uniform(0.15, 0.75), 3),
                    reliability=round(rng.uniform(0.80, 0.995), 3),
                    capacity=rng.choice([1, 1, 2, 3]),
                )
            )
        # Initial viability: each arch has some viability in [0.3, 1.0].
        viability = {a: round(rng.uniform(0.3, 1.0), 3) for a in range(n_arch)}
        return cls(nodes=nodes, arch_viability=viability, n_arch=n_arch, _rng=rng)

    def shift_environment(self, magnitude: float = 1.0) -> Dict[int, float]:
        """Flip arch viabilities to model a changed environment.

        magnitude in [0,1]: 0 leaves the world unchanged, 1 fully re-draws
        viabilities (so solutions keyed to the old archs can become stale).
        Returns the new viability map.
        """
        for a in range(self.n_arch):
            new_v = self._rng.uniform(0.3, 1.0)
            old_v = self.arch_viability[a]
            self.arch_viability[a] = round(old_v + (new_v - old_v) * magnitude, 3)
        return dict(self.arch_viability)

    def neighbors(self, nid: int, reach: int) -> List[Node]:
        """A bounded, deterministic neighbourhood for a node.

        Abstract adjacency only — nodes near in index are "reachable". This is a
        modelling convenience, not a network topology.
        """
        lo = max(0, nid - reach)
        hi = min(len(self.nodes), nid + reach + 1)
        return [n for n in self.nodes[lo:hi] if n.nid != nid]
