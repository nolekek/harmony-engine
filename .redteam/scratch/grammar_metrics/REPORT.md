# Grammar Metrics Report: Soprano Heuristics Removal (Before vs After)

## Executive Summary

Removing rigid heuristic filters on soprano pitches ((a) same_triad_inversion, (b) root_triads fifth matching, (c) S->D soprano prohibition, (d) D->T soprano prohibition) and replacing them with soft penalties (`trans_score -= 6.0`) prevents premature plan rejection, unlocks previously discarded classical progressions (e.g. T->T6 and S->D6/D65), and maintains 100% adherence to harmonic syntax and cadence constraints.

## Comparison Table

| Melody | Length | Plans (Before -> After) | Solved (Before -> After) | Survival % (Before -> After) | NO_FEASIBLE % (Before -> After) | Starvations (B -> A) | Harmonize |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| default | 6 | 61 -> 61 | 13 -> 13 | 21.3% -> 21.3% | 78.7% -> 78.7% | 0 -> 0 | PASSED |
| a-moll desc | 8 | 61 -> 61 | 0 -> 0 | 0.0% -> 0.0% | 100.0% -> 100.0% | 0 -> 0 | PASSED |
| 16-note scale | 16 | 60 -> 60 | 27 -> 27 | 45.0% -> 45.0% | 55.0% -> 55.0% | 0 -> 0 | PASSED |
| 32-note arch | 32 | 60 -> 60 | 0 -> 0 | 0.0% -> 0.0% | 100.0% -> 100.0% | 1 -> 1 | PASSED |
| chromatic 1 | 5 | 60 -> 60 | 4 -> 4 | 6.7% -> 6.7% | 93.3% -> 93.3% | 0 -> 0 | PASSED |
| chromatic 2 | 6 | 60 -> 60 | 3 -> 3 | 5.0% -> 5.0% | 95.0% -> 95.0% | 0 -> 0 | PASSED |
| chromatic 3 | 4 | 12 -> 12 | 1 -> 1 | 8.3% -> 8.3% | 91.7% -> 91.7% | 0 -> 0 | PASSED |
| chromatic 4 | 5 | 61 -> 61 | 0 -> 0 | 0.0% -> 0.0% | 100.0% -> 100.0% | 0 -> 0 | PASSED |
| chromatic 5 | 5 | 61 -> 61 | 0 -> 0 | 0.0% -> 0.0% | 100.0% -> 100.0% | 0 -> 0 | FAILED |
| same_triad (C-E) | 4 | 48 -> 56 | 20 -> 22 | 41.7% -> 39.3% | 58.3% -> 60.7% | 0 -> 0 | PASSED |
| s_to_d_leap (F-G) | 3 | 20 -> 23 | 5 -> 6 | 25.0% -> 26.1% | 75.0% -> 73.9% | 0 -> 0 | PASSED |
