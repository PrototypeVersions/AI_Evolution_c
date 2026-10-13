# Study 1 — confirmation summary

Records: 1020 · seeds: 7000–7029 (30) · protocol 7e75f8ff9b071279 · Holm–Bonferroni across 44 family members

## Regime: new skill every 2 eras, lifespan 5 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 54.1 ± 5.2 | 0.0 ± 0.0 | 0.0 | 67.1 ± 1.5 | — | — |
| IMMORTAL | 52.0 ± 3.7 | 0.2 ± 0.6 | 0.1 | 49.9 ± 0.8 | 43.5 ± 7.0 | 49.6% |
| RESET | 59.3 ± 8.8 | 1.5 ± 1.6 | 1.8 | 52.6 ± 2.5 | 50.0 ± 5.9 | 44.4% |
| RESTART | 56.8 ± 5.6 | 1.1 ± 1.6 | 1.1 | 61.2 ± 2.9 | 39.5 ± 2.9 | 9.3% |
| TEACH | 56.7 ± 5.5 | 0.9 ± 1.6 | 0.8 | 57.3 ± 3.1 | 37.1 ± 6.2 | 18.3% |
| CLONE | 65.6 ± 7.6 | 1.3 ± 2.0 | 1.1 | 80.6 ± 18.3 | 38.9 ± 5.9 | 41.7% |
| GENES | 61.8 ± 8.6 | 0.6 ± 1.1 | 0.7 | 93.4 ± 12.3 | 33.4 ± 2.7 | 23.2% |
| RANDOM | 55.2 ± 5.3 | 0.3 ± 0.8 | 0.4 | 75.1 ± 15.7 | 30.0 ± 1.1 | 2.7% |
| TEACH4 | 55.5 ± 5.5 | 0.1 ± 0.3 | 0.1 | 54.2 ± 2.9 | 32.5 ± 5.1 | 23.7% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | 67.1 ± 1.5 | 54.1 ± 5.2 |
| IMMORTAL | 10.8 ± 2.4 | 0.0 ± 0.0 | 49.9 ± 0.8 | 52.0 ± 3.7 |
| RESET | 11.3 ± 2.4 | 2.1 ± 4.7 | 52.6 ± 2.5 | 59.3 ± 8.8 |
| RESTART | 5.5 ± 1.8 | 0.8 ± 3.2 | 61.2 ± 2.9 | 56.8 ± 5.6 |
| TEACH | 6.0 ± 2.4 | 0.4 ± 2.3 | 57.3 ± 3.1 | 56.7 ± 5.5 |
| CLONE | 5.2 ± 3.2 | 0.0 ± 0.0 | 61.4 ± 9.4 | 63.1 ± 6.7 |
| GENES | 2.7 ± 2.0 | 0.0 ± 0.0 | 62.3 ± 10.1 | 56.6 ± 5.4 |
| RANDOM | 1.7 ± 1.3 | 0.0 ± 0.0 | 64.1 ± 5.5 | 54.2 ± 5.1 |
| TEACH4 | 5.6 ± 2.1 | 0.0 ± 0.0 | 54.2 ± 2.9 | 55.5 ± 5.5 |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -5.1 [-6.4, -4.0] | 0.0001 | 0.0044 | SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: -0.9 [-1.5, -0.4] | 0.0014 | 0.0266 | REVERSED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 0.7 [0.2, 1.4] | 0.0265 | 0.2915 | NOT SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: 4.8 [2.7, 6.8] | 0.0002 | 0.0046 | SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -6.4 [-9.7, -3.2] | 0.0014 | 0.0266 | REVERSED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 13.6 [10.7, 16.7] | 0.0001 | 0.0044 | SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: -2.6 [-5.5, 0.3] | 0.0976 | 0.7111 | NOT SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -12.9 [-14.8, -11.0] | 0.0001 | 0.0044 | REVERSED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 3.5 [2.7, 4.2] | 0.0001 | 0.0044 | SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 4.6 [1.6, 7.7]; IMMORTAL − GENES ONLINE: 10.1 [7.4, 12.8]; IMMORTAL − RANDOM ONLINE: 13.6 [11.2, 16.1] | 0.0067 | 0.1005 | NOT SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: -0.2 [-0.6, 0.2] | 0.3872 | 1.0000 | NOT SUPPORTED |
| S2 (secondary) | FINAL_FRONTIER TEACH4 > IMMORTAL | lean no | 3.5 [1.4, 5.7] | 0.0028 | 0.0252 (secondary family) | SUPPORTED |
| S3 (secondary) | ONLINE TEACH4 > IMMORTAL | lean no | -11.0 [-13.8, -8.2] | 0.0001 | 0.0018 (secondary family) | REVERSED |
| S6 (secondary) | ONLINE TEACH4 > RESET | lean no | -17.5 [-19.5, -15.4] | 0.0001 | 0.0018 (secondary family) | REVERSED |

