"""
Tests for Macro Period Grammar and Functional Plan Generator.
"""

from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar


def test_grammar_pitch_compatibility():
    grammar = HarmonicGrammar(Key(tonic="C", mode="Major"))
    # C4 (60) belongs to T (C-E-G), S (F-A-C)
    chords_c = grammar.get_compatible_chords_for_pitch(60)
    assert "T" in chords_c
    assert "S" in chords_c
    # G4 (67) belongs to T, D
    chords_g = grammar.get_compatible_chords_for_pitch(67)
    assert "T" in chords_g
    assert "D" in chords_g


def test_grammar_syntax_transitions():
    grammar = HarmonicGrammar()
    # D -> S forbidden
    assert not grammar.is_valid_syntax_transition("D", "S")
    assert not grammar.is_valid_syntax_transition("D7", "II")
    # S -> D and S -> K64 allowed
    assert grammar.is_valid_syntax_transition("S", "D")
    assert grammar.is_valid_syntax_transition("II6", "K64")
    # D -> K64 strictly forbidden across all dominant chord types
    assert not grammar.is_valid_syntax_transition("D", "K64")
    assert not grammar.is_valid_syntax_transition("D6", "K64")
    assert not grammar.is_valid_syntax_transition("D7", "K64")
    # K64 must resolve to D / D7, cannot leap straight to T
    assert not grammar.is_valid_syntax_transition("K64", "T")
    assert grammar.is_valid_syntax_transition("K64", "D")
    assert grammar.is_valid_syntax_transition("K64", "D7")
    # D43 -> T6 allowed, D43 -> II forbidden
    assert grammar.is_valid_syntax_transition("D43", "T6")
    assert not grammar.is_valid_syntax_transition("D43", "II")
    # K64 cannot be penultimate chord immediately before final T
    assert "K64" not in grammar.get_compatible_chords_for_pitch(60, is_penultimate=True, is_downbeat=True)


def test_grammar_plan_generation():
    grammar = HarmonicGrammar(Key(tonic="C", mode="Major"))
    melody = [
        {"pitch": 64, "is_downbeat": True},   # E4
        {"pitch": 65, "is_downbeat": False},  # F4
        {"pitch": 67, "is_downbeat": True},   # G4
        {"pitch": 62, "is_downbeat": False},  # D4
        {"pitch": 60, "is_downbeat": True},   # C4
    ]

    plans = grammar.generate_plans(melody, max_plans=3)
    assert len(plans) > 0

    # Top plan must start with T and end with T
    top_plan = plans[0]
    assert len(top_plan) == 5
    assert top_plan[0].function in ("T", "T6")
    assert top_plan[-1].function in ("T", "t")

    # Verify no D -> S in any plan
    for plan in plans:
        for prev_c, curr_c in zip(plan[:-1], plan[1:]):
            assert grammar.is_valid_syntax_transition(prev_c.function, curr_c.function)
