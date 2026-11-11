"""
Tests for voice leading, resolution, doubling, and viterbi cost fixes (T18).
"""
import pytest
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.rules.engine import RuleEngine
from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_melodic_intervals,
)
from src.harmony.rules.resolutions import check_seventh_resolution
from src.harmony.rules.doubling import (
    check_seventh_chord_doubling,
    check_sextaccord_doubling,
)
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver


def test_d7_to_d65_repositioning_sustained_seventh():
    """(a) D7 -> D65 with sustained/repositioned seventh is NOT a violation."""
    engine = RuleEngine()
    key = Key(tonic="C", mode="Major")
    chord_d7 = Chord(function="D7")
    chord_d65 = Chord(function="D65")

    # In C major, D7: G3 (root), B3 (third), D4 (fifth), F4 (seventh, pc=5).
    # S=F4 (65, 7th), A=D4 (62), T=B3 (59), B=G2 (43)
    # D65: S stays on F4 (65, delta=0), A=D4 (62), T=G3 (55), B=B2 (47, third in bass)
    v1 = Voicing(soprano=65, alto=62, tenor=59, bass=43)
    v2 = Voicing(soprano=65, alto=62, tenor=55, bass=47)

    res = engine.validate(v1, v2, prev_chord=chord_d7, curr_chord=chord_d65, key=key)
    seventh_viols = [v for v in res.violations if v.rule_id == "RESOLUTION_SEVENTH_DOWN"]
    assert len(seventh_viols) == 0, f"Sustained seventh in D7->D65 shouldn't violate RESOLUTION_SEVENTH_DOWN: {seventh_viols}"


def test_dim5_to_p5_similar_motion():
    """(b) Diminished 5th to Perfect 5th in similar motion IS a violation (PARALLEL_DIM5_P5)."""
    # Prev: Tenor F3 (53), Bass B2 (47) -> interval = 6 (dim 5th)
    # Curr: Tenor G3 (55), Bass C3 (48) -> interval = 7 (perfect 5th)
    # Both move up in similar motion: dT = +2, dB = +1 (dT * dB > 0).
    v1 = Voicing(soprano=72, alto=60, tenor=53, bass=47)
    v2 = Voicing(soprano=72, alto=60, tenor=55, bass=48)

    viols = check_parallel_fifths_and_octaves(v1, v2)
    dim5_p5 = [v for v in viols if v.rule_id == "PARALLEL_DIM5_P5"]
    assert len(dim5_p5) > 0, "dim5 -> P5 in similar motion must trigger PARALLEL_DIM5_P5 violation"


def test_octave_repositioning_same_chord():
    """(c) Octave shift within the same chord is NOT a violation."""
    engine = RuleEngine()
    chord_t = Chord(function="T")
    key = Key(tonic="C", mode="Major")

    # C major triad: S leaps octave down G4(67) -> G3(55), B leaps octave down C3(48) -> C2(36)
    v1 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
    v2 = Voicing(soprano=55, alto=60, tenor=55, bass=36)

    # Within same chord:
    viols = check_parallel_fifths_and_octaves(v1, v2, prev_chord=chord_t, curr_chord=chord_t)
    assert not any(v.rule_id in ("PARALLEL_FIFTHS", "PARALLEL_OCTAVES") for v in viols)

    viols_contrary = check_contrary_fifths_and_octaves(v1, v2, prev_chord=chord_t, curr_chord=chord_t)
    assert not any(v.rule_id in ("CONTRARY_FIFTHS", "CONTRARY_OCTAVES") for v in viols_contrary)


def test_incomplete_vii7_with_doubled_leading_tone():
    """(d) Incomplete VII7 with doubled leading tone IS a violation."""
    key = Key(tonic="C", mode="Major")
    chord_vii7 = Chord(function="VII7")

    # In C major: VII7 = B, D, F, Ab.
    # Incomplete with doubled root B (leading tone!): B2(47), B3(59), D4(62), Ab4(68) - fifth F omitted
    v_bad = Voicing(soprano=68, alto=62, tenor=59, bass=47)
    viols = check_seventh_chord_doubling(v_bad, chord_vii7, key=key)
    assert any(v.rule_id == "SEVENTH_CHORD_DISTRIBUTION" for v in viols)

    # Complete VII7 is valid:
    v_good = Voicing(soprano=68, alto=65, tenor=62, bass=47)  # Ab4(68), F4(65), D4(62), B2(47)
    viols_good = check_seventh_chord_doubling(v_good, chord_vii7, key=key)
    assert len(viols_good) == 0


