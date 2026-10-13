"""Run Study 1 or 1b: one (seed, arm, regime) at a time, records appended to JSONL.

    python -m learners.run --phase pilot --seeds 100-109
    python -m learners.run --phase confirmation --seeds 7000-7029
    python -m learners.run --phase pilot_1b --seeds 300-304 --protocol learners/protocol_1b.json

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
import platform
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np  # noqa: E402

from . import __version__  # noqa: E402
from . import arms_1b  # noqa: E402
from .arms import ARMS, FWD  # noqa: E402
from .net import MLP, fresh_weight  # noqa: E402
from .world import SkillWorld, random_inputs  # noqa: E402

STUDY = "reproduce_or_live_forever"
HERE = os.path.dirname(os.path.abspath(__file__))
PROTOCOL_PATH = os.path.join(HERE, "protocol.json")
RESULTS_DIR = os.path.join(HERE, "results")
ARM_ORDER = ["IMMORTAL", "RESET", "RESTART", "TEACH", "CLONE", "GENES", "RANDOM", "TEACH4", "TEACH16"]
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
KNOWN = 0.9  # a skill counts as known when a linear readout decodes it this well
KINDS = {"frontier": 0, "novel": 1, "knowledge": 2}


def evaluate(net: MLP, world: SkillWorld, task, key: Tuple, n: int) -> float:
    x, y = world.batch(task, np.random.default_rng(key), n)
    return net.accuracy(x, y)


def probe(net: MLP, world: SkillWorld, skill: int, steps: int, key: Tuple, proto: Dict,
          lr: Optional[float] = None) -> float:
    """Fine-tune a copy on a single-skill task, then score it. The copy gets a
    fresh output layer (identical for every arm, drawn from the probe key) and
    fresh Adam state, so the probe measures what the hidden layers can learn
    rather than how confidently the old output layer answers the previous task.
    The copy is discarded, so probing never affects a run."""
    c = net.copy(with_optimizer=False)
    if lr is not None:
        c.lr = lr
    n_in, n_out = c.W[-1].shape
    c.W[-1][...] = fresh_weight(np.random.default_rng(key + (2,)), n_in, n_out)
    c.b[-1][...] = 0.0
    rng = np.random.default_rng(key)
    for _ in range(steps):
        c.train_step(*world.skill_batch(skill, rng, proto["batch"]))
    return c.accuracy(*world.skill_batch(skill, np.random.default_rng(key + (1,)), proto["eval_n"]))


def knowledge(net: MLP, world: SkillWorld, n_skills: int, key: Tuple) -> List[float]:
    """How well each introduced skill can be read out linearly from the last
    hidden layer (ridge least squares on 4,000 inputs, scored on 2,000 more).
    Nothing is trained in the network itself."""
    rng = np.random.default_rng(key)
    xtr, xte = random_inputs(rng, 4000), random_inputs(rng, 2000)
    bias = lambda h: np.hstack([h, np.ones((len(h), 1))])
    Htr, Hte = bias(net.features(xtr)), bias(net.features(xte))
    skills = list(range(n_skills))
    Ytr, Yte = world.signs(xtr, skills), world.signs(xte, skills)
    gram = Htr.T @ Htr
    ridge = 1e-3 * np.trace(gram) / len(gram)
    W = np.linalg.solve(gram + ridge * np.eye(len(gram)), Htr.T @ Ytr)
    return [round(float(v), 4) for v in (np.sign(Hte @ W) == Yte).mean(axis=0)]


def measure(world: SkillWorld, checkpoint: int, proto: Dict, net_for) -> Dict:
    """The full battery at one checkpoint. `net_for(kind, i)` gives the network
    to probe (the arm's representative, or a fresh one for SCRATCH)."""
    skills = world.probes(checkpoint)
    # FRONTIER asks "could it take the next step within one era?", so it gets
    # an era's worth of steps; NOVEL keeps the calibrated probe length.
    steps = {"frontier": proto.get("frontier_steps", proto["probe_steps"]),
             "novel": proto["probe_steps"]}
    out = {kind: [round(probe(net_for(kind, i), world, k, steps[kind],
                              (world.seed, 4, checkpoint, j, i), proto), 4)
                  for i, k in enumerate(ks)]
           for j, (kind, ks) in enumerate(sorted(skills.items()))}
    # secondary: the same probes at the default learning rate, so that the
    # state of the weights can be separated from an evolved step size
    for j, kind in enumerate(sorted(skills)):
        out[f"{kind}_fixed_lr"] = [
            out[kind][i] if net_for(kind, i).lr == proto["lr"] else
            round(probe(net_for(kind, i), world, k, steps[kind],
                        (world.seed, 4, checkpoint, j, i), proto, lr=proto["lr"]), 4)
            for i, k in enumerate(skills[kind])]
    out["skills"] = skills
    n = world.n_introduced(checkpoint - 1)
    acc = knowledge(net_for("knowledge", 0), world, n, (world.seed, 8, checkpoint))
    known = [k for k, a in enumerate(acc) if a >= KNOWN]
    out["knowledge"] = acc
    out["known_share"] = round(len(known) / n, 4)
    out["deepest_known"] = max((world.degrees[k] for k in known), default=0)
    out["deepest_introduced"] = max(world.degrees[:n])
    return out


def summary(probes: Dict, last: int) -> Dict:
    p = probes[last]
    return {"FINAL_NOVEL": round(float(np.mean(p["novel"])), 4),
            "FINAL_FRONTIER": round(float(np.mean(p["frontier"])), 4),
            "FINAL_KNOWLEDGE": p["known_share"], "FINAL_DEPTH": p["deepest_known"]}


# ---- runs -----------------------------------------------------------------
def make_arm(seed: int, arm: str, R: int, L: int, proto: Dict):
    if proto.get("study") == "1b":
        return arms_1b.make(arm, seed, R, L, proto)
    rng = np.random.default_rng([seed, 10, R, L, ARM_ORDER.index(arm)])
    return ARMS[arm](proto, rng, L if L else 10 ** 9)


def run_one(seed: int, arm: str, R: int, L: int, proto: Dict) -> Dict:
    t0 = time.time()
    world = SkillWorld(seed, R, proto["n_eras"])
    a = make_arm(seed, arm, R, L, proto)
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
            probes[cp] = measure(world, cp, proto, lambda kind, i: rep.net)
            xs = random_inputs(np.random.default_rng([seed, 7, cp]), 1000)
            diag[cp] = {"dead": round(rep.net.dead_fraction(xs), 4),
                        "weight_norm": round(rep.net.weight_norm(), 3),
                        "rep": {"id": rep.id, **{k: round(v, 8) for k, v in rep.genome().items()}},
                        "members": [{"id": m.id, "fitness": round(m.fitness, 4),
                                     **{k: round(v, 8) for k, v in m.genome().items()}}
                                    for m in a.members]}
    half = proto["n_eras"] // 2
    return {
        "arm": arm, "seed": seed, "R": R, "L": L,
        **summary(probes, proto["checkpoints"][-1]),
        "ONLINE": round(float(np.mean(online[half:])), 4),
        "online": online, "tasks": world.tasks, "probes": probes, "diag": diag,
        "rep_ids": rep_ids, "lineage": a.lineage, "macs_per_era": macs,
        "budget_per_era": a.budget, "seconds": round(time.time() - t0, 2),
    }


def run_scratch(seed: int, R: int, proto: Dict) -> Dict:
    """The battery on fresh default networks: context for every arm, plus a
    description of the world (the skill tree) for figures."""
    t0 = time.time()
    world = SkillWorld(seed, R, proto["n_eras"])
    probes = {}
    for cp in proto["checkpoints"]:
        fresh = lambda kind, i, cp=cp: MLP(np.random.default_rng([seed, 6, cp, KINDS[kind], i]),
                                           lr=proto["lr"])
        probes[cp] = measure(world, cp, proto, fresh)
    return {"arm": "SCRATCH", "seed": seed, "R": R, "L": NO_LIFESPAN,
            **summary(probes, proto["checkpoints"][-1]), "probes": probes,
            "tasks": world.tasks, "world": world.describe(),
            "seconds": round(time.time() - t0, 2)}


def jobs(seeds: List[int], proto: Dict, arms: Optional[List[str]] = None) -> List[Tuple]:
    study_1b = proto.get("study") == "1b"
    arms = arms or (arms_1b.ARM_ORDER_1B if study_1b else ARM_ORDER)
    no_births = arms_1b.NO_BIRTHS if study_1b else ("IMMORTAL",)
    out = []
    for seed in seeds:
        for R in proto["regimes"]["novelty_interval"]:
            out.append((seed, "SCRATCH", R, NO_LIFESPAN))
            for arm in arms:
                lifespans = [NO_LIFESPAN] if arm in no_births else proto["regimes"]["lifespan"]
                if not study_1b and arm in ARMS and hasattr(ARMS[arm], "childhood"):
                    # a childhood must end before the next birth
                    lifespans = [L for L in lifespans if L > ARMS[arm].childhood]
                for L in lifespans:
                    out.append((seed, arm, R, L))
    return out


def _work(args):
    seed, arm, R, L, proto, meta = args
    rec = run_scratch(seed, R, proto) if arm == "SCRATCH" else run_one(seed, arm, R, L, proto)
    return {**meta, **rec, "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def fmt_line(rec: Dict) -> str:
    return (f"  {rec['arm']:8s} seed {rec['seed']} R={rec['R']} L={rec['L']:2d}  "
            f"knows {rec['FINAL_KNOWLEDGE']:.2f} (depth {rec['FINAL_DEPTH']:2d})  "
            f"frontier {rec['FINAL_FRONTIER']:.3f}  novel {rec['FINAL_NOVEL']:.3f}  "
            f"online {rec.get('ONLINE', float('nan')):.3f}  {rec['seconds']}s")


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
    ap.add_argument("--phase", required=True,
                    choices=["pilot", "confirmation", "smoke", "pilot_1b", "confirmation_1b", "smoke_1b"])
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--arms", default="")
    ap.add_argument("--procs", type=int, default=os.cpu_count() or 1)
    ap.add_argument("--protocol", default=PROTOCOL_PATH)
    ap.add_argument("--shard", default="0/1", help="i/n: run every n-th job starting at i")
    args = ap.parse_args(argv)

    proto = load_protocol(args.protocol)
    if args.phase.endswith("_1b") != (proto.get("study") == "1b"):
        sys.exit(f"phase {args.phase} does not match the protocol {args.protocol}")
    if args.phase.startswith("confirmation") and not proto.get("frozen"):
        sys.exit("the protocol is not frozen; confirmation seeds may not be run yet")
    meta = {"study": proto.get("study_name", STUDY), "phase": args.phase, "version": __version__,
            "code_commit": code_commit(), "protocol_hash": protocol_hash(proto),
            "numpy": np.__version__, "python": platform.python_version()}
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
                print(fmt_line(rec), flush=True)
    else:
        with open(path, "a") as f:
            for w in work:
                rec = _work(w)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                print(fmt_line(rec), flush=True)


if __name__ == "__main__":
    main()
