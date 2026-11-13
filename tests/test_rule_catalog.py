"""
Tests for RuleEngine catalog integration and syntax progression rules (T17).
"""
from src.harmony.core.types import Key, Chord
from src.harmony.rules.engine import RuleEngine
from src.harmony.syntax.grammar import HarmonicGrammar


def test_rule_catalog_loaded():
    engine = RuleEngine()
    assert len(engine.rules_registry) > 0
    desc_unison = engine.get_rule_description("VOICE_UNISON")
    assert desc_unison is not None
    assert isinstance(desc_unison, str)
    assert len(desc_unison) > 0

    desc_p5 = engine.get_rule_description("PARALLEL_FIFTHS")
    assert desc_p5 is not None

    desc_missing = engine.get_rule_description("DEFINITELY_NON_EXISTENT_RULE_12345")
    assert desc_missing is None


def test_d_to_s_syntax_rule():
    engine = RuleEngine()
    chord_d = Chord(function="D")
    chord_s = Chord(function="S")

    # Inside phrase (phrase_boundary=False) -> hard violation
    viols_no_boundary = engine.check_syntax(
        chord_d, chord_s, is_downbeat=True, phrase_boundary=False
    )
    assert any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in viols_no_boundary)

    # At phrase boundary (phrase_boundary=True) -> allowed!
    viols_boundary = engine.check_syntax(
        chord_d, chord_s, is_downbeat=True, phrase_boundary=True
    )
    assert not any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in viols_boundary)


def test_grammar_syntax_transition_consistency():
    grammar = HarmonicGrammar(Key("C", "Major"))

    # D -> S inside phrase is forbidden
    assert not grammar.is_valid_syntax_transition("D", "S", is_downbeat=True, phrase_boundary=False)

    # D -> S at phrase boundary is allowed
    assert grammar.is_valid_syntax_transition("D", "S", is_downbeat=True, phrase_boundary=True)

    # K64 on weak beat is forbidden in grammar and engine
    assert not grammar.is_valid_syntax_transition("S", "K64", is_downbeat=False)
