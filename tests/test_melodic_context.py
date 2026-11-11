"""
Tests for melodic context and voice-leading rule enhancements:
(a) leaps +8 and +9 -> hard gate
(b) diminished 5th down (-6) after upward leap with prev2 -> NOT hard
(c) two consecutive leaps in same direction -> MELODIC_TWO_LEAPS_SAME_DIRECTION
(d) contrary fifths 31 -> 19 -> CONTRARY_FIFTHS
(e) contrary motion 12 -> 0 -> CONTRARY_OCTAVES with diagnostic mentioning unison
"""
import pytest
from src.harmony.core.types import Voicing, Key
from src.harmony.rules.engine import RuleEngine
from src.harmony.rules.voice_leading import (
    check_melodic_intervals,
    check_contrary_fifths_and_octaves,
    validate_voice_leading,
)


def test_melodic_leaps_plus8_and_plus9_hard():
    """(a) Leap of +8 (aug 5th) and +9 (dim 7th) must produce hard violations."""
    key_a = Key(tonic="A", mode="MinorHarmonic")

    # +8 semitones leap in Soprano: C4 (60) -> G#4 (68) in A minor
    v1 = Voicing(soprano=60, alto=57, tenor=52, bass=45)
    v2 = Voicing(soprano=68, alto=57, tenor=52, bass=45)
    res_8 = check_melodic_intervals(v1, v2, key=key_a)
    viols_8 = [v for v in res_8 if v.is_hard and v.voices == (0,)]
    assert len(viols_8) > 0, "Leap of +8 semitones must trigger a hard violation"
    assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in viols_8)

    # +9 semitones leap in Soprano: G#4 (68) -> F5 (77) in A minor
    v3 = Voicing(soprano=68, alto=57, tenor=52, bass=45)
    v4 = Voicing(soprano=77, alto=57, tenor=52, bass=45)
    res_9 = check_melodic_intervals(v3, v4, key=key_a)
    viols_9 = [v for v in res_9 if v.is_hard and v.voices == (0,)]
    assert len(viols_9) > 0, "Leap of +9 semitones must trigger a hard violation"
    assert any(v.rule_id == "MELODIC_DIMINISHED_SEVENTH" for v in viols_9)


def test_diminished_fifth_down_after_upward_leap_with_prev2():
    """(b) Diminished 5th down (-6) after an upward leap (>= 4) with prev2 is NOT hard."""
    key_c = Key(tonic="C", mode="Major")

    # Soprano: C4 (60) -> F4 (65, leap up +5 >= 4) -> B3 (59, leap down -6)
    v_prev2 = Voicing(soprano=60, alto=55, tenor=52, bass=48)
    v_prev = Voicing(soprano=65, alto=57, tenor=52, bass=45)
    v_curr = Voicing(soprano=59, alto=60, tenor=55, bass=48)

    res = check_melodic_intervals(v_prev, v_curr, key=key_c, prev2_voicing=v_prev2)
    s_viols = [v for v in res if v.voices == (0,) and v.is_hard]
    assert len(s_viols) == 0, f"Dim 5th down resolving inward after leap up >= 4 must NOT be hard: {s_viols}"


def test_two_leaps_same_direction():
    """(c) Two consecutive leaps in the same direction (each > 4 semitones) -> MELODIC_TWO_LEAPS_SAME_DIRECTION."""
    # Soprano: C4 (60) -> F4 (65, +5) -> B4 (71, +6)
    # Both leaps > 4 semitones upwards
    engine = RuleEngine()
    v_a = Voicing(soprano=60, alto=55, tenor=52, bass=48)
    v_b = Voicing(soprano=65, alto=57, tenor=52, bass=45)
    v_c = Voicing(soprano=71, alto=60, tenor=55, bass=43)

    res = engine.validate(
        prev_voicing=v_b,
        curr_voicing=v_c,
        prev_chord="S",
        curr_chord="D",
        key="C Major",
        prev2_voicing=v_a,
    )
    two_leaps = [v for v in res.violations if v.rule_id == "MELODIC_TWO_LEAPS_SAME_DIRECTION"]
    assert len(two_leaps) > 0, "Two consecutive leaps in same direction must trigger MELODIC_TWO_LEAPS_SAME_DIRECTION"
    assert two_leaps[0].is_hard


def test_contrary_fifths_compound_31_to_19():
    """(d) Contrary fifths across compound interval: 31 -> 19 -> CONTRARY_FIFTHS."""
    # Bass=36 (C2), Soprano=67 (G4): distance 31 semitones (2 octaves + 5th).
    # Contrary motion: Bass moves 36 -> 43 (+7), Soprano moves 67 -> 62 (-5).
    # Current distance: 62 - 43 = 19 semitones (contrary 12th).
    v_prev = Voicing(soprano=67, alto=60, tenor=55, bass=36)
    v_curr = Voicing(soprano=62, alto=59, tenor=55, bass=43)

    viols = check_contrary_fifths_and_octaves(v_prev, v_curr)
    contrary_fifths = [v for v in viols if v.rule_id == "CONTRARY_FIFTHS"]
    assert len(contrary_fifths) > 0, "Contrary fifths (31 -> 19) must trigger CONTRARY_FIFTHS"


def test_contrary_octaves_12_to_0_unison_diagnostic():
    """(e) Contrary motion 12 -> 0 -> CONTRARY_OCTAVES with diagnostic mentioning unison."""
    # S=72 (C5), A=60 (C4): distance 12 semitones.
    # Contrary motion: S moves 72 -> 66 (-6), A moves 60 -> 66 (+6).
    # Current distance: 66 - 66 = 0 semitones (unison).
    v_prev = Voicing(soprano=72, alto=60, tenor=55, bass=48)
    v_curr = Voicing(soprano=66, alto=66, tenor=55, bass=48)

    viols = check_contrary_fifths_and_octaves(v_prev, v_curr)
    contrary_octaves = [v for v in viols if v.rule_id == "CONTRARY_OCTAVES"]
    assert len(contrary_octaves) > 0, "Contrary motion 12 -> 0 must trigger CONTRARY_OCTAVES"
    assert "unison" in contrary_octaves[0].description.lower(), "Diagnostic must mention unison"
