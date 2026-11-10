"""
Tests for T2: D43 vs D2 differentiation and resolutions according to Brigade rules.
"""

import pytest
from src.harmony.core.types import Chord, Key, Voicing
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.resolutions import check_d43_resolution, check_d2_resolution
from src.harmony.rules.engine import RuleEngine
from src.harmony.syntax.grammar import HarmonicGrammar


def test_bass_pitch_classes_in_c_major():
    """
    In C-dur:
    D43 (V4/3)  -> bass = fifth of D7 = scale degree II = D (PC 2)
    D2 (V2/4)   -> bass = seventh of D7 = scale degree IV = F (PC 5)
    II43 (II4/3) -> bass = fifth of II7 (D-F-A-C) = A (PC 9)
    II2 (II2/4)  -> bass = seventh of II7 = C (PC 0)
    """
    k = Key("C", "Major")

    # D43: soprano=67 (G4, root of D)
    voicings_d43 = generate_candidate_voicings(67, Chord("D43"), key=k)
    assert len(voicings_d43) > 0
    bass_pcs_d43 = {v.bass % 12 for v in voicings_d43}
    assert bass_pcs_d43 == {2}, f"D43 bass pcs in C-dur must be {{2}}, got {bass_pcs_d43}"

    # D2: soprano=67 (G4, root of D)
    voicings_d2 = generate_candidate_voicings(67, Chord("D2"), key=k)
    assert len(voicings_d2) > 0
    bass_pcs_d2 = {v.bass % 12 for v in voicings_d2}
    assert bass_pcs_d2 == {5}, f"D2 bass pcs in C-dur must be {{5}}, got {bass_pcs_d2}"

    # II43: soprano=65 (F4, third of II)
    voicings_ii43 = generate_candidate_voicings(65, Chord("II43"), key=k)
    assert len(voicings_ii43) > 0
    bass_pcs_ii43 = {v.bass % 12 for v in voicings_ii43}
    assert bass_pcs_ii43 == {9}, f"II43 bass pcs in C-dur must be {{9}}, got {bass_pcs_ii43}"

    # II2: soprano=65 (F4, third of II)
    voicings_ii2 = generate_candidate_voicings(65, Chord("II2"), key=k)
    assert len(voicings_ii2) > 0
    bass_pcs_ii2 = {v.bass % 12 for v in voicings_ii2}
    assert bass_pcs_ii2 == {0}, f"II2 bass pcs in C-dur must be {{0}}, got {bass_pcs_ii2}"


def test_d43_resolution_to_t_and_t6():
    """
    D43 resolves canonically to T53 (bass II -> I) or T6 (bass II -> III).
    The 7th in upper voices steps down.
    """
    key = Key("C", "Major")
    chord_d43 = Chord("D43")
    chord_t = Chord("T")
    chord_t6 = Chord("T6")
    chord_ii = Chord("II")

    # In C-dur: D7 = G(7), B(11), D(2), F(5).
    # D43: Bass is D (50 = D3). Upper voices: S=F4(65, 7th), A=G4(67, root), T=B3(59, 3rd).
    v_d43 = Voicing(soprano=65, alto=67, tenor=59, bass=50)

    # Resolution to T:
    # Bass D3(50) -> C3(48) (-2).
    # S: F4(65, 7th) -> E4(64) (-1).
    # A: G4(67) -> G4(67) (0).
    # T: B3(59) -> C4(60) (+1).
    v_t = Voicing(soprano=64, alto=67, tenor=60, bass=48)
    assert len(check_d43_resolution(v_d43, v_t, chord_d43, chord_t, key=key)) == 0

    # Resolution to T6:
    # Bass D3(50) -> E3(52) (+2).
    # S: F4(65, 7th) -> E4(64) (-1).
    # A: G4(67) -> G4(67) (0).
    # T: B3(59) -> C4(60) (+1).
    v_t6 = Voicing(soprano=64, alto=67, tenor=60, bass=52)
    assert len(check_d43_resolution(v_d43, v_t6, chord_d43, chord_t6, key=key)) == 0

    # Forbidden target: D43 -> II
    v_ii = Voicing(soprano=65, alto=69, tenor=62, bass=50)
    viol_ii = check_d43_resolution(v_d43, v_ii, chord_d43, chord_ii, key=key)
    assert any(v.rule_id == "RESOLUTION_D43_TO_T6" for v in viol_ii)


def test_d2_resolution_strictly_to_t6():
    """
    D2 has 7th in bass (F). Must resolve strictly to T6 (bass F -> E).
    Resolution of D2 to T53 is a violation.
    """
    key = Key("C", "Major")
    chord_d2 = Chord("D2")
    chord_t6 = Chord("T6")
    chord_t = Chord("T")

    # D2: Bass is F3(53, 7th). Upper voices: S=G4(67), A=D4(62), T=B3(59).
    v_d2 = Voicing(soprano=67, alto=62, tenor=59, bass=53)

    # Proper D2 -> T6: Bass F3(53) -> E3(52) (-1).
    v_t6 = Voicing(soprano=67, alto=60, tenor=60, bass=52)
    # wait, S=67(G), A=64(E), T=60(C), B=52(E)
    v_t6_clean = Voicing(soprano=67, alto=64, tenor=60, bass=52)
    assert len(check_d2_resolution(v_d2, v_t6_clean, chord_d2, chord_t6, key=key)) == 0

    # Forbidden D2 -> T (5/3):
    v_t = Voicing(soprano=67, alto=64, tenor=60, bass=48)
    viol_t = check_d2_resolution(v_d2, v_t, chord_d2, chord_t, key=key)
    assert any(v.rule_id == "RESOLUTION_D2_TO_T6" for v in viol_t)


def test_grammar_syntax_transition_d43_d2():
    grammar = HarmonicGrammar()
    # D43 transitions
    assert grammar.is_valid_syntax_transition("D43", "T") is True
    assert grammar.is_valid_syntax_transition("D43", "T53") is True
    assert grammar.is_valid_syntax_transition("D43", "T6") is True
    assert grammar.is_valid_syntax_transition("D43", "II") is False

    # D2 transitions
    assert grammar.is_valid_syntax_transition("D2", "T6") is True
    assert grammar.is_valid_syntax_transition("D2", "T") is False
    assert grammar.is_valid_syntax_transition("D2", "T53") is False
