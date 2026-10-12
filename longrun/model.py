"""Multi-habitat world with evolvable rule-based agents.

What can evolve: each agent's *behaviour program*, a short ordered list of
condition -> action rules plus a default action and a memory-trust trait. Rules
are added, deleted and altered by mutation when an agent replicates, so the
space of behaviours is open-ended within the fixed action vocabulary, rather
than a few numbers on a slider. Inherited memory (beliefs about which node
types are viable) is passed to children separately from the program, and
habitats keep a shared "commons" memory that agents may write to and read from.

What drives selection: energy. Agents must forage on limited, regrowing node
resources; replication and movement cost energy; agents that run out die. Node
types (arch) differ in viability per habitat, so knowledge that is right in one
habitat can be wrong in another, and shocks can make it wrong at home too.

Everything here is in-memory state. MIGRATE moves a record between habitats in
this object; it does not touch anything outside the simulator.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

ACTIONS = ("CONSUME", "REST", "REPLICATE", "TEST", "READ", "SHARE", "MIGRATE", "MOVE", "STEAL")
FAMILY_OF = {
    "CONSUME": "Foraging", "REST": "Foraging",
    "REPLICATE": "Reproducing",
    "TEST": "Learning", "READ": "Learning", "SHARE": "Learning",
    "MIGRATE": "Moving", "MOVE": "Moving",
    "STEAL": "Competing",
}
FAMILIES = ("Foraging", "Reproducing", "Learning", "Moving", "Competing")
FEATURES = ("energy", "crowding", "belief", "resource", "age", "company")
MAX_RULES = 6
PRIOR = 0.5
A = {name: i for i, name in enumerate(ACTIONS)}

# Rule = [feature_idx, op (0 '<', 1 '>'), threshold, action_idx]
Rule = List


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


# ---------------------------------------------------------------- genome ---
def random_rule(rng: random.Random) -> Rule:
    return [rng.randrange(len(FEATURES)), rng.randrange(2), round(rng.random(), 3), rng.randrange(len(ACTIONS))]


def founder_program(rng: random.Random) -> Tuple[List[Rule], int, float]:
    """A minimal viable program (forage; replicate when well fed) plus random
    extra rules, so founders start alive but varied."""
    rules = [[FEATURES.index("energy"), 1, 0.6, A["REPLICATE"]]]
    for _ in range(rng.randrange(3)):
        rules.append(random_rule(rng))
    return rules, A["CONSUME"], round(rng.uniform(0.2, 0.8), 3)


def mutate(rng: random.Random, rules: List[Rule], default: int, trust: float):
    rules = [list(r) for r in rules]
    for r in rules:
        if rng.random() < 0.10:
            r[2] = round(clamp(r[2] + rng.gauss(0, 0.1)), 3)
        if rng.random() < 0.05:
            r[3] = rng.randrange(len(ACTIONS))
        if rng.random() < 0.05:
            r[0] = rng.randrange(len(FEATURES))
        if rng.random() < 0.05:
            r[1] = 1 - r[1]
    if len(rules) < MAX_RULES and rng.random() < 0.08:
        rules.insert(rng.randrange(len(rules) + 1), random_rule(rng))
    if rules and rng.random() < 0.06:
        rules.pop(rng.randrange(len(rules)))
    if rng.random() < 0.04:
        default = rng.randrange(len(ACTIONS))
    if rng.random() < 0.20:
        trust = round(clamp(trust + rng.gauss(0, 0.06)), 3)
    return rules, default, trust


def describe_program(rules: List[Rule], default: int) -> str:
    """Human-readable program, e.g. 'if energy>0.60: REPLICATE; else CONSUME'."""
    parts = [f"if {FEATURES[f]}{'<>'[op]}{t:.2f}: {ACTIONS[a]}" for f, op, t, a in rules]
    parts.append(f"else {ACTIONS[default]}")
    return "; ".join(parts)


def program_shape(rules: List[Rule], default: int) -> str:
    """The program with thresholds blanked out: its *strategy shape*.

    Programs that differ only in tuning share a shape; a new shape means the
    structure of behaviour changed (a rule gained, lost, or rewired)."""
    rules = list(rules)
    # Trailing rules whose action equals the default can never change behaviour:
    # if they match, they do what the default would have done anyway.
    while rules and rules[-1][3] == default:
        rules.pop()
    parts = [f"if {FEATURES[f]}{'<>'[op]}·: {ACTIONS[a]}" for f, op, t, a in rules]
    parts.append(f"else {ACTIONS[default]}")
    return "; ".join(parts)


# ----------------------------------------------------------------- world ---
class Agent:
    __slots__ = ("id", "lineage", "gen", "parent", "hab", "node", "energy", "age",
                 "rules", "default", "trust", "memory", "counts", "born")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw[k])

    def to_list(self) -> list:
        return [getattr(self, k) for k in self.__slots__]

    @classmethod
    def from_list(cls, row: list) -> "Agent":
        kw = dict(zip(cls.__slots__, row))
        kw["memory"] = {int(k): v for k, v in kw["memory"].items()}
        return cls(**kw)


class World:
    """The whole persistent world. Serialisable to plain JSON via to_state()."""

    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self.rng = random.Random(cfg["seed"])
        self.tick = 0
        self.epoch = 1
        self.next_id = 0
        self.next_lineage = 0
        self.agents: List[Agent] = []
        self.lineages: Dict[int, Dict] = {}     # alive lineages only
        self.extinct_lineages = 0
        self.births = 0
        self.deaths = 0
        self.migrations = 0
        self.habitats: List[Dict] = []
        n_arch = cfg["n_arch"]
        for h in cfg["habitats"]:
            nodes = []
            for _ in range(h["n_nodes"]):
                nodes.append([
                    self.rng.randrange(n_arch),                       # arch
                    round(self.rng.uniform(0.1, 0.5), 3),             # base difficulty
                    self.rng.choice([1, 2, 2, 3]),                    # capacity
                    round(self.rng.uniform(0.3, 1.0), 3),             # resource
                    0,                                                # occupants
                ])
            self.habitats.append({
                "nodes": nodes,
                "via": [round(self.rng.uniform(0.2, 1.0), 3) for _ in range(n_arch)],
                "commons": {},
            })
        self.links: Dict[int, List[int]] = {i: [] for i in range(len(cfg["habitats"]))}
        for a, b in cfg["links"]:
            self.links[a].append(b)
            self.links[b].append(a)
        # Per-tick tallies, read and reset by the observer.
        self.window = self._empty_window()
        self.tick_events: List[Tuple[str, Dict]] = []
        self._seed_founders()

    # ------------------------------------------------------------ helpers --
    def _empty_window(self):
        return {"actions": [[0] * len(ACTIONS) for _ in self.habitats],
                "births": [0] * len(self.habitats), "deaths": [0] * len(self.habitats),
                "arrivals": [0] * len(self.habitats), "steals": [0] * len(self.habitats)}

    def _free_nodes(self, h: int) -> List[int]:
        return [i for i, n in enumerate(self.habitats[h]["nodes"]) if n[4] < n[2]]

    def _estimate(self, ag: Agent, arch: int) -> float:
        m = ag.memory.get(arch)
        if m is None:
            return PRIOR
        return ag.trust * m[0] + (1 - ag.trust) * PRIOR

    def _choose_node(self, ag: Agent, h: int) -> Optional[int]:
        free = self._free_nodes(h)
        if not free:
            return None
        sample = free if len(free) <= 5 else self.rng.sample(free, 5)
        nodes = self.habitats[h]["nodes"]
        return max(sample, key=lambda i: self._estimate(ag, nodes[i][0]))

    def _difficulty(self, h: int, node: list) -> float:
        return clamp(node[1] + (1 - self.habitats[h]["via"][node[0]]) * 0.6, 0.0, 0.98)

    @staticmethod
    def _record(mem: Dict, arch: int, value: float, add_weight: float = 1.0, cap: float = 12.0):
        e = mem.get(arch)
        if e is None:
            mem[arch] = [round(value, 4), add_weight]
        else:
            w = e[1] + add_weight
            e[0] = round((e[0] * e[1] + value * add_weight) / w, 4)
            e[1] = min(w, cap)

    def _place(self, ag: Agent, h: int, node_idx: int) -> None:
        ag.hab, ag.node = h, node_idx
        self.habitats[h]["nodes"][node_idx][4] += 1

    def _leave(self, ag: Agent) -> None:
        n = self.habitats[ag.hab]["nodes"][ag.node]
        n[4] = max(0, n[4] - 1)

    def _new_agent(self, *, lineage, gen, parent, hab, node, energy, rules, default, trust, memory) -> Agent:
        ag = Agent(id=self.next_id, lineage=lineage, gen=gen, parent=parent, hab=hab, node=node,
                   energy=energy, age=0, rules=rules, default=default, trust=trust,
                   memory=memory, counts=[0] * len(ACTIONS), born=self.tick)
        self.next_id += 1
        self.habitats[hab]["nodes"][node][4] += 1
        self.agents.append(ag)
        lin = self.lineages[lineage]
        lin["alive"] += 1
        lin["max_gen"] = max(lin["max_gen"], gen)
        return ag

    def _seed_founders(self) -> None:
        h = self.cfg["founder_habitat"]
        free = self._free_nodes(h)
        self.rng.shuffle(free)
        for idx in free[: self.cfg["founders"]]:
            lid = self.next_lineage
            self.next_lineage += 1
            self.lineages[lid] = {"founded": self.tick, "epoch": self.epoch, "max_gen": 0, "alive": 0}
            rules, default, trust = founder_program(self.rng)
            self._new_agent(lineage=lid, gen=0, parent=None, hab=h, node=idx, energy=0.6,
                            rules=rules, default=default, trust=trust, memory={})

    # ----------------------------------------------------------- dynamics --
    def _environment(self) -> None:
        for h, (hab, spec) in enumerate(zip(self.habitats, self.cfg["habitats"])):
            if spec["drift"]:
                hab["via"] = [round(clamp(v + self.rng.gauss(0, spec["drift"]), 0.05, 1.0), 4) for v in hab["via"]]
            if spec["shock_prob"] and self.rng.random() < spec["shock_prob"]:
                hab["via"] = [round(self.rng.uniform(0.05, 1.0), 4) for _ in hab["via"]]
                self.tick_events.append(("shock", {"habitat": h}))
            regen = spec["regen"]
            for n in hab["nodes"]:
                n[3] = round(n[3] + regen * (1 - n[3]), 4)

    def _features(self, ag: Agent) -> List[float]:
        node = self.habitats[ag.hab]["nodes"][ag.node]
        company = min(1.0, (len(self._members.get((ag.hab, ag.node), ())) - 1) / 2)
        return [ag.energy, self._crowding[ag.hab], self._estimate(ag, node[0]), node[3],
                ag.age / self.cfg["max_age"], company]

    def _decide(self, ag: Agent, feats: List[float]) -> int:
        for f, op, t, a in ag.rules:
            v = feats[f]
            if (v > t) if op else (v < t):
                return a
        return ag.default

    def _act(self, ag: Agent, action: int) -> float:
        """Execute one action. Returns the metabolism multiplier for this tick."""
        name = ACTIONS[action]
        hab = self.habitats[ag.hab]
        node = hab["nodes"][ag.node]
        if name == "CONSUME":
            take = min(node[3], 0.3)
            node[3] = round(node[3] - take, 4)
            ag.energy = min(1.0, ag.energy + take * (0.4 + 0.6 * hab["via"][node[0]]))
        elif name == "REST":
            return 0.5
        elif name == "REPLICATE":
            if ag.energy < 0.5 or len(self.agents) >= self.cfg["max_population"]:
                return 1.0
            ag.energy -= 0.35
            target = self._choose_node(ag, ag.hab)
            if target is None:
                return 1.0
            tnode = hab["nodes"][target]
            self._record(ag.memory, tnode[0], hab["via"][tnode[0]])
            if self.rng.random() < 1 - self._difficulty(ag.hab, tnode):
                rules, default, trust = mutate(self.rng, ag.rules, ag.default, ag.trust)
                memory = {k: list(v) for k, v in ag.memory.items()}
                self._new_agent(lineage=ag.lineage, gen=ag.gen + 1, parent=ag.id, hab=ag.hab, node=target,
                                energy=0.3, rules=rules, default=default, trust=trust, memory=memory)
                self.births += 1
                self.window["births"][ag.hab] += 1
        elif name == "TEST":
            probe = hab["nodes"][self.rng.randrange(len(hab["nodes"]))]
            self._record(ag.memory, probe[0], hab["via"][probe[0]])
            ag.energy -= 0.01
        elif name == "READ":
            for arch, (b, w) in hab["commons"].items():
                self._record(ag.memory, int(arch), b, add_weight=max(0.1, w * ag.trust * 0.25))
            ag.energy -= 0.01
        elif name == "SHARE":
            for arch, (b, w) in ag.memory.items():
                self._record(hab["commons"], arch, b, add_weight=1.0, cap=20.0)
            ag.energy -= 0.02
        elif name == "MOVE":
            ag.energy -= 0.03
            target = self._choose_node(ag, ag.hab)
            if target is not None and target != ag.node:
                self._leave(ag)
                self._place(ag, ag.hab, target)
        elif name == "STEAL":
            ag.energy -= 0.02
            victims = [o for o in self._members.get((ag.hab, ag.node), ())
                       if o is not ag and o.energy > 0 and o.hab == ag.hab and o.node == ag.node]
            if victims and self.rng.random() < 0.5:
                v = self.rng.choice(victims)
                amount = min(0.25, v.energy)
                v.energy = round(v.energy - amount, 4)
                ag.energy = min(1.0, ag.energy + 0.8 * amount)
                self.window["steals"][ag.hab] += 1
        elif name == "MIGRATE":
            if ag.energy < 0.2:
                return 1.0
            ag.energy -= 0.12
            dest = self.rng.choice(self.links[ag.hab])
            if self.rng.random() < 0.6 * (1 - self.cfg["habitats"][dest]["harshness"]):
                target = self._choose_node(ag, dest)
                if target is not None:
                    self._leave(ag)
                    self._place(ag, dest, target)
                    self.migrations += 1
                    self.window["arrivals"][dest] += 1
        return 1.0

    def _reap(self) -> None:
        survivors = []
        max_age = self.cfg["max_age"]
        for ag in self.agents:
            if ag.energy <= 0 or ag.age >= max_age:
                self._leave(ag)
                self.deaths += 1
                self.window["deaths"][ag.hab] += 1
                lin = self.lineages[ag.lineage]
                lin["alive"] -= 1
                if lin["alive"] == 0:
                    del self.lineages[ag.lineage]
                    self.extinct_lineages += 1
            else:
                survivors.append(ag)
        self.agents = survivors

    def step(self) -> None:
        self._environment()
        # Crowding is read once per tick per habitat (cheap, and order-independent).
        self._crowding = []
        for hab in self.habitats:
            cap = sum(n[2] for n in hab["nodes"])
            occ = sum(n[4] for n in hab["nodes"])
            self._crowding.append(occ / cap if cap else 1.0)
        # Who shares a node with whom, read once per tick.
        self._members = {}
        for ag in self.agents:
            self._members.setdefault((ag.hab, ag.node), []).append(ag)
        order = list(self.agents)
        self.rng.shuffle(order)
        for ag in order:
            action = self._decide(ag, self._features(ag))
            ag.counts[action] += 1
            self.window["actions"][ag.hab][action] += 1
            mult = self._act(ag, action)
            ag.energy = round(ag.energy - 0.03 * self.cfg["habitats"][ag.hab]["metabolism"] * mult, 4)
            ag.age += 1
        self._reap()
        self.tick += 1
        if not self.agents:
            self.tick_events.append(("global_extinction", {"epoch": self.epoch}))
            if self.cfg["reseed_on_global_extinction"]:
                self.epoch += 1
                self._seed_founders()
                self.tick_events.append(("reseed", {"epoch": self.epoch}))

    # -------------------------------------------------------- persistence --
    def to_state(self) -> Dict:
        return {
            "tick": self.tick, "epoch": self.epoch, "next_id": self.next_id,
            "next_lineage": self.next_lineage, "extinct_lineages": self.extinct_lineages,
            "births": self.births, "deaths": self.deaths, "migrations": self.migrations,
            "rng": [self.rng.getstate()[0], list(self.rng.getstate()[1]), self.rng.getstate()[2]],
            "habitats": [{"nodes": h["nodes"], "via": h["via"],
                          "commons": {str(k): v for k, v in h["commons"].items()}} for h in self.habitats],
            "lineages": {str(k): v for k, v in self.lineages.items()},
            "agents": [ag.to_list() for ag in self.agents],
        }

    @classmethod
    def from_state(cls, cfg: Dict, st: Dict) -> "World":
        w = cls.__new__(cls)
        w.cfg = cfg
        w.rng = random.Random()
        w.rng.setstate((st["rng"][0], tuple(st["rng"][1]), st["rng"][2]))
        for k in ("tick", "epoch", "next_id", "next_lineage", "extinct_lineages", "births", "deaths", "migrations"):
            setattr(w, k, st[k])
        w.habitats = [{"nodes": h["nodes"], "via": h["via"],
                       "commons": {int(k): v for k, v in h["commons"].items()}} for h in st["habitats"]]
        w.lineages = {int(k): v for k, v in st["lineages"].items()}
        w.agents = []
        for row in st["agents"]:
            ag = Agent.from_list(row)
            ag.memory = {int(k): v for k, v in ag.memory.items()}
            w.agents.append(ag)
        w.links = {i: [] for i in range(len(cfg["habitats"]))}
        for a, b in cfg["links"]:
            w.links[a].append(b)
            w.links[b].append(a)
        w.window = w._empty_window()
        w.tick_events = []
        return w
