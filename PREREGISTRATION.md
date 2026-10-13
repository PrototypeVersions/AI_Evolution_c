# Pre-registration — Study 1: Should a learning machine reproduce, or live forever?

Status: **registered before any code for this study was written or run.**
The git commit that adds this file is its timestamp. Anything changed later is
listed under *Deviations* at the end, with the reason, and never edited in place.

## 1. The question

Living things improve across generations because individuals die and
descendants inherit something from them. Software does not have to die: one
network can, in principle, keep learning forever. So for an artificial learner
the choice is real:

> **Under a fixed training-compute budget, on a never-ending stream of learning
> problems, does a learner improve more by living forever (one network trained
> continuously) or by reproducing (handing over to descendants), and which
> inheritance channel — weights, behaviour, or only learning settings — matters?**

Why either answer is plausible:

- *For reproduction.* Networks trained for a long time on changing problems
  gradually lose the ability to learn new ones ("loss of plasticity": Dohare et
  al., *Nature* 2024; Lyle et al., ICML 2023; Ash & Adams, NeurIPS 2020;
  Nikishin et al., ICML 2022). A fresh descendant starts with full plasticity.
  Passing knowledge through a narrow channel to a fresh network can make it
  *better* than its parent (born-again networks, Furlanello et al., ICML 2018;
  iterated relearning, Igl et al., ICLR 2021; iterated learning, Ren et al.,
  ICLR 2020; fortuitous forgetting, Zhou et al., ICLR 2022). A population
  explores several learning settings at once, and selection keeps what works
  (population-based training, Jaderberg et al. 2017; Hinton & Nowlan 1987).
- *Against.* Birth costs compute (teaching, or relearning from scratch), copies
  can inherit their parents' problems, and a population splits a fixed budget
  so each member learns less.

What is new here is the head-to-head: every life history gets **exactly the
same training compute**, on the **same stream**, and is measured separately on
**reusing old knowledge** and **learning genuinely new things**.

## 2. The world: a stream of skill problems

- **Inputs.** `x` is 32 random bits (±1), freshly sampled for every batch, so
  there is no fixed dataset to memorise.
- **Skills.** A per-seed library of 48 skills. Skill *k* is the XOR (product)
  of a fixed random pair of input bits, all pairs distinct. Detecting a skill
  requires a hidden unit, so a learned skill is reusable knowledge.
  40 skills are *stream skills*; 8 are *reserved* and never appear in the
  stream.
- **Tasks.** A task is an ordered pair of distinct skills `(a, b)`; the label is
  `2·[skill a] + [skill b]`, one of 4 classes (chance = 25%).
- **The stream.** Time is divided into **eras**; each era presents one task.
  A new stream skill is introduced every **R** eras. Each era's task pairs the
  newest skill with a random earlier one with probability ½, and otherwise is a
  random pair of introduced skills. A fixed random 20% of ordered skill pairs
  are **held out** and never appear in the stream (they are probe material).
- **Same world for everyone.** One seed fixes the skill library, the held-out
  pairs and the task sequence; every arm runs on every seed, so comparisons are
  paired.
- **Length.** 120 eras per run.

## 3. The learner

A multilayer perceptron, 32 → 128 → 128 → 4, ReLU, He initialisation, Adam,
batch 32, cross-entropy. The default learning rate and the steps per era are
fixed by the calibration rules in §7 using fresh networks only.

**Compute accounting.** Compute is counted in multiply-accumulates (MACs). A
training example costs 3× the forward MACs; a forward-only example (teaching
or evaluation used *by an arm*) costs 1×. Every arm gets the same budget per
era, `B = S × 32 × 3 × forward MACs`, where `S` is the immortal learner's steps
per era. Unspent budget is not carried over. Measurement (probes, evaluation
sets) is outside the budget and identical for all arms.

## 4. The arms (life histories)

All arms use the same network shape. "Lifespan" **L** is the number of eras
between births.

| Arm | Population | What happens every L eras | What is inherited |
|---|---|---|---|
| **IMMORTAL** | 1 | nothing; trains forever | — |
| **RESET** | 1 | shrink-and-perturb: weights ×0.8 plus 0.1 × fresh initial weights (Ash & Adams 2020) | everything, partly scrambled |
| **RESTART** | 1 | replaced by a fresh network | nothing |
| **TEACH** | 1 | a fresh child spends the first half of that era's budget matching the parent's hidden activations (mean squared error) and output distribution (KL) on random inputs, teacher forward passes counted; then the parent retires | behaviour, not weights |
| **CLONE** | 4 | bottom 2 members are overwritten with copies of the top 2 (weights and optimiser state), learning rate ×0.8 or ×1.25 | weights and learning settings (Lamarckian) |
| **GENES** | 4 | all members replaced by fresh networks whose learning settings come from the top 2, mutated | learning settings only (Darwinian) |
| **RANDOM** | 4 | all members replaced by fresh networks with freshly drawn learning settings | nothing (random search) |

- Population members train in parallel on the current task and each get ¼ of
  the era budget.
- **Fitness** for selection is a member's accuracy over its last 20 training
  batches. It is already computed during training, so selection costs nothing.
- **Learning settings** (the genome) are learning rate, weight decay and
  initial weight scale.
  - The prior is: learning rate log-uniform within ×3 of the default; weight
    decay log-uniform on [1e-6, 1e-3]; initial scale uniform on [0.5, 2] × He.
  - Mutation multiplies the learning rate and weight decay by 0.8 or 1.25, and
    adds ±0.1 to the initial scale.
  - Population arms draw their initial members from the prior.
  - Single-network arms use the defaults with no weight decay.

## 5. Measurements

- **Online accuracy.** At the end of each era, accuracy of the arm's
  representative on 2,000 fresh inputs of the current task.
  - For a single-network arm, the representative is that network.
  - For a population arm, it is the member with the best fitness.
