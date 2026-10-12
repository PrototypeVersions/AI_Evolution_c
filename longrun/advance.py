"""Advance the persistent world and publish what happened.

    python -m longrun.advance --ticks 2000          # continue from the checkpoint
    python -m longrun.advance --ticks 2000 --init   # start a brand-new world (tick 0)

Each advance loads longrun/state/, runs more ticks, detects notable events,
appends sampled history, saves the checkpoint, and writes docs/longrun.json for
the viewer. If longrun/config.json changed since the last advance, that change
is logged as an *intervention* so the record always shows when the world's rules
were touched by a person rather than evolving on their own.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import hashlib
import json
import os
import time
from typing import Dict, List

from experiments.records import code_commit

from .model import ACTIONS, FAMILIES, FAMILY_OF, World, describe_program, program_shape
from .phylo import ShapeTracker, fresh_state

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config.json")
STATE_DIR = os.path.join(HERE, "state")
STATE = os.path.join(STATE_DIR, "world.json.gz")
# History and events are append-only JSON lines: git stores appends as small
# deltas, whereas a rewritten gzip would add a full copy to the repo every day.
HIST_HAB = os.path.join(STATE_DIR, "history_habitats.jsonl")
HIST_WORLD = os.path.join(STATE_DIR, "history_world.jsonl")
EVENTS = os.path.join(STATE_DIR, "events.jsonl")
HIST_SHAPES = os.path.join(STATE_DIR, "history_shapes.jsonl")
META = os.path.join(STATE_DIR, "meta.json")
DOCS = os.path.join(os.path.dirname(HERE), "docs", "longrun.json")

FAMILY_IDX = {f: i for i, f in enumerate(FAMILIES)}
SETTLED, HOLD = 5, 20   # a habitat is "settled" after >= 5 agents for 20 ticks
SHAPE_EVERY = 100       # ticks between strategy-population samples


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())


def _hash(cfg: Dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:16]


def _read_gz(path):
    with gzip.open(path, "rt") as fh:
        return json.load(fh)


def _write_gz(path, obj):
    # mtime=0 keeps the file byte-identical for identical content.
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as fh:
        fh.write(json.dumps(obj, separators=(",", ":")).encode())


class Observer:
    """Turns raw world state into a sampled history and a feed of notable events.

    Events are descriptive ("Shock Valley went extinct"), never interpretive.
    """

    def __init__(self, world: World, meta: Dict, history: Dict, cfg: Dict):
        self.w, self.meta, self.history, self.cfg = world, meta, history, cfg
        self.new_events: List[Dict] = []
        self.names = [h["name"] for h in cfg["habitats"]]
        self.history.setdefault("shapes", [])
        self.phylo = ShapeTracker(meta.setdefault("phylo", fresh_state()))

    def event(self, kind: str, text: str, **data) -> None:
        self.new_events.append({"tick": self.w.tick, "epoch": self.w.epoch, "kind": kind,
                                "text": text, "data": data})

    def _pops(self) -> List[int]:
        pops = [0] * len(self.names)
        for ag in self.w.agents:
            pops[ag.hab] += 1
        return pops

    def after_tick(self) -> None:
        w, m = self.w, self.meta
        self.phylo.observe_births(w)
        for kind, data in w.tick_events:
            if kind == "shock":
                self.event("shock", f"Shock in {self.names[data['habitat']]}: which node types are viable changed abruptly.", habitat=data["habitat"])
            elif kind == "global_extinction":
                self.event("global_extinction", f"Every agent in the world died. Epoch {data['epoch']} ended.")
            elif kind == "reseed":
                self.event("reseed", f"Epoch {data['epoch']} began with {self.cfg['founders']} fresh founders (pre-declared rule, not an intervention).")
        w.tick_events = []

        # Habitat status with hysteresis: a habitat is "settled" only after
        # holding >= SETTLED agents for HOLD ticks, and "dies out" only from that
        # state, so brief incursions don't flood the feed.
        pops = self._pops()
        for h, now in enumerate(pops):
            st = m["hstate"][h]
            name = self.names[h]
            if now == 0:
                if st == "settled":
                    self.event("local_extinction", f"The population of {name} died out (settled since tick {m['settled_at'][h]}).", habitat=h)
                    m["emptied_at"][h] = w.tick
                    m["attempts"][h] = 0
                m["hstate"][h], m["above_since"][h] = "empty", None
                continue
            if st == "empty":
                m["hstate"][h] = st = "foothold"
                m["attempts"][h] += 1
                if not m["colonized"][h]:
                    m["colonized"][h] = True
                    lin = next(ag.lineage for ag in w.agents if ag.hab == h)
                    self.event("arrival", f"First agents ever reach {name} (lineage L{lin}).", habitat=h, lineage=lin)
            if now >= SETTLED:
                if m["above_since"][h] is None:
                    m["above_since"][h] = w.tick
                if st != "settled" and w.tick - m["above_since"][h] >= HOLD:
                    m["hstate"][h] = "settled"
                    m["settled_at"][h] = w.tick
                    tries = m["attempts"][h]
                    if not m["ever_settled"][h]:
                        m["ever_settled"][h] = True
                        self.event("colonization", f"{name} is settled for the first time, after {tries} attempt{'s' * (tries != 1)}.", habitat=h)
                    else:
                        gap = w.tick - m["emptied_at"][h]
                        self.event("recolonization", f"{name} was resettled {gap} ticks after dying out, after {tries} attempt{'s' * (tries != 1)}.", habitat=h)
            else:
                m["above_since"][h] = None
        m["occupied"] = pops

        n_lin = len(w.lineages)
        if n_lin == 1 and not m["single_lineage"]:
            lid = next(iter(w.lineages))
            self.event("single_lineage", f"Only one founding lineage (L{lid}) survives; every living agent descends from it.", lineage=lid)
        m["single_lineage"] = n_lin == 1

        max_gen = max((l["max_gen"] for l in w.lineages.values()), default=0)
        milestone = (max_gen // 100) * 100
        if milestone > m["gen_milestone"]:
            m["gen_milestone"] = milestone
            self.event("generation", f"Generation {milestone} reached.")

        if w.tick % self.cfg["sample_every"] == 0:
            self._sample(pops)

    def _sample(self, pops: List[int]) -> None:
        w, m = self.w, self.meta
        by_hab = collections.defaultdict(list)
        for ag in w.agents:
            by_hab[ag.hab].append(ag)
        for h in range(len(self.names)):
            fam = [0] * len(FAMILIES)
            for a_idx, c in enumerate(w.window["actions"][h]):
                fam[FAMILY_IDX[FAMILY_OF[ACTIONS[a_idx]]]] += c
            ags = by_hab[h]
            self.history["habitat"].append([
                w.tick, h, pops[h],
                round(sum(a.energy for a in ags) / len(ags), 3) if ags else 0,
                len({a.lineage for a in ags}),
                max((a.gen for a in ags), default=0),
                fam, w.window["births"][h], w.window["deaths"][h], w.window["arrivals"][h],
                w.window["steals"][h], [round(v, 2) for v in w.habitats[h]["via"]],
            ])
        w.window = w._empty_window()

        shape_counts = self.phylo.sample(w)
        if w.tick % SHAPE_EVERY == 0:
            fam_counts = collections.Counter()
            for sid, c in shape_counts.items():
                r = self.phylo.nearest_registered(sid)
                if r is not None:
                    fam_counts[r] += c
            self.history["shapes"].append([w.tick, sorted([sid, c] for sid, c in fam_counts.items() if c >= 2)])
        shapes = collections.Counter(program_shape(a.rules, a.default) for a in w.agents)
        n_alive = len(w.agents)
        diversity = sum(1 for c in shapes.values() if c >= 3)
        top_share = round(shapes.most_common(1)[0][1] / n_alive, 3) if n_alive else 0
        self.history["world"].append([w.tick, n_alive, diversity, top_share, len(w.lineages)])
        if not n_alive:
            return

        # Innovation: a strategy shape never seen at scale reaches 10% of agents.
        for shape, c in shapes.items():
            if c / n_alive >= 0.10 and shape not in m["seen_shapes"]:
                m["seen_shapes"].append(shape)
                if len(m["seen_shapes"]) > 1:   # the founders' shape isn't news
                    self.event("innovation", f"A new strategy shape spread to {c / n_alive:.0%} of agents: {shape}", shape=shape)

        # Dominance: reported once a shape holds the top spot for 3 samples.
        top, n = shapes.most_common(1)[0]
        pend = m["pending_top"]
        if top == pend.get("shape"):
            pend["count"] += 1
        else:
            m["pending_top"] = pend = {"shape": top, "count": 1}
        if pend["count"] >= 3 and top != m["top_shape"] and n / n_alive >= 0.2:
            first = m["top_shape"] is None
            m["top_shape"] = top
            self.event("strategy", f"{'Most common' if first else 'New most common'} strategy shape ({n / n_alive:.0%} of agents): {top}", shape=top, share=round(n / n_alive, 3))


def _fresh_meta(cfg: Dict) -> Dict:
    n = len(cfg["habitats"])
    return {
        "created_at": _now(), "config_hash": _hash(cfg), "advances": [], "interventions": [],
        "occupied": [0] * n, "colonized": [False] * n, "emptied_at": [0] * n,
        "single_lineage": False, "gen_milestone": 0, "pending_top": {}, "top_shape": None,
        "hstate": ["empty"] * n, "above_since": [None] * n, "settled_at": [0] * n,
        "attempts": [0] * n, "ever_settled": [False] * n, "seen_shapes": [],
    }


def _read_jsonl(path: str) -> List:
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _append_jsonl(path: str, rows: List) -> None:
    with open(path, "a") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")


def publish(world: World, meta: Dict, cfg: Dict, commit: str) -> Dict:
    history = {"habitat": _read_jsonl(HIST_HAB), "world": _read_jsonl(HIST_WORLD),
               "shapes": _read_jsonl(HIST_SHAPES)}
    events = _read_jsonl(EVENTS)
    names = [h["name"] for h in cfg["habitats"]]
    tracker = ShapeTracker(meta["phylo"])
    phylo = tracker.publish(world)

    # A snapshot of every node and agent right now, for the live habitat view.
    snap_agents = []
    for a in world.agents:
        sid = meta["phylo"]["agent_shape"].get(str(a.id))
        reg = tracker.nearest_registered(sid) if sid is not None else None
        snap_agents.append([a.hab, a.node, -1 if reg is None else reg, int(sid is not None and sid == reg),
                            a.lineage, round(a.energy, 2), a.gen, a.age])
    snapshot = {
        "nodes": [[[n[0], n[2], round(n[3], 2), n[4]] for n in hab["nodes"]] for hab in world.habitats],
        "agents": snap_agents,
    }
    by_hab = collections.defaultdict(list)
    for ag in world.agents:
        by_hab[ag.hab].append(ag)
    recent = {}
    for row in history["habitat"][-len(names) * 5:]:
        recent.setdefault(row[1], []).append(row)

    habitats = []
    for h, name in enumerate(names):
        ags = by_hab[h]
        shapes = collections.Counter(program_shape(a.rules, a.default) for a in ags)
        fam = [0] * len(FAMILIES)
        for r in recent.get(h, []):
            fam = [x + y for x, y in zip(fam, r[6])]
        tot = sum(fam) or 1
        top = shapes.most_common(1)
        habitats.append({
            "name": name, "spec": cfg["habitats"][h], "status": meta["hstate"][h],
            "population": len(ags),
            "capacity": sum(n[2] for n in world.habitats[h]["nodes"]),
            "mean_energy": round(sum(a.energy for a in ags) / len(ags), 3) if ags else 0,
            "lineages": sorted({a.lineage for a in ags}),
            "family_share": [round(x / tot, 3) for x in fam],
            "top_shape": {"shape": top[0][0], "share": round(top[0][1] / len(ags), 3)} if top else None,
            "viability": world.habitats[h]["via"],
            "commons_entries": len(world.habitats[h]["commons"]),
            "links": world.links[h],
        })

    groups = collections.defaultdict(list)
    for a in world.agents:
        groups[program_shape(a.rules, a.default)].append(a)
    strategies = []
    for shape, ags in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:10]:
        example = collections.Counter(describe_program(a.rules, a.default) for a in ags).most_common(1)[0][0]
        strategies.append({
            "shape": shape, "example": example, "count": len(ags),
            "mean_gen": round(sum(a.gen for a in ags) / len(ags), 1),
            "habitats": sorted({names[a.hab] for a in ags}),
            "rules": len(ags[0].rules),
        })

    lineages = []
    for lid, lin in sorted(world.lineages.items(), key=lambda kv: -kv[1]["alive"]):
        members = [a for a in world.agents if a.lineage == lid]
        lineages.append({"id": lid, "founded": lin["founded"], "epoch": lin["epoch"],
                         "max_gen": lin["max_gen"], "alive": lin["alive"],
                         "habitats": sorted({names[a.hab] for a in members})})

    # Downsample long histories so the page stays small (~1500 points per series).
    n_samples = len(history["world"])
    step = max(1, n_samples // 1500)
    keep = lambda t: (t // cfg["sample_every"]) % step == 0
    out = {
        "generated_at": _now(), "tick": world.tick, "epoch": world.epoch,
        "code_commit": commit, "created_at": meta["created_at"],
        "families": list(FAMILIES), "actions": list(ACTIONS), "links": cfg["links"],
        "totals": {"alive": len(world.agents), "births": world.births, "deaths": world.deaths,
                   "migrations": world.migrations, "lineages_alive": len(world.lineages),
                   "lineages_extinct": world.extinct_lineages,
                   "max_generation": max((l["max_gen"] for l in world.lineages.values()), default=0),
                   "strategy_shapes": sum(1 for g in groups.values() if len(g) >= 3),
                   "shapes_ever_spread": len(meta["seen_shapes"])},
        "habitats": habitats, "strategies": strategies, "lineages": lineages,
        "habitat_columns": ["tick", "habitat", "population", "mean_energy", "lineages", "max_gen",
                            "family_actions", "births", "deaths", "arrivals", "steals", "viability"],
        "world_columns": ["tick", "alive", "strategy_shapes", "top_shape_share", "lineages"],
        "habitat_history": [r for r in history["habitat"] if keep(r[0])],
        "world_history": [r for r in history["world"] if keep(r[0])],
        "shape_history": history["shapes"][::max(1, len(history["shapes"]) // 600)],
        "shape_history_note": "per sample: [tick, [[shape_id, agents incl. unregistered variants], ...]]",
        "phylo": phylo["shapes"], "phylo_registered_total": phylo["registered_total"], "snapshot": snapshot,
        "snapshot_columns": {"node": ["arch", "capacity", "resource", "occupants"],
                             "agent": ["habitat", "node", "shape_id", "exact_shape", "lineage", "energy", "gen", "age"]},
        "n_arch": cfg["n_arch"],
        "events": events[-300:], "event_count": len(events),
        "interventions": meta["interventions"], "advances": meta["advances"][-30:],
    }
    os.makedirs(os.path.dirname(DOCS), exist_ok=True)
    with open(DOCS, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    return out


def genesis(cfg: Dict):
    """A brand-new world at tick 0, with its observer. Shared by advance and replay."""
    world = World(cfg)
    meta = _fresh_meta(cfg)
    obs = Observer(world, meta, {"habitat": [], "world": [], "shapes": []}, cfg)
    home = cfg["founder_habitat"]
    obs.event("genesis", f"World created: {len(cfg['habitats'])} habitats, {cfg['founders']} founders in {cfg['habitats'][home]['name']}.")
    obs.phylo.observe_births(world)
    meta["occupied"] = obs._pops()
    meta["colonized"] = [p > 0 for p in meta["occupied"]]
    meta["hstate"][home], meta["ever_settled"][home], meta["settled_at"][home] = "settled", True, 0
    return world, meta, obs


def advance(ticks: int, init: bool = False) -> Dict:
    with open(CONFIG) as fh:
        cfg = json.load(fh)
    ticks = min(ticks, cfg["max_ticks_per_advance"])
    commit = code_commit()   # read before any files change, so it reflects the code that ran
    os.makedirs(STATE_DIR, exist_ok=True)

    if init or not os.path.exists(STATE):
        for path in (HIST_HAB, HIST_WORLD, EVENTS, HIST_SHAPES):
            if os.path.exists(path):
                os.remove(path)
        world, meta, obs = genesis(cfg)
    else:
        with open(META) as fh:
            meta = json.load(fh)
        world = World.from_state(cfg, _read_gz(STATE))
        obs = Observer(world, meta, {"habitat": [], "world": [], "shapes": []}, cfg)
        new_hash = _hash(cfg)
        if new_hash != meta["config_hash"]:
            entry = {"tick": world.tick, "at": _now(), "from": meta["config_hash"], "to": new_hash,
                     "commit": commit}
            meta["interventions"].append(entry)
            obs.event("intervention", "The world's rules (config.json) were changed by a person at this point.", **entry)
            meta["config_hash"] = new_hash

    start_tick, started = world.tick, time.time()
    for _ in range(ticks):
        if time.time() - started > cfg["max_seconds_per_advance"]:
            obs.event("capped", "Advance stopped early at the wall-clock cap.")
            break
        world.step()
        obs.after_tick()

    meta["advances"].append({"from": start_tick, "to": world.tick, "at": _now(), "commit": commit,
                             "seconds": round(time.time() - started, 1)})
    _write_gz(STATE, world.to_state())
    _append_jsonl(HIST_HAB, obs.history["habitat"])
    _append_jsonl(HIST_WORLD, obs.history["world"])
    _append_jsonl(EVENTS, obs.new_events)
    _append_jsonl(HIST_SHAPES, obs.history["shapes"])
    with open(META, "w") as fh:
        json.dump(meta, fh, separators=(",", ":"))
    return publish(world, meta, cfg, commit)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ticks", type=int, default=2000)
    ap.add_argument("--init", action="store_true", help="start a new world from tick 0")
    args = ap.parse_args()
    out = advance(args.ticks, init=args.init)
    t = out["totals"]
    print(f"Tick {out['tick']} (epoch {out['epoch']}): {t['alive']} agents, "
          f"{t['lineages_alive']} lineages, max generation {t['max_generation']}.")
    for h in out["habitats"]:
        print(f"  {h['name']:<16} pop {h['population']:>4} / {h['capacity']}")
    for e in out["events"][-8:]:
        print(f"  [t{e['tick']}] {e['text']}")


if __name__ == "__main__":
    main()
