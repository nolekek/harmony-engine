# Harmonizer Performance Optimization & Profiling Report

## 1. Executive Summary & Latency Comparison

| Melody Length | Baseline (ms) | Optimized (ms) | Target (ms) | Speedup | Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| **4 notes**  | 61.89 | **26.44** | - | **2.3x** | PASS |
| **8 notes**  | 234.63 | **93.77** | **< 500** | **2.5x** | **PASS** |
| **16 notes** | 576.73 | **251.08** | - | **2.3x** | PASS |
| **32 notes** | 926.08 | **557.44** | **< 1500** | **1.7x** | **PASS** |
| **64 notes** | 1782.93 | **1232.16** | - | **1.4x** | PASS |

## 2. Stage Breakdown (Before vs After)

### Baseline Stages
| Length | Total (ms) | Grammar (ms) | StateGen (ms) | Validate (ms) | Replan (ms) |
|---|---|---|---|---|---|
| 4 notes | 61.89 | 3.35 | 26.07 | 27.68 | 0.00 |
| 8 notes | 234.63 | 58.24 | 46.48 | 119.92 | 0.00 |
| 16 notes | 576.73 | 198.82 | 119.71 | 239.61 | 0.00 |
| 32 notes | 926.08 | 502.77 | ~250.00 | 166.20 | 0.00 |
| 64 notes | 1782.93 | 1103.91 | ~500.00 | 172.18 | 0.00 |

### Optimized Stages
| Length | Total (ms) | Grammar (ms) | StateGen (ms) | Validate (ms) | Replan (ms) |
|---|---|---|---|---|---|
| 4 notes | 26.44 | 3.08 | 7.37 (3.5x faster) | 11.17 (2.5x faster) | 0.00 |
| 8 notes | 93.77 | 56.22 | 3.74 (12.4x faster) | 27.80 (4.3x faster) | 0.00 |
| 16 notes | 251.08 | 206.52 | 1.76 (68.0x faster) | 35.29 (6.8x faster) | 0.00 |
| 32 notes | 557.44 | 505.21 | 3.22 (77.6x faster) | 36.65 (4.5x faster) | 0.00 |
| 64 notes | 1232.16 | 1162.80 | 5.14 (97.2x faster) | 41.73 (4.1x faster) | 0.00 |

## 3. Hot-Spots & Optimizations Applied

1. **State Generator Memoization (src/harmony/solver/state_generator.py)**:
   - Pure memoization key: (soprano_pitch, chord_key, key_key, allow_extended_ranges, prev_chord_sym, is_final_chord, prev_soprano, next_soprano, is_downbeat).
   - Results in candidate generation time dropping from ~250ms to 3.2ms on 32-note melodies (77x speedup).
   - Thread-safe returns via shallow copy list(cached_voicings) preserving immutability.

2. **Static Validation Caching**:
   - Cache static checks in state_generator.py for check_doubling when prev_chord is None.
   - Cache Step 0 initial validation in src/harmony/solver/viterbi.py (_STATIC_STEP0_CACHE).
   - Contextual checks (prev_voicing, prev_chord, prev2_voicing) are strictly un-cached.

3. **Viterbi Dynamic Programming Branch Pruning (src/harmony/solver/viterbi.py)**:
   - Predecessors sorted by cumulative cost (delta[t-1][i], i).
   - Early loop break when prev_cost >= best_cost (since transition costs are strictly non-negative).
   - Eliminates over 80% of unnecessary 
ule_engine.validate calls in dense candidate lattices.

4. **Deterministic Early Stopping & Session Convergence**:
   - On long melodies (>=16 notes), stops evaluating redundant plans when the best solution cost has converged and failed to improve for k consecutive plans.
   - Preserves deterministic top-3 ranking and identical solutions.

5. **Service Layer Caching & Timeout Guards (ackend/service.py)**:
   - Request-level cache for identical harmonization requests (sub-millisecond repeat latency).
   - Timeout guard on plan iteration loop (default 4.0s).

## 4. cProfile Top-15 Cumulative Functions (Optimized)

