"""
Tests for T16: Functional dictionary extensions (III, III6, VII, VII6, VII7, II7, II65)
and descending diatonic harmonization.
"""

import pytest
from src.harmony.core.types import Key
from src.harmony.core.key import Key as CoreKey
from src.harmony.core.pitch import ScaleDegree
from src.harmony.core.chord import ChordFunction, normalize_roman, ChordDefinition
from src.harmony.rules.doubling import get_triad_tones
from src.harmony.syntax.grammar import HarmonicGrammar, ALL_FUNCTIONS
from src.harmony.pipeline import Harmonizer


class TestDictionaryTonesAndNormalization:
    """Verifies get_triad_tones and normalize_roman requirements for T16."""

    def test_get_triad_tones_iii_major(self):
        # III in C Major: E (4), G (7), B (11)
        assert get_triad_tones("III", 0, "Major") == (4, 7, 11)
        assert get_triad_tones("III6", 0, "Major") == (4, 7, 11)

    def test_get_triad_tones_iii_minor(self):
        # III in A Minor (tonic=9): C (0), E (4), G (7)
        assert get_triad_tones("III", 9, "Minor") == (0, 4, 7)

    def test_get_triad_tones_vii(self):
        # VII in C Major: B (11), D (2), F (5)
        assert get_triad_tones("VII", 0, "Major") == (11, 2, 5)
        assert get_triad_tones("VII6", 0, "Major") == (11, 2, 5)
        assert get_triad_tones("VII7", 0, "Major") == (11, 2, 5)

    def test_normalize_roman(self):
        assert normalize_roman("V") == "D"
        assert normalize_roman("I") == "T"
        assert normalize_roman("IV") == "S"
        assert normalize_roman("i") == "t"
        assert normalize_roman("iv") == "s"
        assert normalize_roman("v") == "d"
        assert normalize_roman("V7") == "D7"
        assert normalize_roman("v7") == "d7"
        assert normalize_roman("I6") == "T6"
        assert normalize_roman("IV6") == "S6"
        assert normalize_roman("VI") == "VI"
        assert normalize_roman("II") == "II"
        assert normalize_roman("II6") == "II6"
        assert normalize_roman("III") == "III"
        assert normalize_roman("VII") == "VII"
        assert normalize_roman("VII6") == "VII6"
        assert normalize_roman("K64") == "K64"

    def test_chord_function_enum(self):
        assert ChordFunction.III == "III"
        assert ChordFunction.from_str("III") == ChordFunction.III
        assert ChordFunction.from_str("3") == ChordFunction.III
        assert ChordFunction.III.root_scale_degree == ScaleDegree(3, 0)

    def test_chord_definition_iii(self):
        cdef = ChordDefinition.from_string("III", CoreKey.from_string("C Major"))
        assert cdef.function == ChordFunction.III
        assert cdef.root.value == 4   # E
        assert cdef.third.value == 7  # G
        assert cdef.fifth.value == 11 # B


class TestAllFunctionsAndSyntaxTransitions:
    """Verifies that all new functions are registered in ALL_FUNCTIONS and possess correct syntax."""

    def test_all_functions_presence(self):
        required = ["III", "III6", "VII", "VII6", "VII7", "II7", "II65"]
        for fn in required:
            assert fn in ALL_FUNCTIONS, f"{fn} must be in ALL_FUNCTIONS"

    def test_syntax_transitions_for_new_functions(self):
        g = HarmonicGrammar(Key(tonic="C", mode="Major"))

        # III departures to subdominant group and VI are valid
        assert g.is_valid_syntax_transition("III", "S")
        assert g.is_valid_syntax_transition("III", "S6")
        assert g.is_valid_syntax_transition("III", "VI")
        assert g.is_valid_syntax_transition("III", "II")
        assert g.is_valid_syntax_transition("III", "II6")
        assert g.is_valid_syntax_transition("III", "II65")

        # Prohibitions on III
        assert not g.is_valid_syntax_transition("III", "K64")
        assert not g.is_valid_syntax_transition("III", "DD")
        assert not g.is_valid_syntax_transition("III", "VII")

        # Dominant to III regression is prohibited
        assert not g.is_valid_syntax_transition("D", "III")
        assert not g.is_valid_syntax_transition("D7", "III")
        assert not g.is_valid_syntax_transition("VII", "III")

        # VII resolutions
        assert g.is_valid_syntax_transition("VII6", "T")
        assert g.is_valid_syntax_transition("VII6", "T6")
        assert g.is_valid_syntax_transition("VII7", "T")
        assert g.is_valid_syntax_transition("VII7", "D65")

        # VII regressions prohibited
        assert not g.is_valid_syntax_transition("VII", "S")
        assert not g.is_valid_syntax_transition("VII6", "S")
        assert not g.is_valid_syntax_transition("VII7", "S")
        assert not g.is_valid_syntax_transition("VII6", "II")
        assert not g.is_valid_syntax_transition("VII6", "K64")


class TestDescendingHarmonization:
    """Verifies end-to-end harmonization of descending soprano melodies."""

    def test_descending_diatonic_4_notes(self):
        # C5-B4-A4-G4 in C Major
        res = Harmonizer().harmonize([72, 71, 69, 67], key="C Major")
        assert res.is_success is True, f"Harmonization failed: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == 4

    def test_descending_scale_8_notes(self):
        # C5-B4-A4-G4-F4-E4-D4-C4 in C Major
        res = Harmonizer().harmonize([72, 71, 69, 67, 65, 64, 62, 60], key="C Major")
        assert res.is_success is True, f"Harmonization failed: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == 8
