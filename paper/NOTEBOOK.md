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

## 2026-10-13 ~01:35 — Correction: times of the last three entries

The times on the three entries above were estimated, and too late. Commit
times show the staircase check ended about 00:50, v2 calibration about
01:05, and the v2 pilot was stopped about 01:15. The order of events is
unchanged.

## 2026-10-13 ~01:35 — v2 pilot complete; probes fixed (v2 deviation 3)

- **The pilot.** 280 runs (7 arms × 4 regimes × seeds 100–109, plus fresh
  reference networks) on GitHub Actions in 20 shards. Records:
  `learners/results/pilot.jsonl`. Summary: `results/pilot_summary.md`.
  Figures: `figures/pilot/`. Exploratory: with 10 seeds and 44 tests,
  nothing can pass Holm–Bonferroni (smallest possible p is about 0.002).
- **What it shows** (exploratory, same direction in all 10 seeds unless
  noted):
  - At the slow pace (new skill every 6 eras), the immortal learner and
    shrink-and-perturb keep up with the stream (ONLINE 92–93%). Weight
    copying in a population reaches 77–78%. Teaching a fresh child for half
    an era is no better than restarting from scratch (62% vs 60% with
    lifespan 5; 74% vs 75% with lifespan 20). Darwinian selection on
    learning settings reaches 49–52% and random search 41–46%.
  - At the fast pace (new skill every 2 eras), nobody keeps up (ONLINE
    30–54%). Shrink-and-perturb every 5 eras does best (54% vs 43% for the
    immortal learner).
  - The immortal learner's plasticity falls: NOVEL drops 5–10 points from
    era 20 to era 120, and 44–49% of its hidden units are dead by the end
    (restarting every 5 eras: about 9%).
  - Restarting learners know *more* of the skills at era 120 than the
    immortal learner in the slow pace with lifespan 20 (13.5% vs 8.3%),
    because the immortal learner forgets skills it no longer practises and
    the restarted one learned the recent ones fresh. This goes against H2a.
  - Splitting compute four ways is very costly: 14–51 points of ONLINE.
- **Problems found.**
  - FRONTIER was at chance (50–55%) for every arm, including learners whose
    readouts showed they knew the parent skills: a floor effect from a
    probe calibrated on two-bit skills.
  - NOVEL for population representatives reached 90%+, largely because the
    probe uses each network's own evolved learning rate.
  - FINAL_KNOWLEDGE was near floor (0–17%) for every arm.
- **Why teaching failed** (`exploratory/teaching_fidelity.py`, seeds
  60–64). A parent that knew 5–6 skills was taught to a fresh child for
  half an era, 2 eras or 8 eras of teaching budget. The child kept 0–2 of
  them, 2–4, and 4–6 respectively. Half an era is too short a childhood.
- **Decision: v2 deviation 3** (written in `../PREREGISTRATION_v2.md`
  before any confirmation seed):
  - FRONTIER gets one era's budget (800 steps). NOVEL keeps K = 100.
  - Secondary measures: NOVEL at the default learning rate; KNOWLEDGE
    averaged over checkpoints; share of the 8 newest skills known.
  - Secondary arms TEACH4 and TEACH16 (a childhood of 4 or 16 eras, during
    which the parent keeps learning with half the budget), tested in a
    separate family S1–S6 with predictions written first.
  - The primary family H1–H7 is unchanged.
- **Sanity check of the new probe on world 100** (not a pilot seed for
  analysis; the code and numbers are in the session scratchpad, summarised
  here). Slow pace, era 120:
  - FRONTIER: fresh network 66%, immortal learner 72%, TEACH4 75%,
    restart every 5 eras 67%. The immortal learner's FRONTIER fell from
    99% at era 20 to 72%, so the probe now moves and is not at ceiling.
  - TEACH4 with lifespan 20 kept 26% of skills at era 120 against 9% for
    the immortal learner, with ONLINE 79% against 90%.
  - Fast pace, same world, era 20 → era 120: FRONTIER for the immortal
    learner 87% → 52%, shrink-and-perturb every 5 eras 84% → 69%, TEACH4
    65% → 58%, fresh network 75% → 59%. The immortal learner ends *below* a
    fresh network: it can no longer take steps a fresh network can.
  - So FRONTIER now discriminates at both paces.
- **Bug fixed before freezing.** A new unit test showed that in TEACH4 and
  TEACH16 the child took over at the end of the last childhood era, so it
  was measured once on the stream before it had trained on it. The
  hand-over now happens at the start of the next era, as the plan says.
  The TEACH4 numbers in the sanity check above came from the first version.
- **One more secondary probe.** The pilot's FRONTIER (at K = 100) was also
  highest for the population arms, whose learning rates evolve. So FRONTIER
  is now also recorded at the default learning rate, like NOVEL. A reviewer
  will ask whether population arms win on the probes because of their
  weights or their step size; this answers it.

## 2026-10-13 ~01:45 — Protocol frozen; confirmation launched

- `learners/protocol.json` set to `"frozen": true`. Protocol hash
  `7e75f8ff9b071279`. Every confirmation record must carry this hash.
- Confirmation: seeds 7000–7029, 34 runs per seed (1,020 runs), on GitHub
  Actions from branch `run/study1-confirmation`. These seeds have never been
  run before by any code version.
- From here on, any change to the code or protocol is a deviation that must
  be dated and justified in `../PREREGISTRATION_v2.md`, and results from
  before and after it are reported separately.

## 2026-10-13 01:38 — Correction: freeze time

The `frozen_at` value in `learners/protocol.json` (01:45Z) and the time on
the entry above were estimates and are a few minutes late. The freeze
commit (75e8f0a) is dated 01:37:30Z and the confirmation run on GitHub
(run 38333032173) started at 01:37:42Z; those are the authoritative times.
`frozen_at` is left as written so the protocol hash stays the one the
confirmation records carry. Tests passed on GitHub for the frozen commit.