## Regime: new skill every 2 eras, lifespan 20 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 54.1 ± 5.2 | 0.0 ± 0.0 | 0.0 | 67.1 ± 1.5 | — | — |
| IMMORTAL | 52.0 ± 3.7 | 0.2 ± 0.6 | 0.1 | 49.9 ± 0.8 | 43.5 ± 7.0 | 49.6% |
| RESET | 51.1 ± 1.7 | 0.2 ± 0.5 | 0.2 | 50.3 ± 1.3 | 42.8 ± 6.3 | 49.4% |
| RESTART | 57.3 ± 5.7 | 1.1 ± 1.3 | 1.5 | 53.6 ± 2.6 | 43.5 ± 4.2 | 38.7% |
| TEACH | 56.3 ± 5.8 | 1.0 ± 1.5 | 1.3 | 52.4 ± 2.7 | 42.1 ± 5.0 | 42.0% |
| CLONE | 70.5 ± 9.6 | 1.5 ± 2.2 | 1.2 | 76.9 ± 17.1 | 40.2 ± 4.4 | 39.1% |
| GENES | 60.1 ± 8.4 | 0.4 ± 0.9 | 0.5 | 76.6 ± 15.6 | 31.6 ± 3.5 | 18.3% |
| RANDOM | 58.7 ± 7.7 | 0.4 ± 0.8 | 0.6 | 69.0 ± 16.0 | 30.5 ± 1.6 | 16.6% |
| TEACH4 | 54.5 ± 4.8 | 1.1 ± 1.6 | 1.1 | 52.0 ± 2.8 | 42.0 ± 5.7 | 41.7% |
| TEACH16 | 55.9 ± 7.6 | 0.7 ± 1.4 | 0.8 | 51.3 ± 1.5 | 38.1 ± 3.7 | 44.1% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | 67.1 ± 1.5 | 54.1 ± 5.2 |
| IMMORTAL | 10.8 ± 2.4 | 0.0 ± 0.0 | 49.9 ± 0.8 | 52.0 ± 3.7 |
| RESET | 10.5 ± 2.2 | 0.0 ± 0.0 | 50.3 ± 1.3 | 51.1 ± 1.7 |
| RESTART | 10.2 ± 2.6 | 1.2 ± 3.8 | 53.6 ± 2.6 | 57.3 ± 5.7 |
| TEACH | 10.3 ± 2.3 | 0.4 ± 2.3 | 52.4 ± 2.7 | 56.3 ± 5.8 |
| CLONE | 6.2 ± 3.4 | 0.0 ± 0.0 | 61.4 ± 7.8 | 67.7 ± 8.8 |
| GENES | 4.3 ± 2.7 | 0.0 ± 0.0 | 65.8 ± 8.6 | 58.7 ± 7.1 |
| RANDOM | 3.9 ± 2.3 | 0.0 ± 0.0 | 62.3 ± 6.8 | 58.4 ± 7.1 |
| TEACH4 | 10.1 ± 2.0 | 0.4 ± 2.3 | 52.0 ± 2.8 | 54.5 ± 4.8 |
| TEACH16 | 10.0 ± 2.0 | 0.0 ± 0.0 | 51.3 ± 1.5 | 55.9 ± 7.6 |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -5.1 [-6.4, -4.0] | 0.0001 | 0.0044 | SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: -0.9 [-1.4, -0.4] | 0.0004 | 0.0080 | REVERSED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 1.2 [0.6, 1.8] | 0.0003 | 0.0066 | SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: 4.3 [2.5, 6.1] | 0.0003 | 0.0066 | SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -1.4 [-4.0, 1.2] | 0.2983 | 1.0000 | NOT SUPPORTED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 18.5 [15.2, 21.7] | 0.0001 | 0.0044 | SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: 5.2 [3.2, 7.4] | 0.0001 | 0.0044 | SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -0.7 [-3.0, 1.5] | 0.5452 | 1.0000 | NOT SUPPORTED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 1.1 [0.1, 2.1] | 0.0500 | 0.4500 | NOT SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 3.3 [0.6, 6.1]; IMMORTAL − GENES ONLINE: 11.9 [9.4, 14.5]; IMMORTAL − RANDOM ONLINE: 13.0 [10.7, 15.4] | 0.0275 | 0.2915 | NOT SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: -0.1 [-0.5, 0.4] | 0.6655 | 1.0000 | NOT SUPPORTED |
| S1 (secondary) | Longer teaching passes on more: FINAL_KNOWLEDGE TEACH16 > TEACH | yes | -0.3 [-0.8, 0.3] | 0.3796 | 1.0000 (secondary family) | NOT SUPPORTED |
| S2 (secondary) | FINAL_FRONTIER TEACH4 > IMMORTAL | lean no | 2.5 [0.4, 4.6] | 0.0295 | 0.2065 (secondary family) | NOT SUPPORTED |
| S3 (secondary) | ONLINE TEACH4 > IMMORTAL | lean no | -1.5 [-4.4, 1.3] | 0.3147 | 1.0000 (secondary family) | NOT SUPPORTED |
| S4 (secondary) | FINAL_FRONTIER TEACH16 > IMMORTAL | lean no | 3.9 [1.8, 6.5] | 0.0003 | 0.0030 (secondary family) | SUPPORTED |
| S5 (secondary) | ONLINE TEACH16 > IMMORTAL | lean no | -5.5 [-8.0, -2.9] | 0.0002 | 0.0022 (secondary family) | REVERSED |
| S6 (secondary) | ONLINE TEACH4 > RESET | lean no | -0.8 [-3.6, 1.9] | 0.5777 | 1.0000 (secondary family) | NOT SUPPORTED |

