# Pre-registration v2 — Study 1: Should a learning machine reproduce, or live forever?

Status: **registered before the v2 world's calibration or pilot was run.**
The git commit that adds this file is its timestamp. It replaces
[v1](PREREGISTRATION.md) for everything that follows. v1 stays unchanged as a
record, with its deviations. Later changes go under *Deviations* at the end.

## 0. Why there is a v2

The v1 pilot (51 runs on practice seeds, kept in
`learners/results/pilot_v1_probe_flaw.jsonl`) showed that the v1 world was the
wrong test of the question, for two reasons that do not depend on which arm
"wins".

1. **The v1 world never rewarded accumulated knowledge.** Every task was learnable
   from scratch within one era: the v1 calibration rule required exactly that.
   A learner that started over each generation lost nothing. Probes also
   showed little reuse even for the immortal learner, because old skills were
   overwritten by newer ones. A world where starting over costs nothing cannot
   tell us whether inheritance is worth having.
2. **Its probes mixed up two things.** They measured both what the hidden
   layers knew and how hard the old output layer was to overwrite (v1
   deviation 3).

The v1 pilot also showed one thing worth carrying forward. With a new skill
every 2 eras, the immortal learner's accuracy on the stream fell from about
98% (eras 1–20) to about 60% (eras 101–120), on the 2 seeds that ran.
Learners restarted every 5 eras stayed at 97–99%. With a new skill every 6
eras, the decline was smaller, to 86–92%. This is the known loss-of-plasticity
effect, and it shows the mechanism is present in these small networks.

**The fix is a world where knowledge compounds.** Skills are parities of input
bits, and each new skill extends an existing one by one bit. Gradient descent
finds high-order parities very hard to learn from scratch but easy to learn one
bit at a time: the "staircase" property (Abbe, Boix-Adserà & Misiakiewicz, COLT
2022).

Before writing this plan I checked the property on 24 exploratory runs
(`paper/NOTEBOOK.md`, 2026-10-13). At learning rate 3e-3, fresh networks
failed to learn a 5- or 6-bit parity within 4,000 steps in 5 of 6 tries; the
sixth took 2,500 steps. Networks that climbed one bit at a time needed 75–300
steps per step.

So now both forces are present:
- **Accumulation** favours keeping knowledge: an immortal learner, or any
  inheritance.
- **Plasticity loss** favours a fresh start.

The question is which life history wins when both matter.

## 1. The question (unchanged)

> Under a fixed training-compute budget, on a never-ending stream of learning
> problems, does a learner improve more by living forever or by reproducing,
> and which inheritance channel matters?

In the v2 world, "improve" has a concrete meaning: **climbing**, which means
coming to command deeper skills that cannot be learned from scratch.

## 2. The world: a staircase of skills

- **Inputs.** `x` is 32 random bits (±1), freshly sampled for every batch.
- **Skills.** A skill is the parity (product) of a set of input bits.
  - At era 0, 4 random two-bit skills exist.
  - Every **R** eras one new skill appears. It extends an existing skill by one
    random extra bit. The parent is the newest skill with probability ½, and
    otherwise a uniformly random existing skill. This gives a tree with a main
    trunk and branches.
  - A skill never covers more than 16 bits, and supports are unique.
- **Tasks.** Each era presents one task: an ordered pair of distinct
  introduced skills `(a, b)` with label `2·[a] + [b]` (4 classes).
  - With probability ½, one member of the pair is the newest skill.
  - Otherwise both are uniformly random. The partner is uniformly random
    either way.
  - Which skill comes first is random.
- **Probe material.**
  - 8 reserved two-bit skills never appear in the stream.
  - Future skills (not yet introduced) are also used for probing.
- **Same world for everyone.** One seed and R fix the skill tree and the task
  sequence. Every arm runs on every seed, so comparisons are paired.
- **Length.** 120 eras per run.

## 3. The learner (unchanged from v1)

An MLP 32 → 128 → 128 → 4 with ReLU, He initialisation, Adam, batch 32,
cross-entropy and numpy only. Compute is counted in multiply-accumulates.
- A training example costs 3× the forward pass.
- A forward-only example used by an arm costs 1×.
- Every arm gets the same budget per era: `S × 32 × 3 × forward MACs`.
- Measurement is outside the budget and identical for every arm.

## 4. The arms

