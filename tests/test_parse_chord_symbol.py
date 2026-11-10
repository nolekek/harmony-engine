"""
Tests for T3: parse_chord_symbol handling of ChordDefinition and ChordFunction enums.
"""

import pytest
from src.harmony.core.types import Chord, Key, Voicing, parse_chord_symbol
from src.harmony.core.chord import ChordDefinition, ChordFunction, Inversion
from src.harmony.rules.doubling import check_main_triad_doubling


def test_parse_chord_symbol_enum_and_definition():
    k = Key("C", "Major")
    chord_def_t = ChordDefinition(ChordFunction.T, Inversion.ROOT, key=k)
    chord_def_d43 = ChordDefinition(ChordFunction.D, Inversion.TERZQUART, key=k)
    chord_def_k64 = ChordDefinition(ChordFunction.K64, Inversion.QUARTSEXTA, key=k)

    # 1. ChordDefinition returns value, not "ChordFunction.T"
    assert parse_chord_symbol(chord_def_t) == "T"
    assert parse_chord_symbol(chord_def_d43) == "D43"
    assert parse_chord_symbol(chord_def_k64) == "K64"

    # 2. ChordFunction enum returns value
    assert parse_chord_symbol(ChordFunction.T) == "T"
    assert parse_chord_symbol(ChordFunction.D) == "D"

    # 3. Existing types remain intact
    assert parse_chord_symbol(Chord("T")) == "T"
    assert parse_chord_symbol("T") == "T"
    assert parse_chord_symbol(None) == ""


def test_check_main_triad_doubling_consistency():
    """check_main_triad_doubling gives identical violations on ChordDefinition as on Chord."""
    k = Key("C", "Major")
    chord_def_t = ChordDefinition(ChordFunction.T, Inversion.ROOT, key=k)
    chord_t = Chord("T")

    # Voicing with forbidden doubled third (E4=64, E3=52, G3=55, C3=48):
    v_doubled_third = Voicing(soprano=64, alto=55, tenor=52, bass=48)

    viol_def = check_main_triad_doubling(v_doubled_third, chord_def_t, key=k)
    viol_chord = check_main_triad_doubling(v_doubled_third, chord_t, key=k)

    assert len(viol_def) > 0, "ChordDefinition must not bypass doubling checks!"
    assert len(viol_def) == len(viol_chord)
    assert [v.rule_id for v in viol_def] == [v.rule_id for v in viol_chord]
    assert any(v.rule_id == "DOUBLING_MAIN_TRIAD_ROOT" for v in viol_def)
