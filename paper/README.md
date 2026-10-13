# Paper materials — Study 1

Everything needed to write up Study 1 ("Should a learning machine reproduce,
or live forever?") lives here or is generated from the raw records.

**Status (2026-10-13).** The confirmation run is complete. The verdicts and a
plain reading are in the notebook entry "Confirmation results"; the full
tables are in `results/confirmation_summary.md`.

| What | Where |
|---|---|
| The plan, predictions and every deviation | [`../PREREGISTRATION_v2.md`](../PREREGISTRATION_v2.md) (v1, kept as a record: [`../PREREGISTRATION.md`](../PREREGISTRATION.md)) |
| Dated decisions, findings and mistakes | [`NOTEBOOK.md`](NOTEBOOK.md) |
| Related work with why each paper matters | [`related_work.md`](related_work.md) |
| Draft methods section, updated with every deviation | [`methods.md`](methods.md) |
| Raw run records (one JSON line per run, with code commit and protocol hash) | `../learners/results/<phase>.jsonl` |
| Calibration data | `../learners/calibration.json` |
| Frozen protocol | `../learners/protocol.json` |
| Statistical summaries (pre-registered tests) | `results/<phase>_summary.{json,md}` |
| Figures (PNG and PDF) | `figures/<phase>/` |
| Exploratory checks referenced in the plan | `exploratory/` |

## Regenerating everything

```bash
pip install numpy matplotlib
python -m learners.calibrate                          # calibration (single learners only)
python -m learners.run --phase pilot --seeds 100-109  # exploratory pilot
python -m learners.run --phase confirmation --seeds 7000-7029   # needs a frozen protocol
python -m learners.analysis --phase confirmation      # pre-registered tests
python paper/figures/make_figures.py --phase confirmation
```

A run is deterministic given its seed, the code commit and the numpy version,
which every record stores.
