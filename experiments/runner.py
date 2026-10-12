"""Batch runner: run one EngineConfig across a list of seeds and persist records.

Seeds are drawn from disjoint pools so that effects can be *found* on one pool
and *confirmed* on another pool that was never used during discovery.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List

from sim.engine import EngineConfig, run_once

from .records import Record, connect, insert

# Disjoint, fixed seed pools. Discovery and confirmation never overlap.
DISCOVERY_SEEDS = list(range(1000, 1060))
CONFIRMATION_SEEDS = list(range(9000, 9060))


def run_condition(
    conn,
    study: str,
    condition: str,
    base_config: EngineConfig,
    seeds: List[int],
    seed_pool: str,
    overrides: Dict,
) -> List[str]:
    config = replace(base_config, **overrides)
    run_ids: List[str] = []
    for seed in seeds:
        result = run_once(config, seed)
        rec = Record(
            study=study,
            condition=condition,
            seed_pool=seed_pool,
            engine=config.engine,
            seed=seed,
            params=config.as_dict(),
            result=result.as_dict(),
        )
        run_ids.append(insert(conn, rec))
    return run_ids
