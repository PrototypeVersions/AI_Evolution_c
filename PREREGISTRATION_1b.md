# Pre-registration — Study 1b: What keeps the copying population able to learn?

Status: **draft, registered before any Study 1b run.** The hypotheses and
priors in §5 were written before any Study 1b code. The git commit that adds
this file is its timestamp. Changes made before the pilot go under
*Amendments before any run*, and changes after it under *Deviations*, both at
the end. Study 1 (`PREREGISTRATION_v2.md`) and its frozen protocol are not
changed.

## 0. Why there is a Study 1b

Study 1's most surprising confirmed result was H3c. **CLONE**, a population of
four that every L eras overwrites its two worst members with copies of its two
best, was the best arm in every condition at taking the next step. In the slow
world at era 120, its representative scored 93.5% and 94.3% on the FRONTIER
probe, against 74.7% for the immortal learner. We had predicted the opposite.
The population also had fewer dead units: 28% and 23%, against 43%.

CLONE differs from IMMORTAL in five ways at once, and Study 1 cannot tell them
apart:

1. **Updates (U).** Each member trains 200 steps per era; IMMORTAL trains 800.
   The total compute is equal, but each lineage has a quarter of the updates.
2. **Best of four (B).** The measured representative is the fittest of four
   networks. IMMORTAL is measured as it is.
3. **Starting settings (S).** CLONE's founders draw their learning rate (×⅓ to
   ×3 the default), weight decay (1e-6 to 1e-3) and initial weight scale (0.5
   to 2) from a prior. IMMORTAL uses the default learning rate, no weight decay
   and the default scale. At era 120, CLONE representatives had a median
   weight decay of 6e-5 to 1.3e-4 and a median learning rate of 1.8e-3 to
   2.8e-3.
4. **Learning-rate mutation (M).** Each copy's learning rate is multiplied by
   0.8 or 1.25, so the learning rate can evolve.
5. **Copying (C).** Weights and optimiser state of the best members replace
   the worst, every L eras. Copying does not rejuvenate a network: the copy
   has the same weights, the same optimiser state and the same history of
   updates as its parent. Any benefit of copying must come from repeated
   selection among lineages.

A secondary probe at the default learning rate (Study 1, deviation 3) showed
that most of the lead survives without CLONE's own learning rate (85.1% and
89.7%). That rules out only the learning rate at test time, not U, B, S, M or
C during the run.

Study 1b separates the five. Its main question is whether **copying itself**
helps, because that is what would make "reproduction keeps a mind able to
learn" a real finding rather than a side effect of training each network less.

## 1. The question

> At equal compute, in the Study 1 staircase world, which of the five
> differences explains why a weight-copying population takes the next step
> better than a single continually trained network? In particular, does
> copying the best members' weights help, beyond giving each network fewer
> updates, measuring the best of four, and varying the learning settings?

## 2. The world, the learner and the measurements

These are exactly as in Study 1 (`PREREGISTRATION_v2.md` §2–§5, with
deviations 1–3, and `learners/protocol.json`): the staircase world with
R ∈ {2, 6}, 120 eras, the 32 → 128 → 128 → 4 MLP with Adam, 800 steps of 32
examples per era of budget, and the same probes at eras 20–120.

## 3. The arms

All population arms have four members and use Study 1's fitness (accuracy over
the last 20 training batches) and representative (the fittest member). No arm
ever spends more than the per-era budget.

| Arm | Networks | Steps per network per era | Starting settings | Copies best into worst every L eras | Learning-rate mutation | Differs from the arm above by |
|---|---|---|---|---|---|---|
| IMMORTAL | 1 | 800 | default | — | — | (Study 1 baseline) |
| QUARTER | 1 | 200 (¾ of the budget unspent) | default | — | — | U |
| SOLO4 | 4 | 200 | default | no | — | B |
| COPY4 | 4 | 200 | default | yes | no | C |
| SOLO4P | 4 | 200 | prior | no | — | S (vs SOLO4) |
| COPY4P | 4 | 200 | prior | yes | no | C (vs SOLO4P) |
| CLONE | 4 | 200 | prior | yes | yes | M (vs COPY4P) |

- **QUARTER** is a control, not a strategy: it deliberately leaves three
  quarters of the budget unspent, so that the effect of fewer updates can be
  seen on its own.
- **Copying** in COPY4 and COPY4P is CLONE's copying without the mutation:
  at each birth era the two worst members are replaced by copies of the two
  best (weights and Adam state), and the learning rate is copied unchanged.
- **Matched founders.** Arms that differ only by copying or mutation start
  from identical founders and see an identical data stream until their first
  birth era. SOLO4 and COPY4 share founders; SOLO4P, COPY4P and CLONE share
  founders and founder settings; IMMORTAL and QUARTER share their initial
  network. This makes the key comparisons paired at the level of the
  networks, not only the worlds.
- IMMORTAL, QUARTER, SOLO4 and SOLO4P do not depend on L, so one run per
  world serves both lifespans, and in the analysis each of their comparisons
  among themselves counts **once per world**, not once per lifespan.
- IMMORTAL and CLONE are rerun on the new seeds, so every comparison is
  paired within Study 1b. Their code is unchanged from Study 1.

## 4. Outcomes

**Primary outcomes** (per run):
1. `FINAL_FRONTIER`: mean FRONTIER at era 120 (800-step probe on each of the
   next six skills; 50% is guessing).
2. `FINAL_NOVEL`: mean NOVEL at era 120 (100-step probe on six reserved
   two-bit skills).

