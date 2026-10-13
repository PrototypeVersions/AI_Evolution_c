# Lab notebook

A dated record of decisions, findings and mistakes, kept so the paper can be
written from it. Times are UTC. The newest entry is at the bottom. Entries are
never rewritten; corrections are new entries.

## 2026-10-12 — Origins

- **Starting point.** The project began from a discussion of reports about AI
  systems replicating themselves. The aim is to study AI replication, change
  and improvement safely: a closed simulation with no networking and no real
  machines (see `SAFETY.md`).
- **Lab v0** (PR #1). This was a rule-based simulator of agents with
  inherited memory, run in a discovery-then-confirmation pipeline.
  - First study ("inheritance under environment shift", 360 runs): 0 of 6
    comparisons supported on confirmation seeds.
  - Known flaw: the "unrelated memory" control did not isolate relevance,
    because viability was global.
  - An early pattern ("unrelated memory recovers best") did not replicate on
    fresh seeds.
- **The long run** (PR #2). This is a persistent four-habitat artificial-life
  world with evolvable rule-list programs, advanced daily by GitHub Actions
  and replayable from genesis. Things seen, which are observations rather
  than findings:
  - migration evolved;
  - the harsh habitat needed 17 failed colonisations before a population held;
  - conditional stealing rose to about 30% of actions in one habitat;
  - one founder lineage replaced the rest.

## 2026-10-13 00:30 — Pivot: from ecology to learning machines

- **The critique.** Blake asked whether the ecology was "too biological" to
  say anything about AI. ChatGPT and Claude agreed it was. Its rules (food,
  habitats, death) were written by us, so success in it measures our rules,
  not anything about AI.
- **The new core question.** Software need not die. So under a fixed compute
  budget, should a learning machine live forever (keep training one network)
  or reproduce (hand over to descendants), and what should descendants
  inherit?
- **Why it might matter.**
  - Continual training loses plasticity (Dohare et al. 2024).
  - Fresh networks taught by a parent can beat the parent (born-again
    networks; iterated relearning).
  - Populations explore.
  - On the other side, birth costs compute and copies inherit faults.
- **Decision.** Blake chose "Yes, pivot" (00:32). The ecology world stays as
  a side exhibit.
- **Pre-registration v1** was committed (51083a4) before any study code
  existed.

## 2026-10-13 ~00:45 — v1 build and calibration

- **The build.** numpy MLP 32-128-128-4 with hand-written backprop, checked
  against finite differences (max error ~1e-10). Seven arms with exact
  multiply-accumulate accounting.
- **Calibration (fresh networks only).** Learning rate 3e-3 (median 125
  steps to 90%), S = 200 steps per era, K = 50 probe steps (fresh NOVEL
  = 41%).

## 2026-10-13 ~01:00 — v1 pilot stopped after 51 runs; two problems

1. **The probe was broken.** Every single-network arm, even networks at most
   5 eras old, scored below a fresh network on both probes. The probe was
   measuring how hard a confident old output layer is to overwrite.
   - Fix: give the probe copy a fresh output layer (v1 deviation 3).
   - Even after the fix, trained networks learned new skills more slowly
     than fresh ones. This is consistent with warm-starting results (Ash &
     Adams 2020).
2. **The world could not answer the question.** Every task was learnable from
   scratch within an era (the calibration rule required it). So starting over
   cost nothing, and knowledge never accumulated: the immortal learner's
   reuse was near the fresh baseline, because old skills were overwritten.

- **Carried forward.** With a new skill every 2 eras, the immortal learner's
  online accuracy fell from ~98% to ~60% over 120 eras (2 seeds). Learners
  restarted every 5 eras stayed at 97–99%. Loss of plasticity is present and
  strong at this learning rate.

## 2026-10-13 ~01:10 — Staircase check (exploratory)

- **The idea.** Make knowledge compound by making each new skill extend an
  old one by one bit. Theory says gradient descent learns such "staircases"
  efficiently but struggles with isolated high-order parities (Abbe et al.
  2022).
- **The check.** 24 runs (`paper/exploratory/staircase_check.py`, output in
  `staircase_check.txt`). At learning rate 3e-3:
  - fresh networks failed to learn a 5- or 6-bit parity within 4,000 steps
    in 5 of 6 tries;
  - climbing one bit at a time took 75–300 steps per step.
  - The property holds clearly in our networks.
- **Decision: v2 of the study.**
  - The staircase world replaces the v1 world.
  - TEACH now matches only the parent's last hidden layer plus outputs, so it
    passes on what the parent computes rather than its first-layer weights.
  - New measures:
    - KNOWLEDGE: linear readout of every introduced skill;
    - FRONTIER: learning the stream's next skills;
    - NOVEL: plasticity on reserved two-bit skills.
  - Calibration of S now measures the climbing pace.
  - All of this is written in `PREREGISTRATION_v2.md` before any v2 run.

## 2026-10-13 ~01:40 — v2 calibration

- **First attempt.** One new skill per era. The single climbing learner was
  stuck (more than 3,000 steps) in 16% of eras, because half of new skills
  were never presented before their children arrived.
- **Fix.** New skills are now always presented on arrival, and calibration
  climbs at the grid's fastest pace (a new skill every 2 eras).
- **Second attempt.**
  - Learning rate 3e-3.
  - K = 50 (fresh NOVEL accuracy 70%).
  - Median climbing step 300; 90th percentile about 1,200.
  - S = 800, the largest candidate. It still misses the 90% rule (83%).
  - Logged as v2 deviation 1.

## 2026-10-13 ~02:00 — v2 pilot stopped: the staircase was too steep

- **What happened.** On the first practice world at the fast pace (new
  skill every 2 eras), every arm collapsed to near chance on the stream after
  about 40 eras. That included restarts every 5 eras. About 50% of hidden
  units were dead, and the probes were at chance.
- **Cause.** New skills extended the newest skill half the time. The trunk
  reached 8-bit skills by era 20, so after one missed step most tasks were
  unlearnable. Training on effectively random labels at learning rate 3e-3
  kills plasticity for everyone.
- **Fixes** (v2 deviation 2):
  - Parents are now drawn uniformly, which gives a bushy tree whose depth
    grows slowly (mean skill about 4.7 bits at era 120 at the fast pace).
    Skills are capped at 10 bits.
  - The learning rate and S are now calibrated with the real per-era
    budget, using a single learner's first 40 eras.
- **Recalibration** (seeds 1–8):
  - Learning rate 1e-3, S = 800 and K = 100.
  - The early accuracy at S = 800 was 94% with learning rate 1e-3 and 89%
    with 3e-3.
- **Side observation.** Population representatives with evolved learning
  rates can score near 100% on NOVEL. The probe uses each network's own
  learning rate, so the NOVEL probe partly measures the learning rate as well
  as the state of the weights. Each network's learning rate is recorded, so
  this can be separated in analysis.
- **Pilot logistics.** Runs now go to GitHub Actions in 20 parallel shards
  (`.github/workflows/study1.yml`); results are committed back to the run
  branch.
