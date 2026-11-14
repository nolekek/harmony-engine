"""
Behavior tests for the two new hard gates (G1/G2):

- BASS_INVERSION_MISMATCH: the bass pitch class must match the tone required
  by the declared function + figured-bass inversion (single source of truth:
  rules/doubling.py:required_bass_pc_for, shared with the solver generator).
- FOREIGN_TONE: a voice pitch outside the declared chord is a hard violation
  unless classify_nct recognizes it as a legal passing/neighbor/suspension
  tone in the melodic context of its own voice (voice-agnostic).
"""

from src.harmony.core.types import Chord, Key, Voicing
from src.harmony.rules.engine import RuleEngine

KEY = Key(tonic="C", mode="Major")


def _ids(violations) -> set:
    return {v.rule_id for v in violations}


# ---------------------------------------------------------------- G1: bass

def test_ii6_with_root_bass_is_bass_inversion_mismatch():
    """II6 declares the first inversion: bass D (pc 2) instead of F is a hard gate."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(69, 65, 62, 50), Chord(function="II6"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" in _ids(res.violations)


def test_ii6_with_third_bass_is_clean():
    """II6 with the required bass F (pc 5) does not trigger the gate."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(69, 65, 62, 53), Chord(function="II6"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" not in _ids(res.violations)


def test_d43_with_fifth_bass_is_clean():
    """D43 is the second inversion of the dominant seventh: required bass is
    the chord fifth (D, pc 2 in C major — II degree, per RESOLUTION_D43_TO_T6)."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(74, 71, 60, 50), Chord(function="D43"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" not in _ids(res.violations)


def test_d43_with_foreign_bass_is_bass_inversion_mismatch():
    """D43 with bass A (pc 9, not even a chord tone of G7) is a hard gate."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(74, 71, 60, 45), Chord(function="D43"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" in _ids(res.violations)


def test_t6_with_third_bass_is_clean():
    """T6 requires the third (E) in the bass — no violation."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(67, 60, 60, 52), Chord(function="T6"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" not in _ids(res.violations)


def test_root_t_with_root_bass_is_clean():
    """Root-position T with bass C is consistent with its figured bass."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(60, 55, 55, 48), Chord(function="T"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" not in _ids(res.violations)


def test_root_t_with_third_bass_is_bass_inversion_mismatch():
    """Root-position T declared without inversion but voiced with bass E (a T6
    sonority) contradicts the figured bass — hard gate."""
    engine = RuleEngine()
    res = engine.validate_voicing(Voicing(67, 60, 55, 52), Chord(function="T"), key=KEY)
    assert "BASS_INVERSION_MISMATCH" in _ids(res.violations)


# -------------------------------------------------------- G2: foreign tone

def test_foreign_tone_b4_in_ii_chord_flagged():
    """External-reviewer case: II = D-F-A, voicing (71,69,62,50) sounds B4
    (pc 11); melodic context 69 -> 71 -> 74 is not a legal NCT -> FOREIGN_TONE."""
    engine = RuleEngine()
    res = engine.validate(
        prev_voicing=Voicing(69, 65, 62, 53),
        curr_voicing=Voicing(71, 69, 62, 50),
        prev_chord=Chord(function="II6"),
        curr_chord=Chord(function="II"),
        key=KEY,
        next_voicing=Voicing(74, 71, 60, 50),
    )
    ft = [v for v in res.violations if v.rule_id == "FOREIGN_TONE"]
    assert ft, "B4 over II must be flagged as FOREIGN_TONE"
    assert ft[0].voices == (0,)
    assert ft[0].is_hard


def test_foreign_tone_in_inner_voice_flagged():
    """The gate is voice-agnostic: a foreign alto tone (Bb over T, leaped to
    and away) is flagged exactly like a soprano one."""
    engine = RuleEngine()
    res = engine.validate(
        prev_voicing=Voicing(64, 55, 52, 48),
        curr_voicing=Voicing(64, 58, 52, 48),
        prev_chord=Chord(function="T"),
        curr_chord=Chord(function="T"),
        key=KEY,
        next_voicing=Voicing(64, 55, 52, 48),
    )
    ft = [v for v in res.violations if v.rule_id == "FOREIGN_TONE"]
    assert ft, "Bb3 over T must be flagged as FOREIGN_TONE"
    assert ft[0].voices == (1,)


def test_legal_passing_tone_not_flagged():
    """Soprano D4 between C4 and E4 over T is a passing tone per classify_nct
    -> not a FOREIGN_TONE."""
    engine = RuleEngine()
    res = engine.validate(
        prev_voicing=Voicing(60, 55, 52, 48),
        curr_voicing=Voicing(62, 55, 52, 48),
        prev_chord=Chord(function="T"),
        curr_chord=Chord(function="T"),
        key=KEY,
        next_voicing=Voicing(64, 55, 52, 48),
    )
    assert "FOREIGN_TONE" not in _ids(res.violations)


def test_legal_neighbor_tone_not_flagged():
    """Soprano D4 stepping E4 -> D4 -> E4 over T is a neighbor tone per
    classify_nct -> not a FOREIGN_TONE."""
    engine = RuleEngine()
    res = engine.validate(
        prev_voicing=Voicing(64, 55, 52, 48),
        curr_voicing=Voicing(62, 55, 52, 48),
        prev_chord=Chord(function="T"),
        curr_chord=Chord(function="T"),
        key=KEY,
        next_voicing=Voicing(64, 55, 52, 48),
    )
    assert "FOREIGN_TONE" not in _ids(res.violations)


def test_foreign_tone_skipped_without_full_melodic_context():
    """classify_nct needs prev AND next pitches; without them the classifier
    cannot decide and the gate stays silent (protects solver DP transitions
    and isolated-slice validation from false positives)."""
    engine = RuleEngine()
    curr = Voicing(71, 69, 62, 50)

    res_no_prev = engine.validate(None, curr, curr_chord=Chord(function="II"), key=KEY)
    assert "FOREIGN_TONE" not in _ids(res_no_prev.violations)

    res_no_next = engine.validate(
        prev_voicing=Voicing(69, 65, 62, 53),
        curr_voicing=curr,
        prev_chord=Chord(function="II6"),
        curr_chord=Chord(function="II"),
        key=KEY,
    )
    assert "FOREIGN_TONE" not in _ids(res_no_next.violations)
