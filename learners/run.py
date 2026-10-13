"""Run Study 1: one (seed, arm, regime) at a time, records appended to JSONL.

    python -m learners.run --phase pilot --seeds 100-109
    python -m learners.run --phase confirmation --seeds 7000-7029

Each line of learners/results/<phase>.jsonl is one immutable run record
carrying the code commit and protocol hash it was produced with. Re-running
skips records that already exist, so an interrupted batch can resume.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from . import __version__  # noqa: E402
from .arms import ARMS, FWD  # noqa: E402
from .net import MLP  # noqa: E402
from .world import SkillWorld, random_inputs  # noqa: E402

STUDY = "reproduce_or_live_forever"
HERE = os.path.dirname(os.path.abspath(__file__))
PROTOCOL_PATH = os.path.join(HERE, "protocol.json")
RESULTS_DIR = os.path.join(HERE, "results")
ARM_ORDER = ["IMMORTAL", "RESET", "RESTART", "TEACH", "CLONE", "GENES", "RANDOM"]
NO_LIFESPAN = 0  # IMMORTAL never reproduces, so one run serves every lifespan


def load_protocol(path: str = PROTOCOL_PATH) -> Dict:
    with open(path) as f:
        return json.load(f)


def protocol_hash(proto: Dict) -> str:
    return hashlib.sha256(json.dumps(proto, sort_keys=True).encode()).hexdigest()[:16]


def code_commit() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=5, check=False).stdout.strip()
        if rev and rev != "HEAD":
            dirty = subprocess.run(["git", "status", "--porcelain", "--", "learners"],
                                   capture_output=True, text=True, timeout=5,
                                   check=False).stdout.strip()
            return rev + ("-dirty" if dirty else "")
    except Exception:
        pass
    return "unknown"


# ---- measurement (outside every arm's budget, identical for all arms) ----
def evaluate(net: MLP, world: SkillWorld, task, key: Tuple, n: int) -> float:
    x, y = world.batch(task, np.random.default_rng(key), n)
    return net.accuracy(x, y)


def probe(net: MLP, world: SkillWorld, task, steps: int, key: Tuple, proto: Dict) -> float:
    """Fine-tune a copy on a probe task (fresh Adam, the net's own settings),
    then score it. The copy is discarded, so probing never affects a run."""
    c = net.copy(with_optimizer=False)
    rng = np.random.default_rng(key)
    for _ in range(steps):
        x, y = world.batch(task, rng, proto["batch"])
        c.train_step(x, y)
    return evaluate(c, world, task, key + (1,), proto["eval_n"])


def probe_battery(world: SkillWorld, checkpoint: int, proto: Dict, net_for) -> Dict[str, List[float]]:
    reuse, novel = world.probes(checkpoint)
    out = {}
    for kind, tasks in (("reuse", reuse), ("novel", novel)):
        out[kind] = [round(probe(net_for(kind, i), world, t, proto["probe_steps"],
                                 (world.seed, 4, checkpoint, kind == "novel", i), proto), 4)
                     for i, t in enumerate(tasks)]
    return out


# ---- runs -----------------------------------------------------------------
def run_one(seed: int, arm: str, R: int, L: int, proto: Dict) -> Dict:
    t0 = time.time()
    world = SkillWorld(seed, R, proto["n_eras"])
    rng = np.random.default_rng([seed, 10, R, L, ARM_ORDER.index(arm)])
    a = ARMS[arm](proto, rng, L if L else 10 ** 9)
    online, rep_ids, probes, diag, macs = [], [], {}, {}, []
    for era in range(proto["n_eras"]):
        before = a.macs
        a.era(world, era)
        macs.append(a.macs - before)
        rep = a.representative()
        rep_ids.append(rep.id)
        online.append(round(evaluate(rep.net, world, world.tasks[era], (seed, 3, era),
                                     proto["eval_n"]), 4))
        cp = era + 1
        if cp in proto["checkpoints"]:
            probes[cp] = probe_battery(world, cp, proto, lambda kind, i: rep.net)
            xs = random_inputs(np.random.default_rng([seed, 7, cp]), 1000)
            diag[cp] = {"dead": round(rep.net.dead_fraction(xs), 4),
                        "weight_norm": round(rep.net.weight_norm(), 3),
                        "rep": {"id": rep.id, **{k: round(v, 8) for k, v in rep.genome().items()}},
                        "members": [{"id": m.id, "fitness": round(m.fitness, 4),
                                     **{k: round(v, 8) for k, v in m.genome().items()}}
                                    for m in a.members]}
    last = proto["checkpoints"][-1]
    half = proto["n_eras"] // 2
    return {
        "arm": arm, "seed": seed, "R": R, "L": L,
        "FINAL_REUSE": round(float(np.mean(probes[last]["reuse"])), 4),
        "FINAL_NOVEL": round(float(np.mean(probes[last]["novel"])), 4),
        "ONLINE": round(float(np.mean(online[half:])), 4),
        "online": online, "tasks": world.tasks, "probes": probes, "diag": diag,
        "rep_ids": rep_ids, "lineage": a.lineage, "macs_per_era": macs,
        "budget_per_era": a.budget, "seconds": round(time.time() - t0, 2),
    }


def run_scratch(seed: int, R: int, proto: Dict) -> Dict:
    """The probe battery on fresh default networks: context for every arm."""
    t0 = time.time()
    world = SkillWorld(seed, R, proto["n_eras"])
    probes = {}
    for cp in proto["checkpoints"]:
        fresh = lambda kind, i, cp=cp: MLP(np.random.default_rng([seed, 6, cp, kind == "novel", i]),
                                           lr=proto["lr"])
        probes[cp] = probe_battery(world, cp, proto, fresh)
    last = proto["checkpoints"][-1]
    return {"arm": "SCRATCH", "seed": seed, "R": R, "L": NO_LIFESPAN,
            "FINAL_REUSE": round(float(np.mean(probes[last]["reuse"])), 4),
            "FINAL_NOVEL": round(float(np.mean(probes[last]["novel"])), 4),
            "probes": probes, "seconds": round(time.time() - t0, 2)}


def jobs(seeds: List[int], proto: Dict, arms: Optional[List[str]] = None) -> List[Tuple]:
    arms = arms or ARM_ORDER
    out = []
    for seed in seeds:
        for R in proto["regimes"]["novelty_interval"]:
            out.append((seed, "SCRATCH", R, NO_LIFESPAN))
            for arm in arms:
                lifespans = [NO_LIFESPAN] if arm == "IMMORTAL" else proto["regimes"]["lifespan"]
                for L in lifespans:
                    out.append((seed, arm, R, L))
    return out


def _work(args):
    seed, arm, R, L, proto, meta = args
    rec = run_scratch(seed, R, proto) if arm == "SCRATCH" else run_one(seed, arm, R, L, proto)
    return {**meta, **rec, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def parse_seeds(text: str) -> List[int]:
    out = []
    for part in text.split(","):
        if "-" in part:
            lo, hi = part.split("-")
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return out


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["pilot", "confirmation", "smoke"])
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--arms", default="")
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--protocol", default=PROTOCOL_PATH)
    ap.add_argument("--shard", default="0/1", help="i/n: run every n-th job starting at i")
    args = ap.parse_args(argv)

    proto = load_protocol(args.protocol)
    if args.phase == "confirmation" and not proto.get("frozen"):
        sys.exit("protocol.json is not frozen; confirmation seeds may not be run yet")
    meta = {"study": STUDY, "phase": args.phase, "version": __version__,
            "code_commit": code_commit(), "protocol_hash": protocol_hash(proto)}
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, f"{args.phase}.jsonl")
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if r["protocol_hash"] == meta["protocol_hash"]:
                    done.add((r["seed"], r["arm"], r["R"], r["L"]))
    i, n = (int(v) for v in args.shard.split("/"))
    todo = [j for k, j in enumerate(jobs(parse_seeds(args.seeds), proto,
                                         [a for a in args.arms.split(",") if a] or None))
            if k % n == i and j not in done]
    print(f"{len(todo)} runs to do ({len(done)} already recorded)", flush=True)
    work = [(s, a, R, L, proto, meta) for s, a, R, L in todo]
    if args.procs > 1:
        import multiprocessing as mp
        with mp.get_context("fork").Pool(args.procs) as pool, open(path, "a") as f:
            for rec in pool.imap_unordered(_work, work):
                f.write(json.dumps(rec) + "\n")
                f.flush()
                print(f"  {rec['arm']:8s} seed {rec['seed']} R={rec['R']} L={rec['L']}  "
                      f"reuse {rec['FINAL_REUSE']:.3f}  novel {rec['FINAL_NOVEL']:.3f}  "
                      f"{rec['seconds']}s", flush=True)
    else:
        with open(path, "a") as f:
            for w in work:
                rec = _work(w)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                print(f"  {rec['arm']:8s} seed {rec['seed']} R={rec['R']} L={rec['L']}  "
                      f"reuse {rec['FINAL_REUSE']:.3f}  novel {rec['FINAL_NOVEL']:.3f}  "
                      f"{rec['seconds']}s", flush=True)


if __name__ == "__main__":
    main()
