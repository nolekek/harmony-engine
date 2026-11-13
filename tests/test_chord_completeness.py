"""
Tests for T1: Unison prohibition and triad completeness according to Brigade rules.
"""

from src.harmony.core.types import Chord, Key, Voicing
from src.harmony.rules.spacing import check_voice_unison, validate_spacing
from src.harmony.rules.doubling import check_triad_completeness
from src.harmony.rules.engine import RuleEngine


def test_unison_rejected():
    """(64, 60, 48, 48) for T in C-dur has Tenor == Bass unison -> VOICE_UNISON."""
    v_unison = Voicing(64, 60, 48, 48)
    violations = check_voice_unison(v_unison)
    assert any(
        viol.rule_id == "VOICE_UNISON" and viol.voices == (2, 3)
        for viol in violations
    )
    # Also via validate_spacing
    all_spacing = validate_spacing(v_unison)
    assert any(viol.rule_id == "VOICE_UNISON" for viol in all_spacing)


def test_third_required():
    """(60, 60, 55, 48) for T has C, C, G, C -> missing third (E) -> CHORD_THIRD_MISSING."""
    v_no_third = Voicing(60, 60, 55, 48)
    violations = check_triad_completeness(v_no_third, Chord("T"), key=Key("C", "Major"))
    assert any(viol.rule_id == "CHORD_THIRD_MISSING" for viol in violations)


def test_fifth_required_non_final():
    """(60, 64, 60, 48) non-final has C, E, C, C without fifth (G) -> CHORD_FIFTH_MISSING."""
    v_no_fifth = Voicing(60, 64, 60, 48)
    violations = check_triad_completeness(
        v_no_fifth, Chord("T"), key=Key("C", "Major"), is_final_chord=False
    )
    assert any(viol.rule_id == "CHORD_FIFTH_MISSING" for viol in violations)


def test_incomplete_triad_allowed_only_at_final():
    """Final chord with tripled root and third (without fifth) is permitted."""
    v_final = Voicing(72, 64, 60, 48)  # C5, E4, C4, C3
    violations = check_triad_completeness(
        v_final, Chord("T"), key=Key("C", "Major"), is_final_chord=True
    )
    assert len(violations) == 0

    # But if third is missing in final chord, it is still rejected
    v_final_no_third = Voicing(72, 67, 60, 48)  # C5, G4, C4, C3
    v_fail = check_triad_completeness(
        v_final_no_third, Chord("T"), key=Key("C", "Major"), is_final_chord=True
    )
    assert any(viol.rule_id == "CHORD_THIRD_MISSING" for viol in v_fail)


def test_engine_validate_voicing_includes_completeness_and_unison():
    engine = RuleEngine()
    key = Key("C", "Major")

    # Unison rejected by engine
    v_unison = Voicing(64, 60, 48, 48)
    res_u = engine.validate_voicing(v_unison, chord=Chord("T"), key=key)
    assert not res_u.is_valid
    assert any(v.rule_id == "VOICE_UNISON" for v in res_u.hard_violations)

    # Missing third rejected by engine
    v_no_third = Voicing(67, 60, 55, 48)  # G4, C4, G3, C3 (no E)
    res_t = engine.validate_voicing(v_no_third, chord=Chord("T"), key=key)
    assert not res_t.is_valid
    assert any(v.rule_id == "CHORD_THIRD_MISSING" for v in res_t.hard_violations)
