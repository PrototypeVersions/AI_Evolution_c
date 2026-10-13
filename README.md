# AI_Evolution_c — AI Evolution Lab

Closed simulations of how learning machines change, improve and pass things
on. Everything runs in-process on synthetic data. There is no networking and
no real or volunteer computers are involved. See [SAFETY.md](SAFETY.md).

**Website:** the GitHub Pages site built from `docs/`.

## Study 1: reproduce, or live forever?

The main experiment. Under exactly equal training compute, on a never-ending
stream of problems that keeps getting harder, does a learning machine improve
more by living forever or by reproducing? And which inheritance channel
matters: weights, behaviour (teaching) or learning settings (genes)?

- **The learners** are small neural networks (32 → 128 → 128 → 4) trained with
  hand-written numpy backpropagation.
- **The world** is a staircase of parity skills. Each new skill adds one bit to
  an existing one, so knowledge has to accumulate.
- **Nine life histories** are compared at equal compute:
  - immortal;
  - shrink-and-perturb reset;
  - restart;
  - teach a child, plus two secondary versions with a longer childhood;
  - a population that copies weights;
  - a population that evolves only its learning settings;
  - random search.
- **Pre-registered.** The plan in force is
  [PREREGISTRATION_v2.md](PREREGISTRATION_v2.md), and every later change is a
  dated deviation. The protocol was frozen before the confirmation seeds were
  run.

Everything needed to write the paper lives in [`paper/`](paper/README.md):
- the lab notebook;
- related work;
- the methods draft;
- statistical summaries;
- scripts that rebuild every figure from the raw records.

### Running it

```bash
pip install numpy matplotlib
python -m learners.calibrate                                     # calibration (single learners only)
python -m learners.run --phase pilot --seeds 100-109             # exploratory pilot
python -m learners.run --phase confirmation --seeds 7000-7029    # needs the frozen protocol
python -m learners.analysis --phase confirmation                 # pre-registered tests
python paper/figures/make_figures.py --phase confirmation        # figures
python -m learners.site                                          # website data (docs/study1.json)
python -m unittest discover -s tests                             # tests
```

Big batches run on GitHub Actions. Push a branch named `run/study1-<name>`
containing `learners/batch.json` (for example
`{"phase": "confirmation", "seeds": "7000-7029"}`). The workflow
`.github/workflows/study1.yml` splits the batch over 20 machines and commits
`learners/results/<phase>.jsonl` back to that branch.

## The ecology world (side exhibit)

One persistent world (`longrun/`) that is never reset. It has four habitats
linked by migration. Agents carry small evolving rule-list programs and
compete for regrowing resources. A scheduled GitHub Action advances it once a
day, and `docs/world.html` shows it.

Advances are deterministic, and any change to `longrun/config.json` is logged
as an intervention. It is for watching and for generating hypotheses, not for
causal claims.

```bash
python -m longrun.advance --ticks 4000   # continue from longrun/state/
```

## Layout

```
learners/   Study 1: networks, world, life histories, runner, analysis, site data
paper/      notebook, related work, methods, results summaries, figure scripts
longrun/    the ecology world, its checkpoint (state/) and the daily advance
docs/       the website: index.html (Study 1), world.html (ecology world)
tests/      learner, equal-compute, reproducibility, containment and long-run tests
```

## History

An earlier "lab v0" studied inherited memory in a rule-based replication
simulator. Its one candidate finding did not replicate on fresh seeds. It was
retired on 2026-10-13 when Study 1 replaced it. Its code and results remain in
the git history: see commit 15f7aa0 and the merge of PR #1.
