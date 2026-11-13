"""Unit tests for II7 chord resolution gaps according to Brigade Harmony textbook."""

import pytest
from src.harmony.core.types import Voicing
from src.harmony.rules.resolutions import (
    check_ii7_resolution,
    validate_resolutions,
)


@pytest.fixture
def c_major():
    return "C Major"


@pytest.fixture
def a_minor():
    return "A Minor"


def test_ii7_to_non_dominant_target_raises_violation(c_major):
    # II7 in C-dur: D3(50), F3(53), A3(57), C4(60).
    v_ii7 = Voicing(soprano=60, alto=57, tenor=53, bass=50)
    # Target S: F4(65), C4(60), A3(57), F2(41) - subdominant!
    v_s = Voicing(soprano=65, alto=60, tenor=57, bass=41)

    viols = check_ii7_resolution(v_ii7, v_s, "II7", "S", key=c_major)
    assert any(v.rule_id == "RESOLUTION_II7_TO_DOMINANT" and v.is_hard for v in viols)


def test_ii7_to_dominant_group_targets_allowed(c_major):
    # II7 resolving to D: 7th C4(60) -> B3(59) (-1)
    # II7: S=C4(60), A=A3(57), T=F3(53), B=D3(50)
    # D: S=B3(59), A=G3(55), T=D4(62), B=G2(43)
    v_ii7 = Voicing(soprano=60, alto=57, tenor=53, bass=50)
    v_d = Voicing(soprano=59, alto=62, tenor=55, bass=43)

    for target in ("D", "D6", "D7", "D65", "D43", "D2", "K64"):
        # For K64, common tone C4->C4 is held
        if target == "K64":
            v_target = Voicing(soprano=60, alto=64, tenor=55, bass=43)
        else:
            v_target = v_d
        viols = check_ii7_resolution(v_ii7, v_target, "II7", target, key=c_major)
        target_viols = [v for v in viols if v.rule_id == "RESOLUTION_II7_TO_DOMINANT"]
        assert len(target_viols) == 0, f"Expected {target} to be an allowed target for II7"


def test_ii7_seventh_step_down_resolution(c_major):
    # In C major, II7 7th is C (PC 0).
    # Correct resolution to D: C4(60) -> B3(59) (-1 semitone)
    v_ii7 = Voicing(soprano=60, alto=57, tenor=53, bass=50)
    v_d_good = Voicing(soprano=59, alto=62, tenor=55, bass=43)

    viols = check_ii7_resolution(v_ii7, v_d_good, "II7", "D", key=c_major)
    seventh_viols = [v for v in viols if v.rule_id == "RESOLUTION_II7_SEVENTH_DOWN"]
    assert len(seventh_viols) == 0


def test_ii7_seventh_illegal_leap_or_upward_movement(c_major):
    # In C major: 7th is C4(60) in soprano.
    # Bad 1: leaps up by +9 semitones to A4(69)
    v_ii7 = Voicing(soprano=60, alto=57, tenor=53, bass=50)
    v_d_bad1 = Voicing(soprano=69, alto=59, tenor=55, bass=43)

    viols1 = check_ii7_resolution(v_ii7, v_d_bad1, "II7", "D", key=c_major)
    assert any(v.rule_id == "RESOLUTION_II7_SEVENTH_DOWN" and v.is_hard for v in viols1)

    # Bad 2: steps up by +2 semitones to D4(62)
    v_d_bad2 = Voicing(soprano=62, alto=59, tenor=55, bass=43)
    viols2 = check_ii7_resolution(v_ii7, v_d_bad2, "II7", "D", key=c_major)
    assert any(v.rule_id == "RESOLUTION_II7_SEVENTH_DOWN" and v.is_hard for v in viols2)


def test_ii7_to_k64_seventh_held_as_common_tone(c_major):
    # In II7 -> K64, the seventh (tonic PC, C) is held as common tone in the same voice (delta == 0).
    # II7: S=C4(60), A=A3(57), T=F3(53), B=D3(50)
    # K64: S=C4(60), A=G3(55), T=E3(52), B=G2(43) (delta S = 0)
    v_ii7 = Voicing(soprano=60, alto=57, tenor=53, bass=50)
    v_k64 = Voicing(soprano=60, alto=55, tenor=52, bass=43)

    viols = check_ii7_resolution(v_ii7, v_k64, "II7", "K64", key=c_major)
    seventh_viols = [v for v in viols if v.rule_id == "RESOLUTION_II7_SEVENTH_DOWN"]
    assert len(seventh_viols) == 0


def test_ii7_inversions_coverage(c_major):
    # Test II65, II43, II2
    # In II65: bass is F3(53)
    v_ii65 = Voicing(soprano=60, alto=57, tenor=50, bass=53)
    v_t_bad = Voicing(soprano=64, alto=60, tenor=55, bass=48)  # Resolving to T is forbidden!

    for inv_sym in ("II65", "II43", "II2"):
        viols = check_ii7_resolution(v_ii65, v_t_bad, inv_sym, "T", key=c_major)
        assert any(v.rule_id == "RESOLUTION_II7_TO_DOMINANT" for v in viols)


def test_validate_resolutions_automatically_dispatches_ii7(c_major):
    # Verify that validate_resolutions() includes check_ii7_resolution
    v_ii7 = Voicing(soprano=60, alto=57, tenor=53, bass=50)
    v_d_bad = Voicing(soprano=69, alto=59, tenor=55, bass=43)  # Seventh leaps up

    viols = validate_resolutions(v_ii7, v_d_bad, "II7", "D", key=c_major)
    assert any(v.rule_id == "RESOLUTION_II7_SEVENTH_DOWN" for v in viols)
