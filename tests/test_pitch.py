"""Unit tests for harmony.core.pitch."""

import pytest
from harmony.core.pitch import Interval, Pitch, PitchClass, ScaleDegree


class TestPitchClass:
    def test_values_and_names(self):
        assert PitchClass.C == 0
        assert PitchClass.C_SHARP == 1
        assert PitchClass.DB == 1
        assert PitchClass.D == 2
        assert PitchClass.G == 7
        assert PitchClass.A == 9
        assert PitchClass.B == 11

    def test_string_representations(self):
        assert PitchClass.C.sharp_name == "C"
        assert PitchClass.C_SHARP.sharp_name == "C#"
        assert PitchClass.C_SHARP.flat_name == "Db"
        assert PitchClass.C.russian_name == "До"
        assert PitchClass.G.russian_name == "Соль"

    def test_from_name(self):
        assert PitchClass.from_name("C") == PitchClass.C
        assert PitchClass.from_name("C#") == PitchClass.C_SHARP
        assert PitchClass.from_name("Db") == PitchClass.DB
        assert PitchClass.from_name("D♯") == PitchClass.D_SHARP
        assert PitchClass.from_name("B♭") == PitchClass.BB
        assert PitchClass.from_name("H") == PitchClass.B
        assert PitchClass.from_name("B#") == PitchClass.C
        assert PitchClass.from_name("Cb") == PitchClass.B

    def test_invalid_name(self):
        with pytest.raises(ValueError):
            PitchClass.from_name("XYZ")
        with pytest.raises(ValueError):
            PitchClass.from_name("")

    def test_from_midi(self):
        assert PitchClass.from_midi(60) == PitchClass.C
        assert PitchClass.from_midi(61) == PitchClass.C_SHARP
        assert PitchClass.from_midi(48) == PitchClass.C
        assert PitchClass.from_midi(43) == PitchClass.G

    def test_arithmetic(self):
        assert PitchClass.C + 7 == PitchClass.G
        assert PitchClass.C - 1 == PitchClass.B
        assert PitchClass.G.interval_to(PitchClass.C) == 5
        assert PitchClass.C.interval_to(PitchClass.G) == 7
        assert PitchClass.C + Interval.from_name("ч5") == PitchClass.G


class TestInterval:
    def test_standard_intervals(self):
        p5 = Interval.from_name("ч5")
        assert p5.semitones == 7
        assert p5.is_perfect_fifth
        assert not p5.is_step
        assert p5.is_leap

        octave = Interval.from_name("ч8")
        assert octave.semitones == 12
        assert octave.is_perfect_octave

        m2 = Interval.from_name("м2")
        assert m2.semitones == 1
        assert m2.is_step

        b2 = Interval.from_name("б2")
        assert b2.semitones == 2
        assert b2.is_step

        tritone = Interval.from_name("тритон")
        assert tritone.semitones == 6
        assert tritone.is_tritone

        aug2 = Interval.from_name("ув2")
        assert aug2.semitones == 3
        assert aug2.is_augmented_second

    def test_from_pitches(self):
        c4 = Pitch.from_midi(60)
        g4 = Pitch.from_midi(67)
        c5 = Pitch.from_midi(72)

        inv1 = Interval.from_pitches(c4, g4)
        assert inv1.semitones == 7
        assert inv1.is_perfect_fifth

        inv2 = Interval.from_pitches(c4, c5)
        assert inv2.semitones == 12
        assert inv2.is_perfect_octave


class TestScaleDegree:
    def test_roman_numerals(self):
        assert ScaleDegree(1, 0).roman == "I"
        assert ScaleDegree(4, 0).roman == "IV"
        assert ScaleDegree(5, 0).roman == "V"
        assert ScaleDegree(7, 0).roman == "VII"

    def test_alterations(self):
        deg7_sharp = ScaleDegree(7, 1)
        assert deg7_sharp.name == "VII#"
        assert deg7_sharp.is_leading_tone

        deg2_flat = ScaleDegree(2, -1)
        assert deg2_flat.name == "bII"

    def test_from_str(self):
        assert ScaleDegree.from_str("I") == ScaleDegree(1, 0)
        assert ScaleDegree.from_str("IV") == ScaleDegree(4, 0)
        assert ScaleDegree.from_str("VII#") == ScaleDegree(7, 1)
        assert ScaleDegree.from_str("#VII") == ScaleDegree(7, 1)
        assert ScaleDegree.from_str("bII") == ScaleDegree(2, -1)
        assert ScaleDegree.from_str("bVI") == ScaleDegree(6, -1)

    def test_invalid_degree(self):
        with pytest.raises(ValueError):
            ScaleDegree(0, 0)
        with pytest.raises(ValueError):
            ScaleDegree(8, 0)
        with pytest.raises(ValueError):
            ScaleDegree.from_str("VIII")


class TestPitch:
    def test_midi_and_octave(self):
        c4 = Pitch.from_midi(60)
        assert c4.midi_number == 60
        assert c4.octave == 4
        assert c4.pitch_class == PitchClass.C
        assert c4.note_name == "C4"

        e2 = Pitch.from_midi(40)
        assert e2.octave == 2
        assert e2.pitch_class == PitchClass.E
        assert e2.note_name == "E2"

        a5 = Pitch.from_midi(81)
        assert a5.octave == 5
        assert a5.pitch_class == PitchClass.A
        assert a5.note_name == "A5"

    def test_from_name(self):
        assert Pitch.from_name("C4") == Pitch(60)
        assert Pitch.from_name("G#3") == Pitch(56)
        assert Pitch.from_name("Bb2") == Pitch(46)
        assert Pitch.from_name("E2") == Pitch(40)

    def test_bounds(self):
        with pytest.raises(ValueError):
            Pitch(-1)
        with pytest.raises(ValueError):
            Pitch(128)

    def test_comparisons_and_arithmetic(self):
        p1 = Pitch(60)
        p2 = Pitch(64)
        assert p1 < p2
        assert p2 > p1
        assert p2 - p1 == Interval(4)
        assert p1 + 4 == p2
        assert p1 + Interval.from_name("б3") == p2
        assert p2 - Interval.from_name("б3") == p1
