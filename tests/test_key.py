"""Unit tests for harmony.core.key."""

import pytest
from harmony.core.key import Key, Mode
from harmony.core.pitch import Pitch, PitchClass, ScaleDegree


class TestKeyAndMode:
    def test_mode_intervals(self):
        assert Mode.MAJOR.intervals == (0, 2, 4, 5, 7, 9, 11)
        assert Mode.MINOR_HARMONIC.intervals == (0, 2, 3, 5, 7, 8, 11)
        assert Mode.MAJOR.is_major
        assert Mode.MINOR_HARMONIC.is_minor

    def test_mode_parsing(self):
        assert Mode.from_str("Major") == Mode.MAJOR
        assert Mode.from_str("dur") == Mode.MAJOR
        assert Mode.from_str("мажор") == Mode.MAJOR
        assert Mode.from_str("MinorHarmonic") == Mode.MINOR_HARMONIC
        assert Mode.from_str("moll") == Mode.MINOR_HARMONIC
        assert Mode.from_str("MinorNatural") == Mode.MINOR_NATURAL
        assert Mode.from_str("MinorMelodic") == Mode.MINOR_MELODIC

    def test_key_scale_pitches_c_major(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        expected = [
            PitchClass.C, PitchClass.D, PitchClass.E, PitchClass.F,
            PitchClass.G, PitchClass.A, PitchClass.B
        ]
        assert c_dur.scale_pitch_classes == expected
        assert c_dur.contains(Pitch(60))
        assert c_dur.contains(Pitch(64))  # E
        assert not c_dur.contains(Pitch(61))  # C#

    def test_key_scale_pitches_a_minor_harmonic(self):
        a_moll = Key(PitchClass.A, Mode.MINOR_HARMONIC)
        # A, B, C, D, E, F, G#
        expected = [
            PitchClass.A, PitchClass.B, PitchClass.C, PitchClass.D,
            PitchClass.E, PitchClass.F, PitchClass.G_SHARP
        ]
        assert a_moll.scale_pitch_classes == expected
        assert a_moll.contains(PitchClass.G_SHARP)
        assert not a_moll.contains(PitchClass.G)

    def test_degree_mapping(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        assert c_dur.pitch_class_for_degree(1) == PitchClass.C
        assert c_dur.pitch_class_for_degree(ScaleDegree(4, 0)) == PitchClass.F
        assert c_dur.pitch_class_for_degree(ScaleDegree(5, 0)) == PitchClass.G
        assert c_dur.pitch_class_for_degree(ScaleDegree(7, 0)) == PitchClass.B

        # Altered degree: bII in C-dur -> Db
        assert c_dur.pitch_class_for_degree(ScaleDegree(2, -1)) == PitchClass.DB
        # Altered degree: #IV in C-dur -> F#
        assert c_dur.pitch_class_for_degree(ScaleDegree(4, 1)) == PitchClass.F_SHARP

    def test_degree_for_pitch_class(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        assert c_dur.degree_for_pitch_class(PitchClass.C) == ScaleDegree(1, 0)
        assert c_dur.degree_for_pitch_class(PitchClass.G) == ScaleDegree(5, 0)
        assert c_dur.degree_for_pitch_class(PitchClass.DB) == ScaleDegree(2, -1)

    def test_modal_tendencies(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        # Leading tone
        assert c_dur.leading_tone == PitchClass.B
        assert c_dur.is_leading_tone(PitchClass.B)
        assert not c_dur.is_leading_tone(PitchClass.C)

        # Unstable degrees
        unstable = c_dur.unstable_degrees
        assert ScaleDegree(2, 0) in unstable
        assert ScaleDegree(4, 0) in unstable
        assert ScaleDegree(6, 0) in unstable
        assert ScaleDegree(7, 0) in unstable

        # Stability checks
        assert c_dur.is_stable(PitchClass.C)
        assert c_dur.is_stable(PitchClass.E)
        assert c_dur.is_stable(PitchClass.G)
        assert c_dur.is_unstable(PitchClass.D)
        assert c_dur.is_unstable(PitchClass.F)
        assert c_dur.is_unstable(PitchClass.A)
        assert c_dur.is_unstable(PitchClass.B)

        # Melodic resolutions
        assert c_dur.get_tendency_resolutions(ScaleDegree(7, 0)) == [ScaleDegree(1, 0)]
        assert c_dur.get_tendency_resolutions(ScaleDegree(4, 0)) == [ScaleDegree(3, 0)]
        assert c_dur.get_pitch_tendency_resolutions(PitchClass.B) == [PitchClass.C]
        assert c_dur.get_pitch_tendency_resolutions(PitchClass.F) == [PitchClass.E]

    def test_from_string(self):
        k1 = Key.from_string("C Major")
        assert k1.tonic == PitchClass.C and k1.mode == Mode.MAJOR

        k2 = Key.from_string("C-dur")
        assert k2.tonic == PitchClass.C and k2.mode == Mode.MAJOR

        k3 = Key.from_string("a-moll")
        assert k3.tonic == PitchClass.A and k3.mode == Mode.MINOR_HARMONIC

        k4 = Key.from_string("G:MinorHarmonic")
        assert k4.tonic == PitchClass.G and k4.mode == Mode.MINOR_HARMONIC