## Regime: new skill every 6 eras, lifespan 5 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 58.9 ± 6.7 | 0.0 ± 0.0 | 0.0 | 66.9 ± 1.5 | — | — |
| IMMORTAL | 74.7 ± 9.6 | 9.7 ± 4.8 | 3.5 | 52.3 ± 1.4 | 93.3 ± 3.6 | 43.1% |
| RESET | 83.4 ± 8.9 | 16.1 ± 6.5 | 4.2 | 55.9 ± 2.9 | 94.1 ± 3.8 | 34.4% |
| RESTART | 69.6 ± 9.7 | 6.2 ± 5.1 | 2.0 | 59.7 ± 3.1 | 62.7 ± 4.7 | 9.1% |
| TEACH | 71.8 ± 8.9 | 8.7 ± 5.7 | 2.5 | 56.7 ± 2.9 | 63.2 ± 4.6 | 20.3% |
| CLONE | 93.5 ± 8.9 | 11.6 ± 6.7 | 3.5 | 80.7 ± 16.2 | 80.1 ± 6.8 | 28.5% |
| GENES | 71.0 ± 11.3 | 3.3 ± 4.1 | 1.3 | 91.0 ± 12.3 | 50.3 ± 5.4 | 23.2% |
| RANDOM | 65.0 ± 12.6 | 2.5 ± 3.6 | 0.9 | 71.0 ± 14.3 | 41.6 ± 3.4 | 3.4% |
| TEACH4 | 71.3 ± 9.1 | 8.8 ± 4.0 | 3.1 | 57.0 ± 3.5 | 65.3 ± 4.9 | 18.2% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | 66.9 ± 1.5 | 58.9 ± 6.7 |
| IMMORTAL | 38.3 ± 4.4 | 7.9 ± 9.0 | 52.3 ± 1.4 | 74.7 ± 9.6 |
| RESET | 39.3 ± 5.1 | 12.5 ± 10.9 | 55.9 ± 2.9 | 83.4 ± 8.9 |
| RESTART | 22.1 ± 4.4 | 2.9 ± 6.3 | 59.7 ± 3.1 | 69.6 ± 9.7 |
| TEACH | 22.9 ± 4.8 | 4.6 ± 7.7 | 56.7 ± 2.9 | 71.8 ± 8.9 |
| CLONE | 29.9 ± 7.7 | 7.5 ± 8.4 | 57.2 ± 6.3 | 85.1 ± 10.8 |
| GENES | 11.4 ± 3.0 | 1.2 ± 3.8 | 59.5 ± 8.0 | 66.1 ± 9.5 |
| RANDOM | 9.3 ± 4.3 | 0.0 ± 0.0 | 64.4 ± 7.4 | 64.3 ± 9.3 |
| TEACH4 | 20.4 ± 4.5 | 6.2 ± 8.5 | 57.0 ± 3.5 | 71.3 ± 9.1 |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -3.0 [-3.9, -2.1] | 0.0001 | 0.0044 | SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: 3.5 [1.4, 5.7] | 0.0034 | 0.0544 | NOT SUPPORTED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 8.3 [5.8, 11.0] | 0.0001 | 0.0044 | SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: -3.0 [-6.4, 0.1] | 0.0889 | 0.7111 | NOT SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -30.1 [-31.3, -28.9] | 0.0001 | 0.0044 | REVERSED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 18.7 [15.4, 22.2] | 0.0001 | 0.0044 | SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: -11.6 [-14.0, -9.5] | 0.0001 | 0.0044 | REVERSED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -30.9 [-32.2, -29.7] | 0.0001 | 0.0044 | REVERSED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 8.7 [7.1, 10.4] | 0.0001 | 0.0044 | SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 13.2 [10.9, 15.4]; IMMORTAL − GENES ONLINE: 43.0 [41.7, 44.4]; IMMORTAL − RANDOM ONLINE: 51.7 [50.4, 52.9] | 0.0001 | 0.0044 | SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: 2.5 [0.9, 4.2] | 0.0128 | 0.1664 | NOT SUPPORTED |
| S2 (secondary) | FINAL_FRONTIER TEACH4 > IMMORTAL | lean no | -3.5 [-7.4, 0.3] | 0.1015 | 0.5074 (secondary family) | NOT SUPPORTED |
| S3 (secondary) | ONLINE TEACH4 > IMMORTAL | lean no | -28.0 [-29.6, -26.4] | 0.0001 | 0.0018 (secondary family) | REVERSED |
| S6 (secondary) | ONLINE TEACH4 > RESET | lean no | -28.8 [-30.7, -27.0] | 0.0001 | 0.0018 (secondary family) | REVERSED |

