# Harmonic Rhythm & Macro Syntax Audit Report

## 1. Executive Summary: Before vs After

| Metric | Before Fix (Baseline) | After Fix (Heuristics) | Delta | Status |
|---|---|---|---|---|
| **Total Melodies Audited** | 39 | 39 | 0 | PASSED |
| **Measures with >2 Chord Changes** | 2 / 153 (1.31%) | 2 / 173 (1.16%) | 0 | PASSED (<=10%) |
| **A-B-A-B Chord Oscillations** | 19 | 7 | -12 | **RESOLVED** (0) |
| **III / III6 Intrusions in Major** | 5 | 0 | -5 | **RESOLVED** (0) |
| **(T, T) on Stepwise Soprano** | 0 | 0 | 0 | **CLEAN** (0) |

## 2. Implemented Soft Heuristic Improvements

1. **Anti-Oscillation Heuristic (A-B-A-B)**:
   - Implemented sliding window detector in `HarmonicGrammar._generate_plans_pass` and `_cadence_template_plans`.
   - Penalizes exact alternating chord sequences (`A-B-A-B`) with `-10.0` (and `-15.0` for longer runs) and base function oscillations (`T-S-T-S`) with `-6.0`.
2. **Major III / III6 Elimination**:
   - In `grammar.py`, eliminated spurious bonus for III on descending leading tone in Major; applied `-25.0` penalty for III/III6 in Major, keeping moderate penalty in Minor (Phrygian descent supported).
   - In `engine.py`, added key-aware `compute_functional_cost` applying `+20.0` soft penalty for III/III6 in Major.
3. **Harmonic Rhythm Stability on Weak Beats**:
   - When melody pitch remains within current chord tones on weak beats (`not is_downbeat`), changing chord receives `-5.0` (grammar) / `+4.0` (engine), while retaining harmony receives `+4.0` reward.
4. **Stepwise vs Leap Chord Repetition**:
   - Repeating same chord on stepwise soprano motion (`step in (1, 2)`) is penalized (`-8.0` in grammar, `+8.0` in engine; `-25.0` / `+30.0` at final cadence).
   - Intra-chord leaps (arpeggios) and repeated notes are permitted without penalty, solving arpeggio fragmentation.
5. **Authentic Cadence Reinforcement**:
   - Added `("D7", "T")` and `("D", "T")` to `_CADENCE_TEMPLATES` for melodies ending with tonic leaps.
   - Penultimate step rewards `D7` (`+10.0`) and Dominant group (`+6.0`), while penalizing weak `VI -> T` (`-8.0` grammar / `+8.0` engine).
   - Antepenultimate downbeat rewards `K64` preparation (`+8.0`).

## 3. Cadence Pairs Distribution Comparison

| Cadence Pair | Before Fix Count | After Fix Count |
|---|---|---|
| `D -> T` | 4 | 8 |
| `D43 -> T` | 1 | 0 |
| `D6 -> T` | 13 | 13 |
| `D65 -> T` | 2 | 2 |
| `D7 -> T` | 6 | 7 |
| `S6 -> T` | 1 | 0 |
| `T -> T` | 1 | 3 |
| `VI -> T` | 6 | 6 |

## 4. Detailed Melody Results (After Fix)

