# Study 1 — pilot summary

**Exploratory.** These are pilot seeds. Verdicts use the pre-registered tests, but only confirmation seeds can support a claim.

Records: 280 · seeds: 100–109 (10) · protocol 19a46b0b7e1ba870 · Holm–Bonferroni across 44 family members

## Regime: new skill every 2 eras, lifespan 5 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 49.8 ± 0.4 | 0.0 ± 0.0 | 0.0 | 66.5 ± 2.0 | — | — |
| IMMORTAL | 49.8 ± 0.5 | 0.0 ± 0.0 | 0.0 | 49.9 ± 0.6 | 42.6 ± 9.0 | 49.3% |
| RESET | 50.0 ± 0.6 | 1.7 ± 1.7 | 2.0 | 55.1 ± 4.8 | 54.0 ± 4.9 | 43.1% |
| RESTART | 50.3 ± 0.6 | 1.3 ± 1.5 | 1.5 | 59.8 ± 3.1 | 39.9 ± 3.8 | 9.6% |
| TEACH | 50.0 ± 0.2 | 0.8 ± 1.1 | 1.2 | 58.5 ± 2.6 | 36.4 ± 6.4 | 15.2% |
| CLONE | 50.5 ± 1.0 | 0.6 ± 1.1 | 0.8 | 77.6 ± 17.2 | 38.4 ± 4.4 | 42.9% |
| GENES | 50.0 ± 0.5 | 0.5 ± 0.8 | 0.7 | 89.1 ± 17.3 | 33.1 ± 3.5 | 20.6% |
| RANDOM | 50.0 ± 0.4 | 0.2 ± 0.5 | 0.3 | 70.1 ± 15.5 | 30.3 ± 1.5 | 0.8% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | — | — |
| IMMORTAL | 10.3 ± 2.7 | 0.0 ± 0.0 | — | — |
| RESET | 12.0 ± 1.5 | 2.5 ± 5.3 | — | — |
| RESTART | 6.1 ± 1.7 | 1.2 ± 4.0 | — | — |
| TEACH | 6.7 ± 1.6 | 1.2 ± 4.0 | — | — |
| CLONE | 6.5 ± 4.4 | 0.0 ± 0.0 | — | — |
| GENES | 2.0 ± 1.1 | 0.0 ± 0.0 | — | — |
| RANDOM | 1.4 ± 1.6 | 0.0 ± 0.0 | — | — |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -9.5 [-13.1, -6.2] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: -1.3 [-2.1, -0.5] | 0.0634 | 1.0000 | NOT SUPPORTED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 0.2 [-0.6, 1.0] | 1.0000 | 1.0000 | NOT SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: 0.2 [-0.1, 0.5] | 0.3776 | 1.0000 | NOT SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -6.2 [-14.0, 0.3] | 0.1493 | 1.0000 | NOT SUPPORTED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 0.6 [0.1, 1.3] | 0.0927 | 1.0000 | NOT SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: -0.0 [-0.4, 0.3] | 0.9493 | 1.0000 | NOT SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -17.7 [-22.4, -13.2] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 2.8 [0.7, 4.6] | 0.0322 | 0.7727 | NOT SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 4.2 [-1.1, 9.3]; IMMORTAL − GENES ONLINE: 9.5 [4.5, 14.5]; IMMORTAL − RANDOM ONLINE: 12.3 [7.2, 17.4] | 0.1688 | 1.0000 | NOT SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: -0.5 [-1.3, 0.0] | 0.5005 | 1.0000 | NOT SUPPORTED |