## Regime: new skill every 6 eras, lifespan 20 eras

| Arm | FRONTIER | KNOWLEDGE | deepest known (bits) | NOVEL | ONLINE (eras 61–120) | dead units |
|---|---|---|---|---|---|---|
| SCRATCH | 58.9 ± 6.7 | 0.0 ± 0.0 | 0.0 | 66.9 ± 1.5 | — | — |
| IMMORTAL | 74.7 ± 9.6 | 9.7 ± 4.8 | 3.5 | 52.3 ± 1.4 | 93.3 ± 3.6 | 43.1% |
| RESET | 78.9 ± 10.2 | 9.3 ± 4.7 | 3.6 | 53.1 ± 1.9 | 93.8 ± 4.6 | 41.4% |
| RESTART | 74.7 ± 10.6 | 13.5 ± 6.7 | 3.4 | 54.2 ± 2.2 | 77.0 ± 5.8 | 30.3% |
| TEACH | 74.3 ± 9.7 | 13.9 ± 6.4 | 3.6 | 54.0 ± 2.2 | 76.8 ± 5.3 | 31.0% |
| CLONE | 94.3 ± 7.9 | 16.7 ± 10.3 | 3.4 | 71.8 ± 16.3 | 79.9 ± 7.0 | 22.7% |
| GENES | 80.4 ± 12.6 | 6.7 ± 6.5 | 2.1 | 79.1 ± 16.7 | 52.8 ± 9.1 | 23.5% |
| RANDOM | 74.4 ± 14.5 | 5.7 ± 5.5 | 1.7 | 70.1 ± 13.8 | 46.7 ± 5.4 | 13.1% |
| TEACH4 | 74.0 ± 11.6 | 13.3 ± 5.6 | 3.5 | 53.9 ± 1.9 | 81.4 ± 5.7 | 30.8% |
| TEACH16 | 71.6 ± 9.3 | 11.6 ± 5.5 | 3.4 | 53.0 ± 1.5 | 74.8 ± 5.4 | 34.6% |

