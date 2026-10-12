"""A family tree of strategy shapes.

Every time a child's program mutates into a shape (a program with thresholds
blanked out) that has not been seen before, the new shape is recorded with the
shape its parent had. Most new shapes are one-off mutants that vanish; a shape is
*registered* (kept permanently) once at least REGISTER agents carry it at a
sample point. When an unregistered shape dies out, anything that pointed to it
is re-pointed to its own parent, so the registered tree stays connected without
keeping every transient mutant forever.

This observer never touches the world's random number generator, so adding or
changing it cannot alter how the world evolves.
"""

from __future__ import annotations

import collections
from typing import Dict, List, Optional

from .model import World, describe_program, program_shape

REGISTER = 10
PUBLISH_MAX = 300   # largest tree the viewer receives: every living shape, then by peak size


def fresh_state() -> Dict:
    return {"next_id": 0, "ids": {}, "reg": {}, "pending": {}, "agent_shape": {}}


class ShapeTracker:
    def __init__(self, state: Dict):
        self.s = state

    def _new_id(self) -> int:
        self.s["next_id"] += 1
        return self.s["next_id"] - 1

    def observe_births(self, w: World) -> None:
        """Assign a shape id to every agent not yet seen. Call after every tick,
        before pruning, so a parent that died this tick is still known."""
        s = self.s
        amap = s["agent_shape"]
        for ag in w.agents:
            key = str(ag.id)
            if key in amap:
                continue
            shape = program_shape(ag.rules, ag.default)
            sid = s["ids"].get(shape)
            if sid is None:
                sid = self._new_id()
                s["ids"][shape] = sid
                parent = amap.get(str(ag.parent)) if ag.parent is not None else None
                s["pending"][str(sid)] = {"shape": shape, "first_tick": w.tick, "parent": parent,
                                          "example": describe_program(ag.rules, ag.default)}
            amap[key] = sid

    def sample(self, w: World) -> Dict[int, int]:
        """Update peaks, register shapes that reached REGISTER agents, and prune
        dead unregistered shapes. Returns {shape_id: living count}."""
        s = self.s
        living = {str(a.id) for a in w.agents}
        s["agent_shape"] = {k: v for k, v in s["agent_shape"].items() if k in living}
        counts = collections.Counter(s["agent_shape"].values())

        for key, p in list(s["pending"].items()):
            sid = int(key)
            if counts.get(sid, 0) >= REGISTER:
                s["reg"][key] = {"id": sid, "shape": p["shape"], "first_tick": p["first_tick"],
                                 "parent": p["parent"], "registered_tick": w.tick,
                                 "peak": 0, "peak_tick": w.tick, "last_tick": w.tick,
                                 "example": p["example"]}
                del s["pending"][key]

        for key, r in s["reg"].items():
            c = counts.get(r["id"], 0)
            if c:
                r["last_tick"] = w.tick
            if c > r["peak"]:
                r["peak"], r["peak_tick"] = c, w.tick

        dead = {k for k in s["pending"] if counts.get(int(k), 0) == 0}
        if dead:
            def resolve(pid: Optional[int]) -> Optional[int]:
                while pid is not None and str(pid) in dead:
                    pid = s["pending"][str(pid)]["parent"]
                return pid
            for k, p in s["pending"].items():
                if k not in dead:
                    p["parent"] = resolve(p["parent"])
            for r in s["reg"].values():
                r["parent"] = resolve(r["parent"])
            for k in dead:
                del s["ids"][s["pending"][k]["shape"]]
                del s["pending"][k]
        return dict(counts)

    def nearest_registered(self, sid: int) -> Optional[int]:
        """The registered shape an agent's shape is, or most recently descends from."""
        s = self.s
        while sid is not None and str(sid) not in s["reg"]:
            p = s["pending"].get(str(sid))
            sid = p["parent"] if p else None
        return sid

    def publish(self, w: World) -> Dict:
        s = self.s
        counts = collections.Counter(s["agent_shape"].values())
        alive_by_reg = collections.Counter()
        for sid, c in counts.items():
            r = self.nearest_registered(sid)
            if r is not None:
                alive_by_reg[r] += c
        examples = collections.defaultdict(collections.Counter)
        for a in w.agents:
            sid = s["agent_shape"].get(str(a.id))
            if sid is not None and str(sid) in s["reg"]:
                examples[sid][describe_program(a.rules, a.default)] += 1
        # Keep the published tree bounded: every living shape, then the largest
        # extinct ones; parents are re-pointed to the nearest kept ancestor.
        regs = list(s["reg"].values())
        alive_ids = {r["id"] for r in regs if alive_by_reg.get(r["id"], 0)}
        ranked = sorted(regs, key=lambda r: (r["id"] not in alive_ids, -r["peak"], r["id"]))
        keep = {r["id"] for r in ranked[:PUBLISH_MAX]}

        def kept_parent(pid: Optional[int]) -> Optional[int]:
            pid = self.nearest_registered(pid) if pid is not None else None
            while pid is not None and pid not in keep:
                nxt = s["reg"][str(pid)]["parent"]
                pid = self.nearest_registered(nxt) if nxt is not None else None
            return pid

        shapes: List[Dict] = []
        for r in sorted((r for r in regs if r["id"] in keep), key=lambda r: r["id"]):
            ex = examples.get(r["id"])
            shapes.append({**r, "parent": kept_parent(r["parent"]), "alive": counts.get(r["id"], 0),
                           "alive_with_variants": alive_by_reg.get(r["id"], 0),
                           "example": ex.most_common(1)[0][0] if ex else r["example"]})
        return {"shapes": shapes, "registered_total": len(regs)}
