"""
Unit tests for non-chord tones validator (задержания, проходящие, вспомогательные, предъёмы).
"""

from src.harmony.rules.non_chord_tones import (
    NonChordToneType,
    classify_melodic_tone,
    check_voice_embellishments,
)
from src.harmony.core.types import Voicing


def test_classify_passing_tone_ascending():
    # E4 (64) -> F4 (65) -> G4 (67). F4 is passing tone between E and G.
    tone_type, violations = classify_melodic_tone(
        prev_pitch=64,
        curr_pitch=65,
        next_pitch=67,
        is_curr_chord_tone=False,
        is_downbeat=False,
    )
    assert tone_type == NonChordToneType.PASSING
    assert len(violations) == 0


def test_classify_passing_tone_descending():
    # G4 (67) -> F4 (65) -> E4 (64).
    tone_type, violations = classify_melodic_tone(
        prev_pitch=67,
        curr_pitch=65,
        next_pitch=64,
        is_curr_chord_tone=False,
        is_downbeat=False,
    )
    assert tone_type == NonChordToneType.PASSING
    assert len(violations) == 0


def test_classify_neighbor_tone():
    # G4 (67) -> A4 (69) -> G4 (67). A4 is upper neighbor.
    tone_type, violations = classify_melodic_tone(
        prev_pitch=67,
        curr_pitch=69,
        next_pitch=67,
        is_curr_chord_tone=False,
        is_downbeat=False,
    )
    assert tone_type == NonChordToneType.NEIGHBOR
    assert len(violations) == 0


def test_classify_suspension_valid_resolution():
    # Held tone on downbeat C4 (60 -> 60), resolves down by step to B3 (59)
    tone_type, violations = classify_melodic_tone(
        prev_pitch=60,
        curr_pitch=60,
        next_pitch=59,
        is_curr_chord_tone=False,
        is_downbeat=True,
    )
    assert tone_type == NonChordToneType.SUSPENSION
    assert len(violations) == 0


def test_classify_suspension_unresolved_leap():
    # Held tone on downbeat C4 (60 -> 60), but leaps down to G3 (55) - illegal!
    tone_type, violations = classify_melodic_tone(
        prev_pitch=60,
        curr_pitch=60,
        next_pitch=55,
        is_curr_chord_tone=False,
        is_downbeat=True,
    )
    assert tone_type == NonChordToneType.SUSPENSION
    assert len(violations) == 1
    assert violations[0].is_hard
    assert violations[0].rule_id == "NCT_SUSPENSION_UNRESOLVED"


def test_classify_anticipation():
    # Steps into C4 on weak beat, then next chord holds C4
    tone_type, violations = classify_melodic_tone(
        prev_pitch=62,  # D4
        curr_pitch=60,  # C4
        next_pitch=60,  # C4
        is_curr_chord_tone=False,
        is_downbeat=False,
    )
    assert tone_type == NonChordToneType.ANTICIPATION
    assert len(violations) == 0


def test_illegal_non_chord_tone_leap():
    # Leaps into non-chord tone and leaps out: C4 (60) -> F#4 (66) -> D4 (62)
    tone_type, violations = classify_melodic_tone(
        prev_pitch=60,
        curr_pitch=66,
        next_pitch=62,
        is_curr_chord_tone=False,
        is_downbeat=False,
    )
    assert len(violations) == 1
    assert violations[0].is_hard
    assert violations[0].rule_id == "NCT_ILLEGAL_LEAP_NON_CHORD_TONE"


def test_check_voice_embellishments_satb():
    # Voicing 1: T (C major: E4, C4, G3, C3)
    v1 = Voicing(soprano=64, alto=60, tenor=55, bass=48)
    # Voicing 2: Passing tone in soprano (F4: 65, while others stay or move)
    # Current chord is still T (C major tones: C, E, G = 0, 4, 7)
    v2 = Voicing(soprano=65, alto=60, tenor=55, bass=48)
    # Voicing 3: Reaches G4 (67)
    v3 = Voicing(soprano=67, alto=60, tenor=55, bass=48)

    c_major_tones = {0, 4, 7}
    violations = check_voice_embellishments(
        prev_voicing=v1,
        curr_voicing=v2,
        next_voicing=v3,
        curr_chord_tones=c_major_tones,
        is_downbeat=False,
    )
    # F4 (65) is a valid passing tone between 64 and 67
    assert len(violations) == 0
