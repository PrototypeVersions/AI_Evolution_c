"""Agents: a heritable genome plus inherited memory.

The genome gives heritable *variation* (it mutates on replication). Memory is
inherited information (notes about arch viability) that does not change the
genome — modelling the distinction between passing notes to a descendant and
changing what the descendant intrinsically is.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# Abstract action vocabulary. Each acts only on in-memory simulator state.
ACTIONS = ("OBSERVE", "MOVE", "TEST", "REPLICATE", "RECORD", "WAIT")


@dataclass
class Genome:
    """Heritable decision parameters, all in [0,1]."""

    explore_rate: float      # tendency to MOVE/OBSERVE vs. exploit known nodes
    memory_trust: float      # how strongly inherited memory steers choices
    risk_threshold: float    # min believed viability before attempting REPLICATE

    def mutate(self, rng: random.Random, rate: float, scale: float) -> "Genome":
        def jitter(x: float) -> float:
            if rng.random() < rate:
                x += rng.gauss(0.0, scale)
            return min(1.0, max(0.0, x))

        return Genome(
            explore_rate=jitter(self.explore_rate),
            memory_trust=jitter(self.memory_trust),
            risk_threshold=jitter(self.risk_threshold),
        )

    @classmethod
    def random(cls, rng: random.Random) -> "Genome":
        return cls(
            explore_rate=round(rng.uniform(0.2, 0.8), 3),
            memory_trust=round(rng.uniform(0.2, 0.8), 3),
            risk_threshold=round(rng.uniform(0.2, 0.6), 3),
        )


@dataclass
class MemoryEntry:
    """An inherited observation about an arch: believed viability + sample weight."""

    believed_viability: float
    weight: float  # how many observations back this (confidence proxy)


Memory = Dict[int, MemoryEntry]  # keyed by arch


@dataclass
class Agent:
    aid: int
    genome: Genome
    memory: Memory
    node_id: int
    generation: int
    parent_id: Optional[int]
    lineage_id: int
    alive: bool = True
    age: int = 0
    offspring: int = 0           # successful descendants produced (for R)
    actions_taken: Dict[str, int] = field(default_factory=lambda: {a: 0 for a in ACTIONS})

    def believed_viability(self, arch: int) -> Optional[float]:
        e = self.memory.get(arch)
        return e.believed_viability if e else None

    def record_observation(self, arch: int, observed_viability: float) -> None:
        """Fold a fresh observation into memory (RECORD action)."""
        e = self.memory.get(arch)
        if e is None:
            self.memory[arch] = MemoryEntry(believed_viability=observed_viability, weight=1.0)
        else:
            # Weighted update that lets new evidence correct stale beliefs,
            # but more slowly when the agent has high inherited confidence.
            total = e.weight + 1.0
            e.believed_viability = (e.believed_viability * e.weight + observed_viability) / total
            e.weight = min(e.weight + 1.0, 12.0)