## Regime: new skill every 2 eras, lifespan 20 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 49.8 ± 0.4 | 0.0 ± 0.0 | 0.0 | 66.5 ± 2.0 | — | — |
| IMMORTAL | 49.8 ± 0.5 | 0.0 ± 0.0 | 0.0 | 49.9 ± 0.6 | 42.6 ± 9.0 | 49.3% |
| RESET | 49.9 ± 0.6 | 0.3 ± 1.0 | 0.3 | 50.4 ± 0.6 | 44.9 ± 7.2 | 49.3% |
| RESTART | 50.1 ± 0.5 | 1.0 ± 1.3 | 1.1 | 53.4 ± 2.3 | 42.5 ± 5.0 | 40.8% |
| TEACH | 50.2 ± 0.4 | 0.6 ± 0.8 | 1.2 | 55.1 ± 4.1 | 42.2 ± 4.6 | 40.3% |
| CLONE | 50.4 ± 0.9 | 2.1 ± 2.1 | 1.7 | 70.4 ± 15.9 | 39.8 ± 4.6 | 38.5% |
| GENES | 50.2 ± 0.7 | 0.6 ± 1.1 | 0.8 | 78.8 ± 16.0 | 31.8 ± 1.5 | 28.1% |
| RANDOM | 50.1 ± 0.3 | 0.5 ± 0.8 | 0.7 | 72.1 ± 11.6 | 32.1 ± 2.6 | 12.5% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | — | — |
| IMMORTAL | 10.3 ± 2.7 | 0.0 ± 0.0 | — | — |
| RESET | 9.9 ± 2.3 | 0.0 ± 0.0 | — | — |
| RESTART | 9.1 ± 2.7 | 0.0 ± 0.0 | — | — |
| TEACH | 9.0 ± 2.2 | 1.2 ± 4.0 | — | — |
| CLONE | 6.4 ± 3.0 | 0.0 ± 0.0 | — | — |
| GENES | 5.0 ± 2.5 | 0.0 ± 0.0 | — | — |
| RANDOM | 3.7 ± 2.3 | 0.0 ± 0.0 | — | — |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -9.5 [-13.1, -6.2] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: -1.0 [-1.7, -0.2] | 0.1259 | 1.0000 | NOT SUPPORTED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 1.4 [0.5, 2.7] | 0.0634 | 1.0000 | NOT SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: 0.4 [0.2, 0.6] | 0.0049 | 0.1561 | NOT SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -0.4 [-5.1, 4.0] | 0.8693 | 1.0000 | NOT SUPPORTED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 0.6 [0.1, 1.3] | 0.0283 | 0.7639 | NOT SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: 0.3 [0.1, 0.6] | 0.0439 | 1.0000 | NOT SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -2.6 [-6.4, 1.2] | 0.2254 | 1.0000 | NOT SUPPORTED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: -0.3 [-1.7, 1.0] | 0.7073 | 1.0000 | NOT SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 2.8 [-2.0, 7.9]; IMMORTAL − GENES ONLINE: 10.8 [5.7, 15.9]; IMMORTAL − RANDOM ONLINE: 10.5 [6.1, 15.2] | 0.3210 | 1.0000 | NOT SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: -0.3 [-0.9, 0.3] | 0.6254 | 1.0000 | NOT SUPPORTED |

## Regime: new skill every 6 eras, lifespan 5 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 49.9 ± 0.3 | 0.0 ± 0.0 | 0.0 | 67.6 ± 1.2 | — | — |
| IMMORTAL | 50.0 ± 1.0 | 8.3 ± 3.2 | 3.9 | 52.4 ± 1.6 | 92.0 ± 2.5 | 44.0% |
| RESET | 50.7 ± 0.9 | 11.7 ± 4.1 | 4.3 | 54.5 ± 3.5 | 93.0 ± 3.5 | 38.0% |
| RESTART | 50.9 ± 2.1 | 7.0 ± 6.2 | 2.1 | 60.3 ± 4.9 | 60.4 ± 4.8 | 9.2% |
| TEACH | 51.0 ± 1.2 | 10.0 ± 7.4 | 2.8 | 57.6 ± 3.9 | 61.9 ± 5.1 | 17.8% |
| CLONE | 55.4 ± 4.8 | 11.7 ± 8.9 | 3.2 | 82.0 ± 17.9 | 76.8 ± 9.0 | 37.0% |
| GENES | 52.7 ± 5.5 | 2.6 ± 3.7 | 1.0 | 91.5 ± 13.4 | 49.2 ± 5.5 | 32.7% |
| RANDOM | 50.8 ± 1.6 | 0.9 ± 1.8 | 0.5 | 70.5 ± 13.1 | 41.4 ± 3.5 | 3.5% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | — | — |
| IMMORTAL | 36.3 ± 4.2 | 8.8 ± 8.4 | — | — |
| RESET | 37.7 ± 5.7 | 10.0 ± 7.9 | — | — |
| RESTART | 20.2 ± 7.6 | 5.0 ± 6.5 | — | — |
| TEACH | 22.8 ± 7.7 | 8.8 ± 8.4 | — | — |
| CLONE | 25.2 ± 6.8 | 8.8 ± 10.3 | — | — |
| GENES | 12.3 ± 5.8 | 2.5 ± 5.3 | — | — |
| RANDOM | 7.5 ± 3.9 | 1.2 ± 4.0 | — | — |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -5.1 [-6.9, -3.5] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: 1.3 [-3.0, 5.2] | 0.5161 | 1.0000 | NOT SUPPORTED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 9.1 [4.8, 13.9] | 0.0166 | 0.4810 | NOT SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: 1.0 [0.1, 1.8] | 0.0615 | 1.0000 | NOT SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -30.2 [-33.7, -26.8] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 5.4 [2.5, 8.5] | 0.0068 | 0.2117 | NOT SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: 0.3 [-0.5, 1.1] | 0.5044 | 1.0000 | NOT SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -31.1 [-34.1, -28.0] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 7.8 [5.6, 10.0] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 15.3 [10.7, 19.6]; IMMORTAL − GENES ONLINE: 42.8 [38.8, 46.7]; IMMORTAL − RANDOM ONLINE: 50.7 [47.7, 53.4] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: 3.0 [-0.4, 7.0] | 0.2507 | 1.0000 | NOT SUPPORTED |

