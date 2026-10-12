"""The simulation engine.

Deterministic given a seed. All dynamics (growth, collapse, specialization) are
produced by agent behaviour interacting with the world — not read off a single
"capability" dial. The reproductive number R is *measured* from completed
lifetimes, never prescribed.

Hard caps (max population / steps / wall-clock) bound every run; see SAFETY.md.
"""

from __future__ import annotations

import copy
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import __version__
from .agent import ACTIONS, Agent, Genome, Memory, MemoryEntry
from .world import World

PRIOR_VIABILITY = 0.5


@dataclass
class EngineConfig:
    engine: str = "rule-based"          # labels the record; LLM agents would differ
    n_nodes: int = 80
    n_arch: int = 4
    reach: int = 6
    n_founders: int = 8
    max_steps: int = 120
    max_population: int = 600
    max_seconds: float = 20.0
    max_age: int = 22
    mutation_rate: float = 0.25
    mutation_scale: float = 0.08
    inheritance: str = "related"        # "none" | "related" | "unrelated"
    shift_step: Optional[int] = 60
    shift_magnitude: float = 1.0

    def as_dict(self) -> Dict:
        return dict(self.__dict__)


@dataclass
class RunResult:
    config: Dict
    simulator_version: str
    seed: int
    # Headline metrics
    R_lifetime: Optional[float]         # mean offspring among agents that completed life
    R_n: int                            # sample size behind R_lifetime
    extinct: bool
    extinction_step: Optional[int]
    peak_population: int
    final_population: int
    pre_shift_population: Optional[int]
    recovery_ratio: Optional[float]     # final / pre-shift population (survival after change)
    # Trajectories / structure
    population_by_step: List[int] = field(default_factory=list)
    trait_means_by_phase: Dict[str, Dict[str, float]] = field(default_factory=dict)
    action_counts: Dict[str, int] = field(default_factory=dict)
    events: List[Tuple[int, str]] = field(default_factory=list)
    arch_viability_initial: Dict[int, float] = field(default_factory=dict)
    arch_viability_final: Dict[int, float] = field(default_factory=dict)
    capped: bool = False

    def as_dict(self) -> Dict:
        d = dict(self.__dict__)
        d["events"] = [[s, t] for s, t in self.events]
        return d


def _estimate_viability(agent: Agent, arch: int) -> float:
    """What the agent believes about an arch, blending inherited memory with a
    neutral prior according to how much it trusts inherited information."""
    belief = agent.believed_viability(arch)
    if belief is None:
        return PRIOR_VIABILITY
    return agent.genome.memory_trust * belief + (1 - agent.genome.memory_trust) * PRIOR_VIABILITY


def _trait_means(agents: List[Agent]) -> Dict[str, float]:
    living = [a for a in agents if a.alive]
    if not living:
        return {"explore_rate": 0.0, "memory_trust": 0.0, "risk_threshold": 0.0, "n": 0}
    n = len(living)
    return {
        "explore_rate": round(sum(a.genome.explore_rate for a in living) / n, 4),
        "memory_trust": round(sum(a.genome.memory_trust for a in living) / n, 4),
        "risk_threshold": round(sum(a.genome.risk_threshold for a in living) / n, 4),
        "n": n,
    }


