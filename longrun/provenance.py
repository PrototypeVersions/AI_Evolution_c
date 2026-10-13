"""Which code produced a record: the git commit, marked -dirty if uncommitted."""

from __future__ import annotations

import subprocess


def code_commit() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                             timeout=5, check=False).stdout.strip()
        if rev and rev != "HEAD":
            dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True,
                                   text=True, timeout=5, check=False).stdout.strip()
            return rev + ("-dirty" if dirty else "")
    except Exception:
        pass
    return "unknown"