## Regime: new skill every 6 eras, lifespan 20 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 49.9 ± 0.3 | 0.0 ± 0.0 | 0.0 | 67.6 ± 1.2 | — | — |
| IMMORTAL | 50.0 ± 1.0 | 8.3 ± 3.2 | 3.9 | 52.4 ± 1.6 | 92.0 ± 2.5 | 44.0% |
| RESET | 50.3 ± 0.8 | 7.8 ± 4.9 | 3.4 | 53.0 ± 2.5 | 92.6 ± 2.5 | 42.1% |
| RESTART | 50.6 ± 0.4 | 13.5 ± 4.3 | 3.7 | 55.0 ± 4.1 | 74.8 ± 7.8 | 33.3% |
| TEACH | 50.6 ± 0.6 | 14.3 ± 6.8 | 4.0 | 54.8 ± 3.3 | 73.5 ± 7.0 | 32.6% |
| CLONE | 53.0 ± 2.4 | 16.5 ± 8.1 | 3.4 | 72.8 ± 14.8 | 78.1 ± 8.0 | 22.7% |
| GENES | 52.9 ± 3.9 | 6.1 ± 6.2 | 2.0 | 83.9 ± 15.8 | 51.7 ± 8.0 | 26.1% |
| RANDOM | 51.5 ± 2.9 | 3.9 ± 4.8 | 1.3 | 65.3 ± 12.0 | 45.5 ± 2.6 | 13.5% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | — | — |
| IMMORTAL | 36.3 ± 4.2 | 8.8 ± 8.4 | — | — |
| RESET | 34.8 ± 5.5 | 7.5 ± 6.5 | — | — |
| RESTART | 35.0 ± 4.9 | 11.2 ± 9.2 | — | — |
| TEACH | 36.5 ± 5.0 | 11.2 ± 9.2 | — | — |
| CLONE | 28.8 ± 7.8 | 11.2 ± 9.2 | — | — |
| GENES | 19.9 ± 13.1 | 5.0 ± 6.5 | — | — |
| RANDOM | 15.2 ± 5.3 | 3.8 ± 6.0 | — | — |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -5.1 [-6.9, -3.5] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: -5.2 [-8.7, -2.2] | 0.0205 | 0.5737 | NOT SUPPORTED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 10.4 [3.9, 17.4] | 0.0283 | 0.7639 | NOT SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: 0.6 [0.0, 1.1] | 0.1083 | 1.0000 | NOT SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -18.6 [-22.5, -15.0] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 3.0 [1.5, 4.5] | 0.0088 | 0.2634 | NOT SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: 0.2 [-0.3, 0.8] | 0.5024 | 1.0000 | NOT SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -19.2 [-22.9, -15.8] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 6.2 [2.3, 10.1] | 0.0283 | 0.7639 | NOT SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 14.0 [10.1, 18.5]; IMMORTAL − GENES ONLINE: 40.4 [34.7, 45.7]; IMMORTAL − RANDOM ONLINE: 46.5 [44.2, 48.9] | 0.0029 | 0.1288 | NOT SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: 0.9 [-2.2, 3.9] | 0.5356 | 1.0000 | NOT SUPPORTED |
