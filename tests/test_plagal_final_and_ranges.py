"""
Tests for plagal last-resort final cadence and auto-extended voice ranges.
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.core.types import Voicing, Key, to_satb
from src.harmony.rules.spacing import check_voice_ranges


def test_plagal_final_for_non_tonic_soprano():
    """1. Harmonizer().harmonize([60,64,62,65], 'C Major').is_success is True;
    финальный аккорд функции в ("S","s") и его звуки образуют консонанс F-A-C ({0,5,9})."""
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([60, 64, 62, 65], "C Major")
    assert res.is_success is True
    assert res.best_solution is not None

    final_chord = res.best_solution.chords[-1]
    assert final_chord.function in ("S", "s")

    # In C major, F major triad pcs are {0, 5, 9} (F-A-C). Check final SATB pitch classes.
    final_voicing = res.best_solution.voicings[-1]
    satb = to_satb(final_voicing)
    pcs = {p % 12 for p in satb}
    assert pcs == {0, 5, 9}


def test_auto_extended_ranges_triggered():
    """2. harmonize([65,61,59,60], 'C Major').is_success is True;
    result.auto_extended_ranges is True; верхний голос финального аккорда содержит C."""
    harmonizer = Harmonizer()
    # 59 is B3, which is < 60 (below standard soprano range [60, 81])
    res = harmonizer.harmonize([65, 61, 59, 60], "C Major")
    assert res.is_success is True
    assert res.auto_extended_ranges is True
    assert res.best_solution is not None

    final_voicing = res.best_solution.voicings[-1]
    soprano_pitch = to_satb(final_voicing)[0]
    assert soprano_pitch % 12 == 0  # C


def test_auto_extended_ranges_not_triggered():
    """3. harmonize([60,62,64,65,67,69], 'C Major').auto_extended_ranges is False
    (стандартная мелодия — флаг не включается)."""
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([60, 62, 64, 65, 67, 69], "C Major")
    assert res.auto_extended_ranges is False


def test_dominant_final_preserved():
    """4. harmonize([60,62], 'C Major') → финальный аккорд в ("D","d")
    (доминанта не вытесняется субдоминантой)."""
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([60, 62], "C Major")
    assert res.is_success is True
    assert res.best_solution is not None
    final_chord = res.best_solution.chords[-1]
    assert final_chord.function in ("D", "d")


def test_grammar_cadential_contract():
    """5. grammar.get_compatible_chords_for_pitch(62, is_final_cadence=True) == ["D"]
    и (71, is_final_cadence=True) == ["D"] (контракт не сломан)."""
    grammar = HarmonicGrammar(key=Key.parse("C Major"))
    assert grammar.get_compatible_chords_for_pitch(62, is_final_cadence=True) == ["D"]
    assert grammar.get_compatible_chords_for_pitch(71, is_final_cadence=True) == ["D"]


def test_standard_voice_range_bounds_untouched():
    """6. check_voice_ranges(Voicing(59,58,52,48)) по-прежнему даёт VOICE_RANGE_BOUNDS
    (стандартный диапазон не тронут)."""
    s_low = Voicing(59, 58, 52, 48)
    violations = check_voice_ranges(s_low)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 0 in v.voices for v in violations)
