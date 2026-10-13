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

## 2026-10-13 ~01:55 — Website rebuilt around Study 1; lab v0 retired

- **Website.** `docs/index.html` is now a black-background page about Study
  1. Every number on it comes from `docs/study1.json`, which
  `python -m learners.site` builds from the raw records. While confirmation
  runs, it shows the pilot, clearly labelled exploratory. The arm colours are
  the validated dark categorical palette; secondary arms use dashed lines.
- **Why the stream figure gained a difficulty strip.** Blake read the
  falling accuracy curves as learners getting worse. They are not: the tasks
  get harder, from 2 bits per skill at the start to about 4–5 by era 120.
  Figure 1 and the site now show the mean size of the current task's skills
  above the accuracy curves. Worth keeping in the paper, since any reader
  will have the same first reaction.
- **Observation (pilot, exploratory).** At the 90% readout threshold, the
  immortal learner in the slow world knows only 2 of 23 skills at era 120:
  roughly the two in the current task. It still keeps up at about 90% on the
  stream, so forgotten skills must be relearned quickly. Readout below 90%
  may still carry useful structure ("savings"). KNOWLEDGE measures what is
  explicitly retained, not what is quick to recover. Note this in the
  discussion.
- **Lab v0 retired.** `sim/`, `experiments/`, `dashboard/`, `docs/data.json`
  and `tests/test_sim.py` were deleted. Their one candidate finding
  ("unrelated memory recovers best") did not replicate on fresh seeds. They
  remain in git history (commit 15f7aa0, merge of PR #1). The long run's
  only dependency on them, `code_commit`, moved to `longrun/provenance.py`.

## 2026-10-13 02:05 — Confirmation results (seeds 7000–7029, frozen protocol)

All 1,020 confirmation runs finished on GitHub Actions (run 38333032173)
and carry protocol hash 7e75f8ff9b071279 and code commit 75e8f0a. The
records were copied unchanged from branch `run/study1-confirmation`
(commit 781e3a8) to `learners/results/confirmation.jsonl`. Analysis and
figures were produced by the pre-registered scripts with no changes:
`results/confirmation_summary.{json,md}` and `figures/confirmation/`.
Verdicts below are after Holm–Bonferroni over the 44 family members
(secondary family S1–S6 corrected separately). "Fast" is R = 2, "slow" is
R = 6; the first number of a pair is lifespan 5, the second lifespan 20.

**Primary family.**
- **H1, the immortal learner loses plasticity: SUPPORTED in all four
  regimes.** NOVEL falls from about 55% at era 20 to 50–52% at era 120,
  against 67% for a fresh network; 43–50% of its hidden units are dead.
- **H2a, the immortal learner knows more than one that restarts: REVERSED
  in the fast world** (−0.9 points at both lifespans). Not supported in the
  slow world (+3.5, Holm p = 0.054; −3.8).
- **H2b, CLONE knows more than GENES:** supported in three of four regimes,
  not in fast/L5.
- **H3a, TEACH takes the next step better than IMMORTAL:** supported in the
  fast world (+4.8, +4.3), not in the slow world. In the fast world RESTART
  does just as well (56.8 and 57.3 vs 56.7 and 56.3), so this is the value
  of a fresh network, not of teaching.
- **H3b, TEACH keeps up better than IMMORTAL: REVERSED in three regimes**
  (−6.4 fast/L5, −30.1 slow/L5, −16.5 slow/L20); not significant fast/L20.
- **H3c, CLONE takes the next step better than IMMORTAL: SUPPORTED in all
  four regimes, against our prediction ("no").** Slow world: 93.5 and 94.3
  vs 74.7. At the default learning rate (secondary probe) CLONE still
  reaches 85.1 and 89.7, so most of the lead is not an evolved step size.
- **H4a, TEACH > RESET on the next step:** supported fast/L20 (+5.2),
  reversed slow/L5 (−11.6), not significant otherwise.
- **H4b, TEACH > RESET on the stream:** reversed in three regimes.
- **H5, GENES > RANDOM on the stream:** supported in three regimes (+3.5,
  +8.7, +6.2); fast/L20 not significant (+1.1).
- **H6, splitting compute is costly (IMMORTAL > every population arm on the
  stream):** supported in the slow world (IMMORTAL − CLONE ≈ 13 points);
  not in the fast world.
- **H7, TEACH knows more than RESTART:** not supported anywhere.

**Secondary family.** S1 (TEACH16 knows more than TEACH): not supported.
S2 (TEACH4 > IMMORTAL, next step) supported fast/L5 only; S4 (TEACH16 >
IMMORTAL, next step) supported fast/L20 only. S3, S5 and S6 (a long
childhood keeps up better than IMMORTAL or RESET) were mostly reversed.

**Stream accuracy, eras 61–120 (ONLINE, %).**

| Regime | IMMORTAL | RESET | RESTART | TEACH | CLONE | GENES | RANDOM |
|---|---|---|---|---|---|---|---|
| fast/L5 | 43.5 | 50.0 | 39.5 | 37.1 | 38.9 | 33.4 | 30.0 |
| fast/L20 | 43.5 | 42.8 | 43.5 | 42.1 | 40.2 | 31.6 | 30.5 |
| slow/L5 | 93.3 | 94.1 | 62.7 | 63.2 | 80.1 | 50.3 | 41.6 |
| slow/L20 | 93.3 | 93.8 | 77.0 | 76.8 | 79.9 | 52.8 | 46.7 |

**Plain reading.** To do well on the current task, keep one network and
loosen it now and then (RESET ≈ IMMORTAL in the slow world, RESET best at
fast/L5). To stay able to take the next step, keep a small population and
copy the best member's weights (CLONE best FRONTIER everywhere). Children
started from scratch, taught or not, lose on both. Teaching, as
implemented, did not pass on measurable knowledge even with a 16-era
childhood.

**Caveats to carry into the paper.**
- The fast world is close to the floor for every arm (ONLINE 30–50%,
  chance 25%, FRONTIER near a fresh network's 54%). Its comparisons say
  less than the slow world's.
- CLONE's representative is the fittest of four, and each member gets a
  quarter of the updates. Fewer updates per network may be why it loses
  less plasticity; a control that trains one network with a quarter of the
  budget would separate selection from slower wear.
- FRONTIER falls over time for every arm, including fresh networks, because
  the next skills are larger (more bits). It is comparable between arms at
  a checkpoint, not across checkpoints.
- KNOWLEDGE (linear readout ≥ 90%) is near zero for all arms by era 120. It
  measures explicit retention, not how fast a skill comes back.
- The result is about small MLPs on synthetic parity skills. Whether it
  holds for other architectures (a small transformer) is the obvious next
  study.

**Website.** `docs/study1.json` is now built from the confirmation records
and `docs/index.html` shows the findings and the verdict matrix. Wording on
the site was checked against the summary table; where a result was
descriptive and not tested (RESET vs IMMORTAL on the stream) the site says so.

## 2026-10-13 02:35 — Site went live; an audit of its claims found 21 to correct

Blake approved merging PR #3, and the site went live at 02:07 UTC (merge
commit bf4237d). Because the page is now public, every factual claim on it
was checked against the raw records, the summary, the protocol and the code.
Four independent auditors covered the page in parts. A second reviewer per
part then tried to refute each reported error, and only the errors that
survived were kept: 25 reports, 21 distinct problems. None of them changes
a verdict, but several overstated or misdescribed a result. All were fixed
on branch `site-audit-fixes`. Three more reviewers then checked the fixes
(numbers, meaning, code) and found 14 smaller problems in the new wording,
which were fixed too. The ones worth remembering for the paper:

- **Equal compute is not equal updates.** The page said one era is "800
  training steps, the same for everyone". In fact every arm gets the same
  compute. A population member takes 200 steps per era, and a teaching era
  has 400 task steps. This matters because CLONE's lead on the next step
  (H3c) may come partly from each member wearing out more slowly. The page
  now says so in the CLONE finding, and the paper must too.
- **FRONTIER is a probe, and an accuracy.** "Could learn the next skill
  94% of the time" was wrong twice over.
  - FRONTIER measures a discarded copy given 800 steps on one skill, not
    something the population did in its own life.
  - It is a mean accuracy, not a success rate. In the slow world CLONE
    fully learned (≥ 90%) 84–87% of next-skill probes, against 31% for
    IMMORTAL. At the default learning rate CLONE's share falls to 63–72%.
  - Most probes end near 50% or near 100%, but not the immortal learner's
    in the slow world: 44% of its probes fall between 55% and 90%. Report
    the share fully learned alongside the mean, never instead of it.
- **ONLINE is an average over eras 61–120.** The immortal learner
  "averages" 93%; it slides from 100% at era 60 to about 86% at era 120.
- **Null results were stated too strongly.**
  - H7 slow/L5 is +2.5 points with a CI that excludes zero, but Holm
    p = 0.17.
  - H2a in the slow world is +3.5 and −3.8 by lifespan, and neither
    survives correction.
  - In the fast world, H2a is a reliable reversal, not a null.
- **H1 counts each world once.** IMMORTAL has no lifespan, so H1's "four"
  results are two results, each counted twice. The pre-registered family
  still counts four members, as planned; the page now says "both worlds".
- **What the immortal learner keeps.** At era 120 it knows 75% of the two
  skills in its current task in the slow world, but only 25% of the skills
  from its last five tasks. In the fast world it knows 3% of its current
  task's skills.
- **TEACH vs RESTART on the stream is descriptive.** It was never tested.
  The page now says the cost "seems to" come from starting over.
- **The honesty ledger said "before any data".** That was wrong.
  - H1–H7 and the analysis came before any v2 run, but one prior used the
    stopped v1 pilot.
  - After the v2 pilot, the FRONTIER probe behind H3a, H3c and H4a was
    lengthened from 100 steps to one era (deviation 3), and S1–S6 were
    added.
  - Everything came before confirmation data, which is the claim that
    matters. The paper must state the FRONTIER change wherever H3c is
    reported.
- **Smaller fixes.**
  - The stream chart is a trailing 5-era average; the caption, hover and
    table now say so.
  - The guessing and fresh-network lines are labelled.
  - The secondary family is corrected over its own 18 tests.
  - "Worlds" now means only seeds or the fast and slow pace. The four
    pace × lifespan combinations are "conditions" ("settings" clashed with
    the learning settings GENES inherits).
  - The staircase check numbers are at learning rate 3e-3, and the 1e-3
    numbers are now given too (also corrected in `methods.md`).
- **Rounding.** `learners/site.py` rounded every value to 4 decimals, and
  the page then rounded again to 0.1 point. That moved about 26 displayed
  values by 0.1 from the summary. Values the page displays are now passed
  unrounded (the data file grows from 111 KB to 175 KB). Every test
  statistic and every arm value in `docs/study1.json` is identical to
  `results/confirmation_summary.json`.
