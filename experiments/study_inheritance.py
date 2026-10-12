"""Headline study: when does inherited experience help a population adapt, and
when does it trap the population in strategies that have become obsolete?

Three conditions, equal information budget where possible:
  none       descendants inherit no ancestral memory
  related    descendants inherit their parent's memory
  unrelated  descendants inherit equally-sized memory from a *different* lineage
             (controls for the amount of information, not its relevance)

The environment shifts partway through every run (arch viabilities change), so
memory formed before the shift can become stale. We measure survival after the
change (recovery_ratio = final / pre-shift population), the reproductive number
R, extinction, and how the evolved genome (notably memory_trust) ends up.

World rules are fixed for the duration of each run; only the scheduled shift
changes anything. Runs are reproducible from (config, seed).
"""

from __future__ import annotations

from sim.engine import EngineConfig

from . import records
from .runner import CONFIRMATION_SEEDS, DISCOVERY_SEEDS, run_condition

STUDY = "inheritance_adaptation"

BASE = EngineConfig(
    engine="rule-based",
    n_nodes=80,
    n_arch=4,
    n_founders=8,
    max_steps=120,
    max_population=600,
    shift_step=60,
    shift_magnitude=1.0,
)

CONDITIONS = {
    "none": {"inheritance": "none"},
    "related": {"inheritance": "related"},
    "unrelated": {"inheritance": "unrelated"},
}


def main() -> None:
    conn = records.connect()
    pools = [("discovery", DISCOVERY_SEEDS), ("confirmation", CONFIRMATION_SEEDS)]
    total = 0
    for pool_name, seeds in pools:
        for cond, overrides in CONDITIONS.items():
            ids = run_condition(
                conn, STUDY, cond, BASE, seeds, pool_name, overrides
            )
            total += len(ids)
            print(f"  {pool_name:>12} / {cond:<9} : {len(ids)} runs")
    print(f"Done. {total} immutable records written for study '{STUDY}'.")
    print("Next: python -m experiments.analysis  &&  python -m dashboard.generate")


if __name__ == "__main__":
    main()