**Secondary outcomes** (reported for every arm; tested only where named):
- `FRONTIER_LEARNED`: the share of next-skill probes that reach ≥ 90%
  accuracy at era 120. FRONTIER probes mostly end near 50% or near 100%, but
  not always, so the share fully learned is reported next to the mean.
- `ONLINE` (mean current-task accuracy, eras 61–120), `FINAL_KNOWLEDGE`,
  `FRONTIER_FIXED_LR`, `NOVEL_FIXED_LR`, dead units and weight norm at every
  checkpoint, and the representative's learning settings.

## 5. Hypotheses and predictions (written before any Study 1b code or run)

The priors are my honest beliefs. They are informed by Study 1's
confirmation results but by no Study 1b data.

| # | Hypothesis | Comparison | Conditions | Prediction | Prior |
|---|---|---|---|---|---|
| B1 | **Copying helps, with default settings** | `FINAL_FRONTIER`: COPY4 > SOLO4 | 4 (R × L) | lean yes | 55% |
| B2 | **Copying helps, with varied settings** | `FINAL_FRONTIER`: COPY4P > SOLO4P | 4 | lean yes | 55% |
| B3 | Fewer updates keep the next step open | `FINAL_FRONTIER`: QUARTER > IMMORTAL | 2 (R) | yes | 60% |
| B4 | Measuring the best of four helps | `FINAL_FRONTIER`: SOLO4 > QUARTER | 2 | lean yes | 60% |
| B5 | Varied starting settings help | `FINAL_FRONTIER`: SOLO4P > SOLO4 | 2 | lean yes | 55% |
| B6 | Learning-rate mutation helps | `FINAL_FRONTIER`: CLONE > COPY4P | 4 | lean yes | 55% |
| B7 | Study 1's H3c replicates | `FINAL_FRONTIER`: CLONE > IMMORTAL | 4 | yes | 90% |
| B8 | Fewer updates preserve plasticity | `FINAL_NOVEL`: QUARTER > IMMORTAL | 2 | yes | 70% |
| B9 | Copying preserves plasticity | `FINAL_NOVEL`: COPY4 > SOLO4 | 4 | uncertain | 50% |

Reasoning behind the priors:
- **B1 and B2.** Copying alone cannot make a network more plastic, because a
  copy is identical to its parent. But fitness is current-task accuracy, and
  in a world that keeps adding skills, lineages that still learn quickly
  should have higher fitness when a new skill arrives. Repeated copying would
  then keep selecting for lineages that stay able to learn, compounding over
  generations. Without copying, selection happens only once, when the
  representative is picked. I think this is slightly more likely than not.
- **B3.** Loss of plasticity in Study 1 grew with training, and QUARTER
  trains a quarter as much. Against it, QUARTER may fall behind the staircase
  in the fast world (400 steps per new skill), so its parents may be less well
  learned.
- **B7.** Study 1 found the effect in all four conditions with large margins.

## 6. Design of the runs

- **Conditions:** R ∈ {2, 6} × L ∈ {5, 20}, as in Study 1. COPY4, COPY4P and
  CLONE run at both lifespans. The other arms run once per world.
- **Pilot:** seeds 300–304 (exploratory). It is used only to find bugs, check
  that matched arms are identical until their first birth, and check runtime.
- **Confirmation:** seeds 8000–8029, which no code has run. They are run only
  after `learners/protocol_1b.json` is frozen.
- Per seed: per world, one SCRATCH reference, one run each of IMMORTAL,
  QUARTER, SOLO4 and SOLO4P, and two each (L = 5, 20) of COPY4, COPY4P and
  CLONE: 22 runs per seed, 660 in all.
- Every run writes an immutable record with the code commit, the protocol
  hash, numpy and Python versions, and all outcomes and trajectories.

## 7. Analysis plan

- **Tests.** As in Study 1: per-seed paired differences, a two-sided sign-flip
  permutation test, a 95% bootstrap CI and paired Cohen's *d_z*.
- **Family.** 28 members: B1, B2, B6, B7 and B9 in each of the four
  conditions (20), and B3, B4, B5 and B8 in each world (8). Holm–Bonferroni
  across all 28 at α = 0.05.
- **Verdicts.** SUPPORTED, REVERSED or NOT SUPPORTED, as in Study 1.
- **Decomposition** (descriptive, not tested). In each condition, the
  CLONE − IMMORTAL gap in `FINAL_FRONTIER` is split along the path
  IMMORTAL → QUARTER → SOLO4 → SOLO4P → COPY4P → CLONE. The order of the path
  is fixed here and the split depends on it, so it is reported as one
  decomposition, not as the only one.
- **What we will conclude.**
  - "Copying itself helps the next step" is claimed for a condition only if
    B1 or B2 is SUPPORTED there.
  - If neither B1 nor B2 is SUPPORTED in any condition, the paper reports
    that Study 1's H3c is not explained by copying, and names whichever of
    B3, B4, B5 and B6 are supported.
  - A REVERSED B1 or B2 means copying hurts and is reported as such.
- **Exploratory, labelled as such.** Within SOLO4P, which starting settings
  (learning rate, weight decay, initial scale) go with a high FRONTIER.

## 8. Limits

The same as Study 1: small networks and synthetic parity skills. Study 1b
explains one Study 1 result in this world; it does not test whether the result
generalises to other architectures. QUARTER is a control that wastes compute
on purpose and is not a candidate strategy. Starting settings are varied
together, so B5 cannot say which setting matters.

## 9. Boundaries

As in Study 1: small classifiers on random bit vectors, trained in-process,
with no networking, no external model and no code generation. See
[SAFETY.md](SAFETY.md).

## Amendments before any run

None yet.

## Deviations

None yet.