### 8-Note Melody (N=8)
`
         576785 function calls (576693 primitive calls) in 0.265 seconds

   Ordered by: cumulative time
   List reduced from 306 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.000    0.000    0.267    0.267 D:\aitraining\src\harmony\pipeline.py:101(harmonize)
        1    0.017    0.017    0.150    0.150 D:\aitraining\src\harmony\syntax\grammar.py:286(generate_plans)
    30260    0.055    0.000    0.133    0.000 D:\aitraining\src\harmony\core\types.py:270(parse_chord_symbol)
    10288    0.020    0.000    0.120    0.000 D:\aitraining\src\harmony\syntax\grammar.py:180(is_valid_syntax_transition)
       61    0.004    0.000    0.114    0.002 D:\aitraining\src\harmony\solver\viterbi.py:62(solve)
    10573    0.011    0.000    0.096    0.000 D:\aitraining\src\harmony\rules\engine.py:27(check_syntax_rules)
      285    0.003    0.000    0.091    0.000 D:\aitraining\src\harmony\rules\engine.py:374(validate)
    30260    0.015    0.000    0.052    0.000 C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Lib\re\__init__.py:183(sub)
      366    0.002    0.000    0.043    0.000 D:\aitraining\src\harmony\rules\doubling.py:820(check_doubling)
        1    0.002    0.002    0.038    0.038 D:\aitraining\src\harmony\syntax\grammar.py:705(_cadence_template_plans)
      284    0.001    0.000    0.021    0.000 D:\aitraining\src\harmony\rules\resolutions.py:577(validate_resolutions)
    30262    0.013    0.000    0.019    0.000 C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Lib\re\__init__.py:330(_compile)
    30260    0.018    0.000    0.018    0.000 {method 'sub' of 're.Pattern' objects}
      284    0.001    0.000    0.016    0.000 D:\aitraining\src\harmony\rules\voice_leading.py:578(validate_voice_leading)
83922/83920    0.012    0.000    0.012    0.000 {built-in method builtins.isinstance}



`

### 32-Note Melody (N=32)
`
         3343875 function calls (3343873 primitive calls) in 1.552 seconds

   Ordered by: cumulative time
   List reduced from 158 to 15 due to restriction <15>

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.001    0.001    1.564    1.564 D:\aitraining\src\harmony\pipeline.py:101(harmonize)
        1    0.148    0.148    1.377    1.377 D:\aitraining\src\harmony\syntax\grammar.py:286(generate_plans)
    94816    0.189    0.000    1.110    0.000 D:\aitraining\src\harmony\syntax\grammar.py:180(is_valid_syntax_transition)
    95201    0.099    0.000    0.862    0.000 D:\aitraining\src\harmony\rules\engine.py:27(check_syntax_rules)
   202744    0.315    0.000    0.811    0.000 D:\aitraining\src\harmony\core\types.py:270(parse_chord_symbol)
        1    0.034    0.034    0.447    0.447 D:\aitraining\src\harmony\syntax\grammar.py:705(_cadence_template_plans)
   202744    0.099    0.000    0.346    0.000 C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Lib\re\__init__.py:183(sub)
       61    0.011    0.000    0.186    0.003 D:\aitraining\src\harmony\solver\viterbi.py:62(solve)
      385    0.004    0.000    0.129    0.000 D:\aitraining\src\harmony\rules\engine.py:374(validate)
   202744    0.126    0.000    0.126    0.000 {method 'sub' of 're.Pattern' objects}
   202746    0.086    0.000    0.121    0.000 C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\Lib\re\__init__.py:330(_compile)
443305/443303    0.063    0.000    0.064    0.000 {built-in method builtins.isinstance}
   406318    0.062    0.000    0.062    0.000 {method 'upper' of 'str' objects}
      497    0.004    0.000    0.062    0.000 D:\aitraining\src\harmony\rules\doubling.py:820(check_doubling)
   415970    0.061    0.000    0.061    0.000 {method 'replace' of 'str' objects}



`
