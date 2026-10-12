"""Immutable experimental records.

Every run writes one row that is never updated or deleted. A re-run is a new
row linked to the same study, so there is always an audit trail from any
published number back to the exact code, seed, and parameters that produced it.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional

from . import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id            TEXT PRIMARY KEY,
    created_at        REAL NOT NULL,
    study             TEXT NOT NULL,
    condition         TEXT NOT NULL,
    engine            TEXT NOT NULL,
    code_commit       TEXT NOT NULL,
    simulator_version TEXT NOT NULL,
    seed              INTEGER NOT NULL,
    seed_pool         TEXT NOT NULL,          -- 'discovery' | 'confirmation'
    R_lifetime        REAL,
    R_n               INTEGER,
    extinct           INTEGER,
    final_population  INTEGER,
    recovery_ratio    REAL,
    params_json       TEXT NOT NULL,
    result_json       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_study ON runs(study, condition, seed_pool);
"""


def code_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        rev = out.stdout.strip()
        if rev and rev != "HEAD":
            dirty = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=5, check=False,
            ).stdout.strip()
            return rev + ("-dirty" if dirty else "")
    except Exception:
        pass
    return "unknown"


@dataclass
class Record:
    study: str
    condition: str
    seed_pool: str
    engine: str
    seed: int
    params: Dict
    result: Dict

    def row(self) -> Dict:
        return {
            "run_id": uuid.uuid4().hex,
            "created_at": time.time(),
            "study": self.study,
            "condition": self.condition,
            "engine": self.engine,
            "code_commit": code_commit(),
            "simulator_version": self.result.get("simulator_version", "unknown"),
            "seed": self.seed,
            "seed_pool": self.seed_pool,
            "R_lifetime": self.result.get("R_lifetime"),
            "R_n": self.result.get("R_n"),
            "extinct": 1 if self.result.get("extinct") else 0,
            "final_population": self.result.get("final_population"),
            "recovery_ratio": self.result.get("recovery_ratio"),
            "params_json": json.dumps(self.params, sort_keys=True),
            "result_json": json.dumps(self.result, sort_keys=True),
        }


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert(conn: sqlite3.Connection, record: Record) -> str:
    row = record.row()
    cols = ",".join(row.keys())
    placeholders = ",".join(["?"] * len(row))
    conn.execute(f"INSERT INTO runs ({cols}) VALUES ({placeholders})", list(row.values()))
    conn.commit()
    return row["run_id"]


def fetch(
    conn: sqlite3.Connection,
    study: str,
    condition: Optional[str] = None,
    seed_pool: Optional[str] = None,
) -> List[sqlite3.Row]:
    q = "SELECT * FROM runs WHERE study = ?"
    args: List = [study]
    if condition is not None:
        q += " AND condition = ?"
        args.append(condition)
    if seed_pool is not None:
        q += " AND seed_pool = ?"
        args.append(seed_pool)
    return list(conn.execute(q, args))


def studies(conn: sqlite3.Connection) -> List[str]:
    return [r["study"] for r in conn.execute("SELECT DISTINCT study FROM runs ORDER BY study")]
