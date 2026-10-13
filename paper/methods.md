# Methods (draft)

*Draft written alongside the code. Values marked ⟨calibrated⟩ come from
`learners/protocol.json`; update if the protocol changes before freezing.*

## Overview

We compare seven *life histories* for a learning machine. Each one has the
same training compute and faces the same never-ending stream of learning
problems. Some live forever: one network is trained continuously. Others
reproduce: networks are periodically replaced by descendants that inherit
weights, behaviour or only learning settings. The stream is built so that
knowledge compounds: hard skills can only be learned by building on easier
ones. Both keeping knowledge and staying able to learn therefore matter.

## The staircase world

**Inputs and skills.** Inputs are vectors x ∈ {−1, +1}³², drawn uniformly and
freshly for every batch. A skill *k* is the parity
s_k(x) = ∏_{i∈S_k} x_i of a set S_k of input bits.

**The skill tree.**
- The world starts with four random two-bit skills.
- Every R eras one new skill appears. It extends a uniformly chosen existing
  skill by one random extra bit, so |S_child| = |S_parent| + 1.
- Skills are capped at 10 bits, and supports are unique.

Gradient descent learns sparse parities efficiently when each one can be
reached from an already learned parity by adding one variable (the
merged-staircase property; Abbe et al., 2022), but finds isolated high-order
parities very hard. In an exploratory check at learning rate 3e-3, fresh
networks failed to learn a 5- or 6-bit parity within 4,000 steps in 5 of 6
tries, while networks that climbed one bit at a time needed 75–300 steps per
step. At the study's learning rate of 1e-3, fresh networks failed in 4 of 6
tries (the other two needed about 3,800 steps) and climbing took 175–725 steps
per step (`exploratory/staircase_check.txt`). Accumulated knowledge is therefore
necessary to keep up.

**Tasks.**
- Each era presents one task: an ordered pair of distinct introduced skills
  (a, b), with the four-class label y = 2·[s_a > 0] + [s_b > 0].
- A new skill is always part of the task in the era it arrives. Afterwards
  the newest skill is included with probability ½, and partners are uniform.
- One seed and R determine the skill tree and the task sequence. Every arm
  runs on every seed, so arms are compared on identical worlds.

**Probe material.**
- Eight reserved two-bit skills never appear in the stream.
- Skills the stream has not yet introduced are used to probe the ability to
  take the next step.

## Learner and compute accounting

**The network.**
- Every individual is a multilayer perceptron, 32 → 128 → 128 → 4, with ReLU
  activations and He-normal initialisation (scaled by an initial-scale gene
  in population arms).
- It is trained with Adam (β = 0.9, 0.999), batch size 32 and
  cross-entropy. Weight decay is an L2 term on all parameters.
- The default learning rate is ⟨calibrated: 1e-3⟩.
- Backpropagation is hand-written in numpy and checked against finite
  differences.

