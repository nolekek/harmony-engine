"""
Unit tests for Leading-Tone Seventh Chord (VII7 -> T) Resolution with Doubled Third (Brigade Ch. 21).
"""

from src.harmony.rules.resolutions import check_vii7_resolution
from src.harmony.rules.doubling import check_doubling
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.rules.engine import RuleEngine


def test_vii7_to_t_valid_resolution_with_doubled_third():
    # C major VII7 (B D F Ab) voiced with the leading tone in the bass and the
    # 7th in the alto; the doubled third E lands in two octaves (E4/E3) so no
    # adjacent-voice unison appears.
    # VII7: S=D4 (62), A=Ab3 (56), T=F3 (53), B=B2 (47)
    # T:    S=E4 (64) (3rd up), A=G3 (55) (7th down), T=E3 (52) (5th down), B=C3 (48) (lt up)
    v_vii7 = Voicing(soprano=62, alto=56, tenor=53, bass=47)
    v_t = Voicing(soprano=64, alto=55, tenor=52, bass=48)
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