- **Probes** at eras 20, 40, 60, 80, 100 and 120. A copy of the representative
  is fine-tuned for **K** steps (fresh Adam, its own learning rate) on each probe
  task, then scored on 2,000 fresh inputs. The copy is discarded, so probes
  never affect the run.
  - **REUSE probe:** 6 held-out pairs of skills already introduced. This
    measures recombining old knowledge.
  - **NOVEL probe:** 6 pairs of two *reserved* skills, which the stream never
    shows. This measures plasticity: learning genuinely new skills.
  - **Scratch reference:** the same probes run on a fresh default network,
    reported alongside for context.
- **Diagnostics** (secondary): fraction of dead ReLU units, weight norm,
  learning settings over time, and compute actually spent.

**Primary outcomes** (per run):
1. `FINAL_REUSE` is the mean REUSE probe accuracy at era 120.
2. `FINAL_NOVEL` is the mean NOVEL probe accuracy at era 120.
3. `ONLINE` is the mean online accuracy over eras 61–120.

## 6. Hypotheses and predictions (written before running anything)

Confidence numbers are my honest prior; they are recorded so that surprises are
visible.

| # | Hypothesis | Comparison (per regime) | Prediction | Prior |
|---|---|---|---|---|
| H1 | Plasticity loss occurs in this world | IMMORTAL NOVEL probe at era 120 < at era 20 | yes | 65% |
| H2 | Inherited knowledge gets reused | `FINAL_REUSE`: IMMORTAL > RESTART; CLONE > GENES | yes | 85% |
| H3 | **Reproduction with inheritance beats immortality** | `FINAL_NOVEL`: TEACH > IMMORTAL, and `FINAL_REUSE`: TEACH not worse than IMMORTAL by more than 5 points | TEACH: yes | 50% |
| H3b | Weight copies inherit plasticity loss | `FINAL_NOVEL`: CLONE > IMMORTAL | no | 60% that it is *not* better |
| H4 | Reproduction is more than a reset | `FINAL_NOVEL` and `ONLINE`: TEACH > RESET | lean no | 40% |
| H5 | Selection on learning settings helps | `ONLINE`: GENES > RANDOM | yes | 60% |
| H6 | Splitting compute is costly | `ONLINE`: IMMORTAL > each of CLONE, GENES, RANDOM | yes | 70% |

The headline is H3, in each regime: when does reproducing beat living forever,
and when does it not? Either answer is a result.

## 7. Calibration (pilot), decided only from fresh networks

These choices are made by looking at fresh networks learning single tasks,
never at differences between arms:

1. **Default learning rate.** The value in {3e-4, 1e-3, 3e-3} with which a
   fresh network reaches 90% accuracy on random stream tasks in the fewest
   steps (median over 20 tasks).
2. **Steps per era S.** The smallest value in {100, 200, 300, 500, 800} with
   which a fresh network reaches ≥ 90% accuracy within one era on ≥ 90% of 20
   random tasks.
3. **Probe steps K.** The value in {25, 50, 100, 200} that puts the fresh
   network's mean NOVEL probe accuracy closest to 60%. This leaves room to
   detect both gains and losses.

The calibrated values are written to `learners/protocol.json` and committed
before any confirmation seed is run.

## 8. Design of the runs

- **Regimes** (a 2 × 2 grid, all reported):
  - novelty interval R ∈ {2, 6} eras per new skill;
  - lifespan L ∈ {5, 20} eras.
- **Pilot:** seeds 100–109, exploratory. It is used for calibration, to find
  bugs, and to check the runtime. Pilot results will be shown and labelled as
  exploratory.
- **Confirmation:** seeds 7000–7029 (30 worlds per regime). Never run before
  `protocol.json` is frozen.
- Every run writes an immutable record (code commit, protocol hash, seed, arm,
  regime, all outcomes), as the lab's other studies do.

## 9. Analysis plan

- **Unit.** One seed (world). Every arm runs on every seed, so tests use
  per-seed paired differences.
- **Test.** A two-sided paired sign-flip permutation test with 10,000
  permutations.
- **Effect size.** Mean difference in accuracy points with a 95% bootstrap CI
  (10,000 resamples), plus paired Cohen's *d_z*.
- **Multiple comparisons.** The confirmatory family is every comparison in §6
  in every regime: 9 comparisons × 4 regimes = 36. Holm–Bonferroni at α = 0.05
  is applied across all 36.
  - H1: 1 comparison.
  - H2: 2 comparisons.
  - H3: 1 family member. Both parts must pass, and its p-value is the larger
    of the two.
  - H3b: 1 comparison.
  - H4: 2 comparisons.
  - H5: 1 comparison.
  - H6: 1 family member. All three parts must pass, and its p-value is the
    largest of the three.
- **Non-inferiority** in H3's reuse condition is a one-sided sign-flip test
  that TEACH − IMMORTAL > −5 points.
- **Reporting.** Everything is reported: supported, not supported and
  reversed.
  - Each figure shows every seed, not only the mean.
  - Exploratory analyses are labelled as exploratory.

## 10. What would change my mind, and what this cannot show

- If no arm ever loses plasticity (H1 fails everywhere), the main mechanism for
  reproduction to help is absent in this world. That is itself informative, and
  the next step would be a harder world.
- These are small networks on synthetic problems. A positive result here is
  evidence about a mechanism, not about large models. Generality is the next
  study: the same arms with a small transformer on sequence problems, then
  fine-tuned language models.

## 11. Boundaries

The learners are small classifiers on random bit vectors, trained in-process.
There is no networking, no external model, and no code generation. See
[SAFETY.md](SAFETY.md).

## Deviations

*(none yet)*