Secondary measures (not tested unless named in S1–S6):

| Arm | KNOWLEDGE, mean over checkpoints | newest 8 skills known | NOVEL at default lr | FRONTIER at default lr |
|---|---|---|---|---|
| SCRATCH | 0.0 ± 0.0 | 0.0 ± 0.0 | 66.9 ± 1.5 | 58.9 ± 6.7 |
| IMMORTAL | 38.3 ± 4.4 | 7.9 ± 9.0 | 52.3 ± 1.4 | 74.7 ± 9.6 |
| RESET | 37.4 ± 4.7 | 9.6 ± 8.5 | 53.1 ± 1.9 | 78.9 ± 10.2 |
| RESTART | 36.6 ± 4.4 | 8.3 ± 10.0 | 54.2 ± 2.2 | 74.7 ± 10.6 |
| TEACH | 37.1 ± 4.6 | 8.8 ± 9.9 | 54.0 ± 2.2 | 74.3 ± 9.7 |
| CLONE | 35.2 ± 7.7 | 7.9 ± 10.6 | 57.4 ± 5.5 | 89.7 ± 7.8 |
| GENES | 22.0 ± 8.6 | 4.2 ± 7.6 | 60.3 ± 6.0 | 76.6 ± 12.1 |
| RANDOM | 20.1 ± 5.7 | 0.8 ± 3.2 | 62.9 ± 6.7 | 73.4 ± 12.3 |
| TEACH4 | 36.8 ± 4.9 | 8.8 ± 10.5 | 53.9 ± 1.9 | 74.0 ± 11.6 |
| TEACH16 | 33.3 ± 5.2 | 5.8 ± 9.1 | 53.0 ± 1.5 | 71.6 ± 9.3 |