**Compute** is counted in multiply-accumulate operations (MACs).
- A training example costs 3× the forward-pass MACs (20,992 per example).
- A forward-only example used by an arm (a teacher's pass) costs 1×.
- Every arm receives the same budget per era: S × 32 × 3 × 20,992 MACs, with
  S = ⟨calibrated: 800⟩.
- Unspent budget is not carried over. Rounding can leave an era at most one
  training step under budget, never over.
- Measurement is outside the budget and identical for all arms.

## Life histories (arms)

Let L be the lifespan in eras. All births happen at the start of eras that
are multiples of L.

- **IMMORTAL.** One network is trained on every era's task with the full
  budget.
- **RESET.** The same, but at each birth era the network is shrunk and
  perturbed: θ ← 0.8θ + 0.1θ_fresh, where θ_fresh is a fresh initialisation
  (Ash & Adams, 2020). Its optimiser state is reset.
- **RESTART.** At each birth era the network is replaced by a fresh one, and
  nothing is inherited.
- **TEACH.** At each birth era a fresh child spends half of that era's budget
  learning, on random inputs, to reproduce its parent.
  - The child matches the parent's output distribution (KL divergence) and
    its last hidden layer (mean squared error, normalised by the parent's
    mean squared activation).
  - The parent's forward passes are charged to the budget.
  - The parent then retires and the child trains on the stream with the
    rest of the era's budget. No weights are copied.
- **CLONE** (population of 4, Lamarckian). Each member trains on the
  current task with ¼ of the budget.
  - Fitness is the member's accuracy over its last 20 training batches,
    which costs nothing extra.
  - At each birth era the bottom two members are overwritten with copies of
    the top two (weights and optimiser state), with the learning rate
    multiplied by 0.8 or 1.25. This is population-based training
    (Jaderberg et al., 2017).
- **GENES** (population of 4, Darwinian). At each birth era all members are
  replaced by fresh networks. Their learning settings (learning rate,
  weight decay, initial weight scale) are inherited from the top two with
  mutation. Nothing learned is inherited.
- **RANDOM** (population of 4). At each birth era all members are replaced
  by fresh networks with freshly drawn learning settings. This is random
  search.

**Secondary arms: a longer childhood.** Added after the pilot showed that
half an era of teaching passes on little (see Deviation 3 of the
pre-registration). They are analysed in a separate family.
- **TEACH4 and TEACH16.** At each birth era a fresh child is born, but the
  parent keeps living. For the next 4 (or 16) eras the parent trains on the
  stream with half of each era's budget, and the child spends the other half
  learning to reproduce the parent exactly as in TEACH. Then the parent
  retires and the child takes over with the full budget.
- During a childhood the parent is the representative that is measured.
- TEACH16 is run only with lifespan 20, since a 16-era childhood does not
  fit in a 5-era life.

**Genome.**
- The prior draws:
  - the learning rate log-uniformly within ×3 of the default;
  - weight decay log-uniformly on [1e-6, 1e-3];
  - the initial scale uniformly on [0.5, 2].
- Mutation multiplies the learning rate and weight decay by 0.8 or 1.25, and
  adds ±0.1 to the initial scale.
- Single-network arms use the defaults with no weight decay.

## Measurements

At eras 20, 40, …, 120 the arm's representative is measured. This is the
network itself, or the fittest member of a population.

- **KNOWLEDGE.** For every skill introduced so far, a linear readout is fitted
  to the last hidden layer and scored.
  - The readout is ridge least squares on 4,000 random inputs, with a ridge
    of 1e-3 × the mean eigenvalue scale. It is scored on 2,000 fresh inputs.
  - A skill is *known* when it is decoded with ≥ 90% accuracy.
  - KNOWLEDGE is the share of introduced skills that are known. DEPTH is the
    largest known skill (bits).
  - Secondary knowledge measures: KNOWLEDGE averaged over all six
    checkpoints, and the share of the 8 most recently introduced skills that
    are known at era 120.
- **FRONTIER.** This uses the next six skills the stream will introduce whose
  parent is already introduced. For each, a copy of the representative gets
  a fresh output layer (identical across arms for a given probe) and fresh
  Adam state.
  - The copy is fine-tuned for one era's worth of steps (800) on that single
    skill (labels 0/1) with the network's own learning rate. FRONTIER thus
    asks whether the learner could take the next step within one era.
  - It is scored on 2,000 fresh inputs, then discarded.
  - In practice each probe either succeeds (near 100%) or stays at chance,
    so FRONTIER is close to 50% + ½ × the share of next skills learned.
- **NOVEL.** The same procedure on six reserved two-bit skills, with
  K = ⟨calibrated: 100⟩ steps. This measures plasticity, the ability to
  learn something unrelated to anything seen.
- **Probes at the default learning rate** (secondary). The NOVEL and
  FRONTIER probes repeated with the default learning rate instead of the
  network's own, so that the state of the weights can be separated from an
  evolved step size. For single-network arms they are identical to the
  primary probes.
- **ONLINE.** At the end of every era, the representative's accuracy on that
  era's task (2,000 fresh inputs).
- **Reference and diagnostics.** A fresh network is measured with the same
  battery for reference. Diagnostics are the fraction of dead hidden units
  (zero on 1,000 random inputs), the weight norm, each individual's genome,
  and the full lineage of births.

## Calibration

Calibration used single learners on worlds 1–8, never comparisons between
arms (`learners/calibration.json`).
- **S and the learning rate.** A continually trained network followed the
  first 40 eras at the fast pace (R = 2) with S steps per era. For each S in
  {200, 400, 800}, the learning rate in {3e-4, 1e-3, 3e-3} with the highest
  mean end-of-era accuracy was taken. S is the smallest value where that
  accuracy reaches 85%. This gave S = 800 with learning rate 1e-3, at 94%
  early accuracy.
- **K.** This was set so that fresh networks reach about 75% on NOVEL
  probes. K = 100 gave 67%.

## Design and analysis

**Design.**
- Two paces (R = 2 or 6 eras per new skill) × two lifespans (L = 5 or 20
  eras), for 120 eras.
- IMMORTAL does not depend on L, so one run per world serves both
  lifespans.
- Pilot seeds were 100–109. Confirmation seeds are 7000–7029, run only after
  the protocol is frozen.

**Analysis** (pre-registered).
- The primary outcomes are FRONTIER, KNOWLEDGE and NOVEL at era 120, and
  ONLINE averaged over eras 61–120.
- Comparisons use per-world paired differences with:
  - a two-sided sign-flip permutation test (exact when 2ⁿ ≤ 10,000,
    otherwise 10,000 random sign flips);
  - a 95% bootstrap confidence interval (10,000 resamples);
  - paired Cohen's d_z.
- The 44 pre-registered family members (11 hypotheses × 4 regimes) are
  corrected with Holm–Bonferroni at α = 0.05.
- A family member made of several comparisons passes only if all pass, and
  takes the largest p-value.

**Software and reproducibility.**
- Python 3.12 and numpy; no other dependencies for the experiment.
- Each run record stores the code commit, protocol hash, numpy and Python
  versions, the seed, and all trajectories.
- Runs execute in-process on synthetic data, with no network access.