class Engine:
    def __init__(self, config: EngineConfig, seed: int):
        self.cfg = config
        self.seed = seed
        self.rng = random.Random(seed)
        self.world = World.generate(self.rng, n_nodes=config.n_nodes, n_arch=config.n_arch)
        self.agents: List[Agent] = []
        self.by_lineage: Dict[int, List[Agent]] = {}
        self._next_aid = 0
        self._completed_offspring: List[int] = []   # offspring counts of dead agents (uncensored R)
        self._action_counts = {a: 0 for a in ACTIONS}
        self._events: List[Tuple[int, str]] = []
        self._seed_founders()

    # ---- setup -----------------------------------------------------------
    def _new_aid(self) -> int:
        self._next_aid += 1
        return self._next_aid - 1

    def _seed_founders(self) -> None:
        free = [n for n in self.world.nodes if n.occupants < n.capacity]
        self.rng.shuffle(free)
        for lineage, node in enumerate(free[: self.cfg.n_founders]):
            aid = self._new_aid()
            agent = Agent(
                aid=aid,
                genome=Genome.random(self.rng),
                memory={},
                node_id=node.nid,
                generation=0,
                parent_id=None,
                lineage_id=lineage,
            )
            node.occupants += 1
            self.agents.append(agent)
            self.by_lineage.setdefault(lineage, []).append(agent)

    # ---- inheritance -----------------------------------------------------
    def _inherit_memory(self, parent: Agent) -> Memory:
        mode = self.cfg.inheritance
        if mode == "none":
            return {}
        if mode == "related":
            return copy.deepcopy(parent.memory)
        if mode == "unrelated":
            donors = [
                a for a in self.agents
                if a.alive and a.lineage_id != parent.lineage_id and a.memory
            ]
            if not donors:
                return {}
            return copy.deepcopy(self.rng.choice(donors).memory)
        raise ValueError(f"unknown inheritance mode: {mode}")

    # ---- actions ---------------------------------------------------------
    def _free_target(self, agent: Agent) -> Optional[int]:
        """Best known reachable node to consider, by the agent's beliefs."""
        candidates = self.world.neighbors(agent.node_id, self.cfg.reach)
        candidates = [n for n in candidates if n.occupants < n.capacity]
        if not candidates:
            return None
        best = max(candidates, key=lambda n: _estimate_viability(agent, n.arch))
        return best.nid

    def _step_agent(self, agent: Agent, step: int) -> None:
        agent.age += 1
        explore = self.rng.random() < agent.genome.explore_rate
        target_id = self._free_target(agent)

        if target_id is None or explore:
            # OBSERVE / learn the environment: TEST a reachable node's current
            # true viability and RECORD it (this is the self-correction channel).
            neigh = self.world.neighbors(agent.node_id, self.cfg.reach)
            if neigh:
                probe = self.rng.choice(neigh)
                true_v = self.world.arch_viability.get(probe.arch, PRIOR_VIABILITY)
                agent.record_observation(probe.arch, true_v)
                agent.actions_taken["TEST"] += 1
                self._action_counts["TEST"] += 1
            else:
                agent.actions_taken["WAIT"] += 1
                self._action_counts["WAIT"] += 1
            return

        target = self.world.nodes[target_id]
        est = _estimate_viability(agent, target.arch)
        if est < agent.genome.risk_threshold:
            # Not confident enough: TEST it to update beliefs, don't spend a replication.
            true_v = self.world.arch_viability.get(target.arch, PRIOR_VIABILITY)
            agent.record_observation(target.arch, true_v)
            agent.actions_taken["TEST"] += 1
            self._action_counts["TEST"] += 1
            return

        # Attempt REPLICATE. Success depends on the node's *current* difficulty,
        # which depends on the (possibly shifted) viability of its arch.
        agent.actions_taken["REPLICATE"] += 1
        self._action_counts["REPLICATE"] += 1
        difficulty = target.difficulty(self.world.arch_viability)
        true_v = self.world.arch_viability.get(target.arch, PRIOR_VIABILITY)
        # A failed attempt still teaches the agent the real viability (RECORD),
        # but confident inherited beliefs are corrected only slowly.
        agent.record_observation(target.arch, true_v)
        if self.rng.random() < (1.0 - difficulty) and target.occupants < target.capacity:
            self._spawn_child(agent, target)

    def _spawn_child(self, parent: Agent, node) -> None:
        aid = self._new_aid()
        child = Agent(
            aid=aid,
            genome=parent.genome.mutate(self.rng, self.cfg.mutation_rate, self.cfg.mutation_scale),
            memory=self._inherit_memory(parent),
            node_id=node.nid,
            generation=parent.generation + 1,
            parent_id=parent.aid,
            lineage_id=parent.lineage_id,
        )
        node.occupants += 1
        self.agents.append(child)
        self.by_lineage.setdefault(parent.lineage_id, []).append(child)
        parent.offspring += 1

    def _reap(self, step: int) -> None:
        """Node failures and old age remove agents, completing their lifetimes."""
        for agent in self.agents:
            if not agent.alive:
                continue
            node = self.world.nodes[agent.node_id]
            died = agent.age >= self.cfg.max_age or self.rng.random() > node.reliability
            if died:
                agent.alive = False
                node.occupants = max(0, node.occupants - 1)
                self._completed_offspring.append(agent.offspring)

    # ---- run -------------------------------------------------------------
    def run(self) -> RunResult:
        start = time.time()
        cfg = self.cfg
        viability_initial = dict(self.world.arch_viability)
        population_by_step: List[int] = []
        trait_phases: Dict[str, Dict[str, float]] = {}
        pre_shift_pop: Optional[int] = None
        extinction_step: Optional[int] = None
        capped = False

        trait_phases["start"] = _trait_means(self.agents)

        for step in range(cfg.max_steps):
            if time.time() - start > cfg.max_seconds:
                capped = True
                self._events.append((step, "run hit wall-clock cap"))
                break

            if cfg.shift_step is not None and step == cfg.shift_step:
                pre_shift_pop = sum(1 for a in self.agents if a.alive)
                trait_phases["pre_shift"] = _trait_means(self.agents)
                self.world.shift_environment(cfg.shift_magnitude)
                self._events.append((step, "environment shift: arch viabilities changed"))

            # Act (snapshot so new births wait until next step).
            for agent in list(self.agents):
                if agent.alive:
                    self._step_agent(agent, step)
                if sum(1 for a in self.agents if a.alive) >= cfg.max_population:
                    capped = True
                    break
            self._reap(step)

            living = sum(1 for a in self.agents if a.alive)
            population_by_step.append(living)
            if living == 0:
                extinction_step = step
                self._events.append((step, "population extinct"))
                break
            if capped:
                self._events.append((step, "run hit population cap"))
                break

        trait_phases["end"] = _trait_means(self.agents)

        final_pop = population_by_step[-1] if population_by_step else 0
        peak_pop = max(population_by_step) if population_by_step else 0
        recovery = None
        if pre_shift_pop:
            recovery = round(final_pop / pre_shift_pop, 4)

        # Uncensored R: mean offspring among agents whose life completed.
        done = self._completed_offspring
        R = round(sum(done) / len(done), 4) if len(done) >= 20 else None

        return RunResult(
            config=cfg.as_dict(),
            simulator_version=__version__,
            seed=self.seed,
            R_lifetime=R,
            R_n=len(done),
            extinct=final_pop == 0,
            extinction_step=extinction_step,
            peak_population=peak_pop,
            final_population=final_pop,
            pre_shift_population=pre_shift_pop,
            recovery_ratio=recovery,
            population_by_step=population_by_step,
            trait_means_by_phase=trait_phases,
            action_counts=dict(self._action_counts),
            events=self._events,
            arch_viability_initial=viability_initial,
            arch_viability_final=dict(self.world.arch_viability),
            capped=capped,
        )


def run_once(config: EngineConfig, seed: int) -> RunResult:
    return Engine(config, seed).run()