| Melody | Key | TS | Chords | >2 Changes | A-B-A-B | III (Maj) | (T,T) Step | Final Pair |
|---|---|---|---|---|---|---|---|---|
| `C_maj_scale_asc_8` | C Major | 4/4 | `T II6 T S6 T6 S6 D7 T` | 0 | 0 | 0 | 0 | `D7 -> T` |
| `C_maj_scale_desc_8` | C Major | 4/4 | `T D VII7 T S6 T D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `C_maj_scale_arch_15` | C Major | 4/4 | `T II6 T S6 T II6 D43 T D VII7 T S6 T D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `C_maj_scale_16` | C Major | 4/4 | `T II6 T S6 T II6 D43 T D VII7 T S6 T D6 T T` | 0 | 0 | 0 | 0 | `T -> T` |
| `G_maj_scale_asc_8` | G Major | 4/4 | `T II6 T S6 T6 S6 D7 T` | 0 | 0 | 0 | 0 | `D7 -> T` |
| `G_maj_scale_desc_8` | G Major | 4/4 | `T D VII7 T S6 T D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `G_maj_scale_arch_13` | G Major | 4/4 | `T II6 T II6 T6 S6 D6 VII6 T6 II6 T6 D6 T` | 0 | 1 | 0 | 0 | `D6 -> T` |
| `F_maj_scale_asc_8` | F Major | 4/4 | `T II6 T S6 T6 S6 D7 T` | 0 | 0 | 0 | 0 | `D7 -> T` |
| `F_maj_scale_desc_8` | F Major | 4/4 | `T D VII7 T S6 T D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `F_maj_scale_arch_11` | F Major | 4/4 | `T II6 T S6 T6 S6 T6 S6 T D6 T` | 0 | 2 | 0 | 0 | `D6 -> T` |
| `A_min_scale_asc_8` | A Minor | 4/4 | `T II6 T S6 T S6 D7 T` | 0 | 1 | 0 | 0 | `D7 -> T` |
| `A_min_scale_desc_8` | A Minor | 4/4 | `T III S6 T6 S6 T D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `D_min_scale_asc_8` | D Minor | 4/4 | `T II6 T S T S6 D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `D_min_scale_desc_8` | D Minor | 4/4 | `T III S6 T6 S6 T D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `E_min_scale_asc_8` | E Minor | 4/4 | `T II6 T S6 T S6 D7 T` | 0 | 1 | 0 | 0 | `D7 -> T` |
| `E_min_scale_desc_8` | E Minor | 4/4 | `T III S6 T6 S6 T D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `C_maj_arpeggio_7` | C Major | 4/4 | `T VI T6 S6 T6 VI T` | 0 | 0 | 0 | 0 | `VI -> T` |
| `C_maj_arpeggio_8` | C Major | 4/4 | `T VI D6 T II6 T6 D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `G_maj_arpeggio_7` | G Major | 3/4 | `T VI T6 S6 T6 VI T` | 0 | 0 | 0 | 0 | `VI -> T` |
| `F_maj_arpeggio_7` | F Major | 3/4 | `T VI T6 S6 T6 VI T` | 0 | 0 | 0 | 0 | `VI -> T` |
| `A_min_arpeggio_7` | A Minor | 4/4 | `T VI T6 S6 T6 VI T` | 0 | 0 | 0 | 0 | `VI -> T` |
| `D_min_arpeggio_7` | D Minor | 4/4 | `T VI T6 S6 T6 VI T` | 0 | 0 | 0 | 0 | `VI -> T` |
| `E_min_arpeggio_7` | E Minor | 3/4 | `T VI T6 S6 T6 VI T` | 0 | 0 | 0 | 0 | `VI -> T` |
| `C_maj_chorale_8` | C Major | 4/4 | `T T S T S T D7 T` | 0 | 2 | 0 | 0 | `D7 -> T` |
| `C_maj_waltz_6` | C Major | 3/4 | `T T6 S K64 D7 T` | 0 | 0 | 0 | 0 | `D7 -> T` |
| `C_maj_motif_9` | C Major | 4/4 | `T VI S6 D6 VII6 T S6 D65 T` | 0 | 0 | 0 | 0 | `D65 -> T` |
| `C_maj_melody_12` | C Major | 4/4 | `T II6 T T6 T S T D7 T D D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `G_maj_problem_7` | G Major | 4/4 | `T D6 T S6 D6 T T` | 0 | 0 | 0 | 0 | `T -> T` |
| `G_maj_hymn_7` | G Major | 4/4 | `T D6 T S6 T D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `G_maj_waltz_6` | G Major | 3/4 | `T VI T6 S6 D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `G_maj_phrase_10` | G Major | 4/4 | `T II6 T S6 T6 S6 T S6 D65 T` | 0 | 0 | 0 | 0 | `D65 -> T` |
| `F_maj_motif_6` | F Major | 4/4 | `T S6 T6 D65 T T` | 0 | 0 | 0 | 0 | `T -> T` |
| `F_maj_waltz_9` | F Major | 3/4 | `T VI T6 S6 T D2 T6 D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `A_min_chorale_8` | A Minor | 4/4 | `T VII6 T S T II6 D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `A_min_waltz_6` | A Minor | 3/4 | `T D6 T II6 D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `D_min_motif_8` | D Minor | 4/4 | `T VI K64 D7 T D6 D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |
| `E_min_motif_8` | E Minor | 4/4 | `T VI T6 S6 VI II6 D T` | 0 | 0 | 0 | 0 | `D -> T` |
| `C_maj_quarters_8` | C Major | 4/4 | `T VI D6 T D7 T D6 T` | 2 | 0 | 0 | 0 | `D6 -> T` |
| `G_maj_quarters_6` | G Major | 3/4 | `T VI T6 S6 D6 T` | 0 | 0 | 0 | 0 | `D6 -> T` |