def test_vii6_and_ii6_doubling():
    """VII6 cannot double leading tone; II6 doubles bass/third."""
    key = Key(tonic="C", mode="Major")
    chord_vii6 = Chord(function="VII6")

    # VII6 with doubled leading tone B: B4(71), F4(65), B3(59), D3(50)
    v_bad_vii6 = Voicing(soprano=71, alto=65, tenor=59, bass=50)
    viols_vii6 = check_sextaccord_doubling(v_bad_vii6, chord_vii6, key=key)
    assert any(v.rule_id == "DOUBLING_VII6_LEADING_TONE" for v in viols_vii6)

    # II6 in C major: D, F, A with bass F (third). Normal doubling is bass F (third):
    # S=D4(62), A=A3(57), T=F3(53), B=F2(41) -> doubled third F
    chord_ii6 = Chord(function="II6")
    v_good_ii6 = Voicing(soprano=62, alto=57, tenor=53, bass=41)
    viols_ii6 = check_sextaccord_doubling(v_good_ii6, chord_ii6, key=key)
    assert len(viols_ii6) == 0


def test_melodic_intervals_augmented_and_diminished():
    """Augmented 5th (8), diminished 7th (9), diminished 4th (4) forbidden; diminished 5th down (-6) allowed."""
    key_a = Key(tonic="A", mode="MinorHarmonic")

    # 1. Dim 5th down in bass (-6 semitones, e.g. F3=53 -> B2=47 in a-moll): allowed!
    v1 = Voicing(soprano=69, alto=64, tenor=60, bass=53)
    v2 = Voicing(soprano=69, alto=64, tenor=59, bass=47)
    viols_dim5 = check_melodic_intervals(v1, v2, key=key_a)
    assert not any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" and v.voices == (3,) for v in viols_dim5)

    # 2. Dim 7th leap (9 semitones, G#4=68 -> F5=77): forbidden!
    v3 = Voicing(soprano=68, alto=64, tenor=59, bass=40)
    v4 = Voicing(soprano=77, alto=64, tenor=57, bass=41)
    viols_dim7 = check_melodic_intervals(v3, v4, key=key_a)
    assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in viols_dim7)

    # 3. Aug 5th leap (8 semitones, C4=60 -> G#4=68): forbidden!
    v5 = Voicing(soprano=60, alto=57, tenor=52, bass=45)
    v6 = Voicing(soprano=68, alto=56, tenor=52, bass=40)
    viols_aug5 = check_melodic_intervals(v5, v6, key=key_a)
    assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in viols_aug5)

    # 4. Dim 4th leap upwards (4 semitones, G#4=68 -> C5=72): forbidden!
    v_dim4_1 = Voicing(soprano=68, alto=64, tenor=59, bass=40)
    v_dim4_2 = Voicing(soprano=72, alto=64, tenor=57, bass=41)
    viols_dim4 = check_melodic_intervals(v_dim4_1, v_dim4_2, key=key_a)
    assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in viols_dim4)

    # 5. Two leaps in same direction: forbidden when prev2_voicing provided
    v0 = Voicing(soprano=60, alto=57, tenor=52, bass=45)
    v_step1 = Voicing(soprano=65, alto=57, tenor=52, bass=45)  # Soprano leaped +5
    v_step2 = Voicing(soprano=72, alto=57, tenor=52, bass=45)  # Soprano leaped +7 in same direction
    viols_leaps = check_melodic_intervals(v_step1, v_step2, key=key_a, prev2_voicing=v0)
    assert any("LEAP" in v.rule_id for v in viols_leaps)


def test_default_melody_harmonization_nonnegative_cost():
    """(e) cost >= 0 on default melody harmonization [64, 65, 67, 64, 62, 60]."""
    melody = [64, 65, 67, 64, 62, 60]
    grammar = HarmonicGrammar(Key("C", "Major"))
    plans = grammar.generate_plans(melody)
    assert len(plans) > 0

    solver = ViterbiSolver()
    result = solver.solve(melody, plans[0], Key("C", "Major"))
    assert result.is_success
    assert result.total_cost >= 0.0
