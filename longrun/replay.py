"""Rebuild the world's record by replaying it from genesis, and verify it.

    python -m longrun.replay            # verify only
    python -m longrun.replay --rewrite  # verify, then regenerate history/events/meta

The world is deterministic, so re-running it from its seed to the checkpoint's
tick must reproduce the checkpoint exactly. This is both an audit (the published
record really follows from the rules and the seed) and the way new observers
(for example the strategy family tree) are backfilled over the world's whole
past without touching how it evolved. Only supported while the world has had no
interventions; with interventions the replay would need each config in turn.
"""

from __future__ import annotations

import argparse
import json
import os
import time

from experiments.records import code_commit

from . import advance as adv


def replay(rewrite: bool = False) -> dict:
    with open(adv.CONFIG) as fh:
        cfg = json.load(fh)
    with open(adv.META) as fh:
        old_meta = json.load(fh)
    if old_meta["interventions"]:
        raise SystemExit("Replay is not supported after interventions.")
    checkpoint = adv._read_gz(adv.STATE)
    target = checkpoint["tick"]
    commit = code_commit()

    started = time.time()
    world, meta, obs = adv.genesis(cfg)
    while world.tick < target:
        world.step()
        obs.after_tick()

    same_state = json.dumps(world.to_state(), sort_keys=True) == json.dumps(checkpoint, sort_keys=True)
    old_events = adv._read_jsonl(adv.EVENTS)
    same_events = old_events == obs.new_events
    report = {"tick": target, "state_matches": same_state, "events_match": same_events,
              "events": len(obs.new_events), "seconds": round(time.time() - started, 1)}
    if not same_state:
        raise SystemExit(f"Replay diverged from the checkpoint at tick {target}: {report}")

    if rewrite:
        for key in ("created_at", "advances", "interventions", "config_hash"):
            meta[key] = old_meta[key]
        meta["replays"] = old_meta.get("replays", []) + [
            {"at": adv._now(), "tick": target, "commit": commit, "state_matches": same_state,
             "events_match": same_events}]
        for path, rows in ((adv.HIST_HAB, obs.history["habitat"]), (adv.HIST_WORLD, obs.history["world"]),
                           (adv.HIST_SHAPES, obs.history["shapes"]), (adv.EVENTS, obs.new_events)):
            if os.path.exists(path):
                os.remove(path)
            adv._append_jsonl(path, rows)
        with open(adv.META, "w") as fh:
            json.dump(meta, fh, separators=(",", ":"))
        adv.publish(world, meta, cfg, commit)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Replay the world from genesis and verify it.")
    ap.add_argument("--rewrite", action="store_true", help="regenerate history, events and meta")
    print(json.dumps(replay(ap.parse_args().rewrite)))


if __name__ == "__main__":
    main()