These are as in v1 (seven arms; lifespan **L** = eras between births;
population arms split the budget four ways; fitness is accuracy over the last
20 training batches). There is one change.

- **TEACH** (changed). A fresh child spends the first half of the birth era's
  budget learning to reproduce its parent's **last hidden layer** (normalised
  mean squared error) and **output distribution** (KL), on random inputs.
  Teacher forward passes are counted. Then the parent retires.
  - In v1 every hidden layer was matched. That pins the child's first layer to
    the parent's weights, which is close to copying them.
  - Matching only the last layer passes on *what the parent can compute*. The
    child still builds its own machinery for it.
  - This is closer to teaching than to cloning, and it separates TEACH from
    CLONE.

The other arms are unchanged: IMMORTAL, RESET (shrink-and-perturb ×0.8 + 0.1
fresh), RESTART, CLONE (PBT-style, 4 members), GENES (Darwinian, 4 members) and
RANDOM (random search, 4 members). The genome prior and mutations are as in v1.

## 5. Measurements

At eras 20, 40, 60, 80, 100 and 120, the arm's representative is measured.
That is the network itself, or for a population the member with the best
fitness.

- **KNOWLEDGE.** For every skill introduced so far, a linear readout is
  fitted to the last hidden layer and scored. The fit is ridge least squares
  on 4,000 random inputs, scored on 2,000 more, and nothing in the network
  is trained. A skill is *known* if it is decoded with ≥ 90% accuracy.
  - KNOWLEDGE is the share of introduced skills that are known.
  - DEPTH is the highest degree (bit count) among known skills.
- **FRONTIER.** This measures the ability to take the next step. The probe
  uses the next 6 skills the stream *will* introduce whose parent is already
  introduced. For each, a copy of the representative gets a fresh output layer
  (identical for every arm) and fresh Adam. It is fine-tuned for **K** steps on
  that single skill (labels 0/1), then scored on 2,000 fresh inputs. The copy
  is discarded.
- **NOVEL.** This measures plasticity. It is the same procedure on 6 reserved
  two-bit skills.
- **ONLINE.** The representative's accuracy on the current task at the end of
  every era (2,000 fresh inputs).
- **SCRATCH reference.** The same battery on fresh networks, reported for
  context.
- **Diagnostics** (secondary): dead ReLU units, weight norm, learning
  settings, the lineage of every birth, and the per-skill readout accuracies
  (the "skill map").

**Primary outcomes** (per run):
1. `FINAL_FRONTIER`: mean FRONTIER at era 120.
2. `FINAL_KNOWLEDGE`: KNOWLEDGE at era 120.
3. `FINAL_NOVEL`: mean NOVEL at era 120.
4. `ONLINE`: mean online accuracy over eras 61–120.

## 6. Hypotheses and predictions (written before any v2 run)

The priors are my honest beliefs, updated by the v1 pilot where it applies
(noted).

| # | Hypothesis | Comparison (per regime) | Prediction | Prior |
|---|---|---|---|---|
| H1 | The immortal learner loses plasticity | IMMORTAL NOVEL at era 120 < at era 20 | yes | 80% (v1 pilot online decline) |
| H2a | Knowledge needs inheritance | `FINAL_KNOWLEDGE`: IMMORTAL > RESTART | yes | 90% |
| H2b | Weights carry knowledge; genes don't | `FINAL_KNOWLEDGE`: CLONE > GENES | yes | 90% |
| H3a | **Reproduction with teaching climbs better than immortality** | `FINAL_FRONTIER`: TEACH > IMMORTAL | yes | 50% |
| H3b | …and performs better on the stream | `ONLINE`: TEACH > IMMORTAL | yes | 50% |
| H3c | Weight copies don't escape plasticity loss | `FINAL_FRONTIER`: CLONE > IMMORTAL | no | 65% that it is *not* better |
| H4a | Teaching is more than a reset | `FINAL_FRONTIER`: TEACH > RESET | lean yes | 55% |
| H4b | | `ONLINE`: TEACH > RESET | lean yes | 55% |
| H5 | Selection on learning settings helps | `ONLINE`: GENES > RANDOM | yes | 55% |
| H6 | Splitting compute is costly | `ONLINE`: IMMORTAL > each of CLONE, GENES, RANDOM | yes | 75% |
| H7 | Teaching passes knowledge on | `FINAL_KNOWLEDGE`: TEACH > RESTART | yes | 85% |