| # | Hypothesis | Predicted | Difference (pts, 95% CI) | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|
| H1 | IMMORTAL loses plasticity: NOVEL at the end < NOVEL at the first checkpoint | yes | IMMORTAL NOVEL@120 − IMMORTAL NOVEL@20 NOVEL: -3.0 [-3.9, -2.1] | 0.0001 | 0.0044 | SUPPORTED |
| H2a | Knowledge needs inheritance: FINAL_KNOWLEDGE IMMORTAL > RESTART | yes | IMMORTAL − RESTART FINAL_KNOWLEDGE: -3.8 [-6.5, -1.0] | 0.0195 | 0.2340 | NOT SUPPORTED |
| H2b | Weights carry knowledge, genes don't: FINAL_KNOWLEDGE CLONE > GENES | yes | CLONE − GENES FINAL_KNOWLEDGE: 10.0 [6.5, 13.8] | 0.0001 | 0.0044 | SUPPORTED |
| H3a | Teaching climbs better than immortality: FINAL_FRONTIER TEACH > IMMORTAL | yes | TEACH − IMMORTAL FINAL_FRONTIER: -0.4 [-3.3, 2.4] | 0.7888 | 1.0000 | NOT SUPPORTED |
| H3b | Teaching performs better on the stream: ONLINE TEACH > IMMORTAL | yes | TEACH − IMMORTAL ONLINE: -16.5 [-18.0, -15.0] | 0.0001 | 0.0044 | REVERSED |
| H3c | Weight copies escape plasticity loss: FINAL_FRONTIER CLONE > IMMORTAL | no | CLONE − IMMORTAL FINAL_FRONTIER: 19.5 [16.6, 22.8] | 0.0001 | 0.0044 | SUPPORTED |
| H4a | Teaching is more than a reset: FINAL_FRONTIER TEACH > RESET | lean yes | TEACH − RESET FINAL_FRONTIER: -4.6 [-7.9, -1.3] | 0.0107 | 0.1498 | NOT SUPPORTED |
| H4b | Teaching is more than a reset: ONLINE TEACH > RESET | lean yes | TEACH − RESET ONLINE: -17.0 [-18.9, -15.0] | 0.0001 | 0.0044 | REVERSED |
| H5 | Selection on learning settings helps: ONLINE GENES > RANDOM | yes | GENES − RANDOM ONLINE: 6.2 [2.4, 9.9] | 0.0025 | 0.0425 | SUPPORTED |
| H6 | Splitting compute is costly: ONLINE IMMORTAL > CLONE, GENES, RANDOM | yes | IMMORTAL − CLONE ONLINE: 13.4 [11.3, 15.5]; IMMORTAL − GENES ONLINE: 40.4 [37.3, 43.7]; IMMORTAL − RANDOM ONLINE: 46.6 [45.2, 48.3] | 0.0001 | 0.0044 | SUPPORTED |
| H7 | Teaching passes knowledge on: FINAL_KNOWLEDGE TEACH > RESTART | yes | TEACH − RESTART FINAL_KNOWLEDGE: 0.4 [-1.6, 2.3] | 0.6717 | 1.0000 | NOT SUPPORTED |
| S1 (secondary) | Longer teaching passes on more: FINAL_KNOWLEDGE TEACH16 > TEACH | yes | -2.3 [-4.5, -0.3] | 0.0490 | 0.2940 (secondary family) | NOT SUPPORTED |
| S2 (secondary) | FINAL_FRONTIER TEACH4 > IMMORTAL | lean no | -0.8 [-4.0, 2.3] | 0.6403 | 1.0000 (secondary family) | NOT SUPPORTED |
| S3 (secondary) | ONLINE TEACH4 > IMMORTAL | lean no | -11.8 [-13.4, -10.3] | 0.0001 | 0.0018 (secondary family) | REVERSED |
| S4 (secondary) | FINAL_FRONTIER TEACH16 > IMMORTAL | lean no | -3.2 [-5.8, -0.8] | 0.0221 | 0.1768 (secondary family) | NOT SUPPORTED |
| S5 (secondary) | ONLINE TEACH16 > IMMORTAL | lean no | -18.5 [-20.2, -16.8] | 0.0001 | 0.0018 (secondary family) | REVERSED |
| S6 (secondary) | ONLINE TEACH4 > RESET | lean no | -12.4 [-14.2, -10.4] | 0.0001 | 0.0018 (secondary family) | REVERSED |
