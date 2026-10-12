# AI_Evolution_c — Autonomous Ecology Lab

A **contained, abstract simulation** for studying population dynamics of
self-propagating agents: when inherited experience helps a population adapt,
and when it traps the population in strategies that have become obsolete.

> **This is a simulation, not a tool.** Everything happens inside an in-memory
> model. There is no networking, no device discovery, no exploitation, and no
> interaction with any real system. See [SAFETY.md](SAFETY.md). The agents'
> entire universe is a Python object; an action like `REPLICATE(node_17)` only
> instantiates another record inside the simulator.

## What this is (and is not)

This is agent-based evolutionary modelling, in the same family as a
branching-process or Lotka–Volterra simulation. It was motivated by public
discussion of distributed/edge-device AI replication, but it deliberately
studies only the **abstract science** of the question: under what conditions a
population of agents that pass information to their descendants sustains itself,
specializes, or collapses.

It does **not** reproduce, and cannot be extended within this repo to reproduce,
any of the real-world propagation steps (network scanning, gaining access to
machines, deploying software to hardware). The simulated action set is fixed and
operates only on simulated nodes.

## Design goals (from the project plan)

1. **Separate simulation from real models.** v0 is rule-based only. Every
   experiment record and dashboard view is labelled with its `engine` type so a
   rule-based result is never mistaken for a measurement of a real LLM. An
   optional LLM-controlled agent can be dropped into the *same* environment
   later for comparison; it is not part of v0.
2. **Make variation and selection explicit.** Agents carry a small heritable
   genome (decision parameters) plus inherited memory. Replication copies both
   with mutation, so there is heritable variation and differential reproductive
   success — real selection, not just note-passing.
3. **Keep discovery and confirmation separate.** The analysis layer finds
   *candidate* effects on one set of seeds, then confirms them on fresh,
   previously-unused seeds. Reports carry effect sizes, uncertainty, the number
   of comparisons made, and failed replications — never bare "confidence %".
4. **Preserve provenance from day one.** Every run writes an immutable record:
   code commit, simulator version, seed, full parameters, and summary metrics.
   Raw records go to a local SQLite database; summaries and figures are
   published to a static dashboard (`docs/`, GitHub Pages).

## The model in one paragraph

A **world** is a set of nodes, each with hidden properties (an `arch`
category, a difficulty, a reliability, a capacity). An **agent** lives on a
node and, each step, chooses from a fixed abstract action set
(`OBSERVE, MOVE, TEST, REPLICATE, RECORD, WAIT`). Whether a replication attempt
succeeds depends on the target's difficulty, the agent's genome, and whether the
agent's **inherited memory** contains a relevant, *still-accurate* observation
for that node's `arch`. The environment can **shift** partway through a run
(which archs are viable flips), which is where stale inherited memory can become
a trap. The measured outcome is the **reproductive number R** (mean successful
descendants per agent) plus population survival and how strategies change.

## The long run

Alongside the controlled studies there is one **persistent world** (`longrun/`)
that is never reset. Four habitats with different conditions (stable, drifting,
shock-prone, harsh) are linked by migration routes. Agents carry a small
behaviour *program* — an ordered list of `if <feature> <op> <threshold>:
<ACTION>` rules plus a default — and mutation can add, delete, and rewire rules,
so strategy structure itself evolves. Agents forage on limited, regrowing
resources, reproduce, test and share knowledge, move, migrate, and can steal
energy from neighbours on the same node.

A scheduled GitHub Action advances the world once a day from its checkpoint,
commits the new state, and republishes the viewer (`docs/world.html`). Advances
are deterministic: resuming from a checkpoint gives exactly the same history as
an uninterrupted run (tested). Any change to `longrun/config.json` after the
world starts is logged as an **intervention** and shown on the viewer.

A single long run is a sample of one: it is for watching and for generating
hypotheses. Claims about *why* something happens belong in controlled,
replicated studies (`experiments/`).

## Layout

```
sim/            study engine (world, agent, engine) — pure, deterministic given a seed
experiments/    immutable records (SQLite), batch runner, analysis, the studies
dashboard/      report generator: results -> docs/ data for GitHub Pages
longrun/        the persistent multi-habitat world, its checkpoint (state/), and the daily advance
docs/           static site for GitHub Pages: index.html (studies), world.html (the long run)
tests/          reproducibility, containment, and persistence tests
```

## Running it

No third-party packages are required — it runs on the Python 3 standard library.

```bash
# run the headline study (writes an immutable record per run to results.db)
python -m experiments.study_inheritance

# analyse: find candidate effects, then confirm on fresh seeds
python -m experiments.analysis

# regenerate the static dashboard under docs/ from the results database
python -m dashboard.generate

# advance the persistent world (continues from longrun/state/)
python -m longrun.advance --ticks 4000

# tests
python -m unittest discover -s tests
```

`results.db` (raw history) is git-ignored; the committed record of findings is
the summary JSON under `docs/` and the per-finding snapshots under
`experiments/snapshots/`.
