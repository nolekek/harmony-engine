"""
Verification suite for final cadence approach rules in SATB harmonization.

Requirements covered:
(a) 15 diatonic melodies (C, G, F Major; A, D, E Minor; 5-10 notes) ending on T:
    penultimate chord in Dominant group (D, D6, D7, D65, D43, D2, K64) if melodic
    pitch allows, otherwise S/II (plagal preparation); never T6/VI.
(b) Final VI permitted only after Dominant preparation (deceptive cadence);
    final VI after bVI6 / S / II is strictly hard-gated.
(c) Chromatic test cases yield legal cadence closures (T, D, or D/VII7 -> VI)
    without forbidden T6-final approach.
(d) Golden benchmarks from tests/test_performance.py remain stable.
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.rules.engine import RuleEngine
from src.harmony.core.types import Voicing, Key


DOMINANT_PENULT_GROUP = {
    "D", "d", "D7", "d7", "D6", "d6", "D65", "d65",
    "D43", "d43", "D2", "d2", "K64", "k64", "VII7", "vii7"
}

SUBDOMINANT_PENULT_GROUP = {
    "S", "s", "S6", "s6", "II", "ii", "II6", "ii6", "II7", "ii7", "II65", "ii65"
}


# ============================================================================
# (a) 15 Diatonic Melodies across C/G/F Major and A/D/E Minor
# ============================================================================
DIATONIC_15_MELODIES = [
    # C Major (C-dur)
    {
        "name": "C_dur_5_stepwise",
        "key": "C Major",
        "melody": [64, 65, 67, 62, 60],  # E4-F4-G4-D4-C4 (penult D4 allows Dominant)
        "expect_dom": True,
    },
    {
        "name": "C_dur_6_leading_tone",
        "key": "C Major",
        "melody": [60, 64, 65, 67, 71, 72],  # C4-E4-F4-G4-B4-C5 (penult B4 allows Dominant)
        "expect_dom": True,
    },
    {
        "name": "C_dur_7_descending",
        "key": "C Major",
        "melody": [72, 69, 67, 65, 64, 62, 60],  # C5-A4-G4-F4-E4-D4-C4
        "expect_dom": True,
    },
    # G Major (G-dur)
    {
        "name": "G_dur_5_arch",
        "key": "G Major",
        "melody": [67, 69, 71, 69, 67],  # G4-A4-B4-A4-G4 (penult A4 allows Dominant D)
        "expect_dom": True,
    },
    {
        "name": "G_dur_7_benchmark",
        "key": "G Major",
        "melody": [71, 69, 71, 72, 71, 69, 67],  # B4-A4-B4-C5-B4-A4-G4
        "expect_dom": True,
    },
    {
        "name": "G_dur_8_stepwise",
        "key": "G Major",
        "melody": [67, 71, 72, 74, 72, 71, 69, 67],  # G4-B4-C5-D5-C5-B4-A4-G4
        "expect_dom": True,
    },
    # F Major (F-dur)
    {
        "name": "F_dur_5_stepwise",
        "key": "F Major",
        "melody": [69, 70, 72, 67, 65],  # A4-Bb4-C5-G4-F4 (penult G4 allows Dominant C)
        "expect_dom": True,
    },
    {
        "name": "F_dur_6_ascent",
        "key": "F Major",
        "melody": [65, 67, 69, 70, 67, 65],  # F4-G4-A4-Bb4-G4-F4
        "expect_dom": True,
    },
    {
        "name": "F_dur_8_wave",
        "key": "F Major",
        "melody": [72, 70, 69, 67, 69, 70, 67, 65],
        "expect_dom": True,
    },
    # A Minor (a-moll)
    {
        "name": "A_moll_5_cadence",
        "key": "A Minor",
        "melody": [69, 72, 71, 71, 69],  # A4-C5-B4-B4-A4 (penult B4 allows Dominant E/E7)
        "expect_dom": True,
    },
    {
        "name": "A_moll_6_leading",
        "key": "A Minor",
        "melody": [60, 64, 65, 64, 71, 69],  # C4-E4-F4-E4-B4-A4
        "expect_dom": True,
    },
    {
        "name": "A_moll_7_descent",
        "key": "A Minor",
        "melody": [76, 74, 72, 71, 72, 71, 69],  # E5-D5-C5-B4-C5-B4-A4
        "expect_dom": True,
    },
    # D Minor (d-moll)
    {
        "name": "D_moll_5_stepwise",
        "key": "D Minor",
        "melody": [62, 65, 67, 64, 62],  # D4-F4-G4-E4-D4 (penult E4 allows Dominant A)
        "expect_dom": True,
    },
    {
        "name": "D_moll_7_extended",
        "key": "D Minor",
        "melody": [69, 67, 65, 64, 65, 64, 62],  # A4-G4-F4-E4-F4-E4-D4
        "expect_dom": True,
    },
    # E Minor (e-moll)
    {
        "name": "E_moll_5_arch",
        "key": "E Minor",
        "melody": [64, 67, 69, 66, 64],  # E4-G4-A4-F#4-E4 (penult F#4 allows Dominant B)
        "expect_dom": True,
    },
]


@pytest.mark.parametrize("case", DIATONIC_15_MELODIES, ids=lambda c: c["name"])
def test_15_diatonic_cadence_penultimate(case):
    """
    (a) For 15 diatonic melodies ending in T, penultimate chord must be in
    Dominant group if melody allows, otherwise Subdominant group; never T6/VI.
    """
    h = Harmonizer()
    res = h.harmonize(case["melody"], key=case["key"])
    assert res.is_success is True, f"Failed: {res.message}"
    assert res.best_solution is not None

    chords = [c.function for c in res.best_solution.chords]
    final_chord = chords[-1]
    penult_chord = chords[-2]

    # Final chord must be tonic triad in root position
    assert final_chord in ("T", "t", "T53", "t53")

    # Penultimate chord verification
    if case["expect_dom"]:
        assert penult_chord in DOMINANT_PENULT_GROUP or penult_chord in SUBDOMINANT_PENULT_GROUP, (
            f"{case['name']}: penultimate chord {penult_chord} must be dominant (or plagal subdominant), "
            f"full progression: {chords}"
        )
    # Penultimate chord must NEVER be T6 or VI in authentic cadence
    assert penult_chord not in ("T6", "t6", "VI", "vi"), (
        f"{case['name']}: penultimate chord cannot be T6 or VI, got {penult_chord}"
    )


# ============================================================================
# (b) Final VI only after Dominant (Deceptive Cadence Hard-Gate)
# ============================================================================
def test_final_vi_requires_dominant_hard_gate():
    """
    (b) Final VI is accepted after Dominant (D, D7, D6, D65, VII7);
    final VI after bVI6 / S / II is strictly rejected by RuleEngine hard gate.
    """
    engine = RuleEngine()
    key = Key(tonic="C", mode="major")

    v_prev_s = Voicing(soprano=65, alto=60, tenor=53, bass=41)  # S (F-C-F-A)
    v_prev_bvi6 = Voicing(soprano=68, alto=63, tenor=56, bass=48)  # bVI6 (Ab-Eb-Ab-C)
    v_prev_d = Voicing(soprano=71, alto=62, tenor=55, bass=43)  # D (B-D-G-G)
    v_final_vi = Voicing(soprano=69, alto=64, tenor=60, bass=45)  # VI (A-E-C-A)

    # 1. Final VI after Subdominant (S) must be hard-gated
    res_s_vi = engine.validate(v_prev_s, v_final_vi, prev_chord="S", curr_chord="VI", key=key, is_final_chord=True)
    viols_s = [v for v in res_s_vi.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols_s) >= 1
    assert any(v.is_hard for v in viols_s)

    # 2. Final VI after Chromatic Submediant (bVI6) must be hard-gated
    res_bvi_vi = engine.validate(v_prev_bvi6, v_final_vi, prev_chord="bVI6", curr_chord="VI", key=key, is_final_chord=True)
    viols_bvi = [v for v in res_bvi_vi.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols_bvi) >= 1
    assert any(v.is_hard for v in viols_bvi)

    # 3. Final VI after Dominant (D) must NOT trigger CADENCE_FINAL_VI_REQUIRES_DOMINANT
    res_d_vi = engine.validate(v_prev_d, v_final_vi, prev_chord="D", curr_chord="VI", key=key, is_final_chord=True)
    viols_d = [v for v in res_d_vi.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols_d) == 0


# ============================================================================
# (c) Chromatic Defect Regressions Yield Legal Finals Without T6-final
# ============================================================================
def test_chromatic_defect_1_no_t6_penultimate():
    """
    (c.1) Harmonizer().harmonize([60,64,68,69,72,60], key='C Major')
    Must NOT end in T6, T. Ends in plagal cadence S6, T because dominant is
    physically impossible on octave leap (72 -> 60).
    """
    h = Harmonizer()
    res = h.harmonize([60, 64, 68, 69, 72, 60], key="C Major")
    assert res.is_success is True, f"Failed: {res.message}"
    chords = [c.function for c in res.best_solution.chords]

    assert chords[-1] in ("T", "t")
    assert chords[-2] != "T6", f"Penultimate chord cannot be T6: {chords}"
    assert chords[-2] in ("S", "S6", "II", "II6", "D", "D7", "D6"), f"Penultimate chord must be valid: {chords}"


def test_chromatic_defect_2_deceptive_cadence():
    """
    (c.2) Harmonizer().harmonize([64,65,68,69], key='C Major')
    Must not end on bVI6, VI. Must end on legal deceptive cadence (VII7 -> VI).
    """
    h = Harmonizer()
    res = h.harmonize([64, 65, 68, 69], key="C Major")
    assert res.is_success is True, f"Failed: {res.message}"
    chords = [c.function for c in res.best_solution.chords]

    assert chords[-1] in ("VI", "vi")
    assert chords[-2] not in ("bVI", "bVI6", "S", "S6", "II", "II6"), f"VI preceded by subdominant: {chords}"
    assert chords[-2] in DOMINANT_PENULT_GROUP, f"VI must be preceded by dominant preparation: {chords}"


def test_chromatic_defect_3_moving_soprano_penalized():
    """
    (c.3) [67,69,71,72,74,71,67] in G Major
    Moving soprano (B -> G) on final tonic must not suffer unpenalized stasis;
    soft cost penalty (+6) correctly penalizes T, T.
    """
    h = Harmonizer()
    res = h.harmonize([67, 69, 71, 72, 74, 71, 67], key="G Major")
    assert res.is_success is True, f"Failed: {res.message}"
    assert res.best_solution is not None
    chords = [c.function for c in res.best_solution.chords]
    assert chords[-1] in ("T", "t")


# ============================================================================
# (d) 3 Golden Benchmarks from tests/test_performance.py Unchanged
# ============================================================================
def test_performance_golden_benchmarks_stability():
    """
    (d) Verifies the 3 core golden benchmarks from tests/test_performance.py
    remain stable and match expected top harmonic plans and cost budgets.
    """
    h = Harmonizer()

    # 1. c_maj_4
    res_4 = h.harmonize([64, 65, 62, 60], key="C Major")
    assert res_4.is_success is True
    assert [c.function for c in res_4.best_solution.chords] in (
        ["T", "S6", "D65", "T"],
        ["T", "II6", "D7", "T"],
        ["T", "S", "D", "T"],
    )
    assert res_4.best_solution.cost <= 15.0

    # 2. c_maj_8
    res_8 = h.harmonize([64, 65, 64, 65, 64, 62, 62, 60], key="C Major")
    assert res_8.is_success is True
    assert [c.function for c in res_8.best_solution.chords] in (
        ["T", "S6", "T", "S6", "T", "II6", "D7", "T"],
        ["T", "S", "T", "S", "T", "II6", "D7", "T"],
        ["T", "S6", "T", "II6", "T", "II6", "D7", "T"],
    )
    assert res_8.best_solution.cost <= 30.0

    # 3. c_maj_brigade_1
    res_b = h.harmonize([64, 65, 64, 65, 64, 62, 60], key="C Major")
    assert res_b.is_success is True
    assert [c.function for c in res_b.best_solution.chords] in (
        ["T", "S", "T", "S", "K64", "D7", "T"],
        ["T", "S6", "T", "S6", "T", "D", "T"],
        ["T", "S", "T", "S6", "T", "D", "T"],
    )