The headline is H3a/H3b in each regime: when does teaching a successor beat
living forever, and when does it not? Either answer is a result. A map of
where each life history wins across the four regimes is the main figure.

## 7. Calibration (single learners only; never arm comparisons)

1. **Learning rate.** The value in {3e-4, 1e-3, 3e-3} with which fresh
   networks learn a pair of root skills to 90% in the fewest steps (median
   over 20 worlds).
2. **Steps per era S.** This is the climbing pace. One learner with unlimited
   compute follows the first 16 eras of a stream that adds a skill every
   era, training each task to 90%. S is the smallest value in
   {100, 200, 300, 500, 800} within which ≥ 90% of those eras finish. So a
   learner that has kept up can climb within an era's budget.
3. **Probe steps K.** The value in {25, 50, 100, 200} that puts fresh
   networks' mean NOVEL accuracy closest to 75%. Chance is 50%, so this
   leaves room both above and below.

Calibration uses seeds 1–20 and writes `learners/calibration.json` and
`learners/protocol.json`.

## 8. Design of the runs

- **Regimes:** a 2 × 2 grid, all reported.
  - Novelty interval R ∈ {2, 6} eras per new skill.
  - Lifespan L ∈ {5, 20} eras.
- **Pilot:** seeds 100–109 (exploratory). It is used to find bugs and check
  runtime. It is shown labelled as exploratory.
- **Confirmation:** seeds 7000–7029, which are never run before
  `protocol.json` is frozen. The code refuses to run them otherwise.
- Every run writes an immutable record with the code commit, protocol hash,
  numpy and Python versions, the seed, the arm, the regime, and all outcomes
  and trajectories.

## 9. Analysis plan

- **Tests.** Per-seed paired differences, a two-sided sign-flip permutation
  test (exact when 2^n ≤ 10,000), a 95% bootstrap CI and paired Cohen's *d_z*.
- **Family.** The confirmatory family has 11 members per regime × 4 regimes
  = 44.
  - Each of H1, H2a, H2b, H3a, H3b, H3c, H4a, H4b, H5 and H7 is one member.
  - H6 is one member whose p-value is the largest of its three comparisons,
    and it passes only if all three do.
  - Holm–Bonferroni is applied across all 44 at α = 0.05.
- **Verdicts.** SUPPORTED (significant, predicted direction), REVERSED
  (significant, opposite direction), or NOT SUPPORTED.
  - For H3c the prediction is "no", and the verdict refers to the
    hypothesis as written.
- **Reporting.** Everything is reported, figures show every seed, and
  exploratory analyses are labelled as exploratory.

## 10. Limits

These are small networks on synthetic parity problems. The staircase world
is chosen because it makes accumulation matter, and that is a deliberate
modelling choice: results tell us about this mechanism, not directly about
large models. The next study repeats the same arms with a small transformer on
sequence problems, then with fine-tuned language models.

## 11. Boundaries

The learners are small classifiers on random bit vectors, trained in-process.
There is no networking, no external model, and no code generation. See
[SAFETY.md](SAFETY.md).

## Deviations

1. **2026-10-13, during calibration, before any arm was run on the v2 world.**
   - **First calibration attempt.** It followed §7 at one new skill per era.
     The single climbing learner needed more than 3,000 steps in 16% of eras
     (`paper/exploratory/calibration_v2a.json`).
   - **Cause.** A new skill was presented on arrival only half the time, so
     its child often appeared before the skill had ever been practised. The
     learner then faced a two- or three-bit leap rather than a step.
   - **Fixes:**
     - every new skill is now part of the task in the era it arrives;
     - the climbing learner follows the grid's fastest pace (a new skill
       every 2 eras, 32 eras) instead of one per era, which no regime uses.
   - **Second calibration** (`learners/calibration.json`):
     - learning rate 3e-3 (median 125 steps for a fresh root pair);
     - K = 50 (fresh NOVEL accuracy 70%);
     - the climbing steps had a median of 300 and a 90th percentile of
       about 1,200 steps.
   - **S = 800.** No candidate met the 90% rule (100: 20%; 200: 38%; 300:
     54%; 500: 70%; 800: 83%). S was therefore set to the largest candidate,
     800, under which 83% of climbing eras finish within one era. The
     climbing learner itself trains continuously, so some of its slow eras
     probably reflect its own loss of plasticity.
