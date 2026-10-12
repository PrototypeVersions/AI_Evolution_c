"""The long run: one persistent, multi-habitat world that keeps evolving.

Each advance loads the last checkpoint, runs more ticks, and saves again, so the
same population continues across days. Like the rest of the lab it is a closed
simulation: habitats, migration, and agents are in-memory records only. See
SAFETY.md.
"""
