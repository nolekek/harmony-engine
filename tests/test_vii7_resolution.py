"""
Unit tests for Leading-Tone Seventh Chord (VII7 -> T) Resolution with Doubled Third (Brigade Ch. 21).
"""

import pytest
from src.harmony.rules.resolutions import check_vii7_resolution
from src.harmony.rules.doubling import check_doubling
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.rules.engine import RuleEngine


def test_vii7_to_t_valid_resolution_with_doubled_third():
    # C major:
    # VII7 (diminished 7th in C): B3 (59), D4 (62), F4 (65), Ab4 (68)
    # Voice leading to T:
    # Soprano: Ab4 (68) -> G4 (67) (7th resolves down by half-step)
    # Alto:    F4 (65)  -> E4 (64) (5th resolves down into 3rd of T)
    # Tenor:   D4 (62)  -> E4 (64) (3rd resolves up into 3rd of T -> doubled third!)
    # Bass:    B2 (47)  -> C3 (48) (leading tone resolves up to tonic)
    v_vii7 = Voicing(soprano=68, alto=65, tenor=62, bass=47)
    v_t = Voicing(soprano=67, alto=64, tenor=64, bass=48)
    k = Key(tonic="C", mode="Major")
    c_vii7 = Chord(function="VII7")
    c_t = Chord(function="T")

    # 1. Resolutions check
    res_violations = check_vii7_resolution(v_vii7, v_t, c_vii7, c_t, key=k)
    assert len(res_violations) == 0

    # 2. Doubling check: T has doubled third E4 (64), which is permitted & required after VII7!
    doubling_violations = check_doubling(v_t, c_t, key=k, prev_chord=c_vii7)
    assert len(doubling_violations) == 0

    # 3. Master RuleEngine validation
    engine = RuleEngine()
    result = engine.validate(
        prev_voicing=v_vii7,
        curr_voicing=v_t,
        prev_chord=c_vii7,
        curr_chord=c_t,
        key=k,
    )
    assert result.is_valid
    assert not result.has_hard_violations


def test_vii7_seventh_unresolved_leap_blocked():
    # Seventh Ab4 (68) leaps up to C5 (72) instead of resolving down to G4
    v_vii7 = Voicing(soprano=68, alto=65, tenor=62, bass=47)
    v_t = Voicing(soprano=72, alto=64, tenor=64, bass=48)
    k = Key(tonic="C", mode="Major")
    c_vii7 = Chord(function="VII7")
    c_t = Chord(function="T")

    res_violations = check_vii7_resolution(v_vii7, v_t, c_vii7, c_t, key=k)
    assert len(res_violations) > 0
    assert any(v.rule_id == "RESOLUTION_VII7_SEVENTH_DOWN" and v.is_hard for v in res_violations)
