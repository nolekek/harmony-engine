"""Unit tests for harmony.core.chord."""

import pytest
from harmony.core.chord import ChordDefinition, ChordFunction, Inversion
from harmony.core.key import Key, Mode
from harmony.core.pitch import Pitch, PitchClass


class TestChord:
    @pytest.fixture
    def c_major(self) -> Key:
        return Key(PitchClass.C, Mode.MAJOR)

    @pytest.fixture
    def a_minor(self) -> Key:
        return Key(PitchClass.A, Mode.MINOR_HARMONIC)

    def test_chord_function_properties(self):
        assert ChordFunction.T.is_tonic_group
        assert ChordFunction.VI.is_tonic_group
        assert ChordFunction.S.is_subdominant_group
        assert ChordFunction.II.is_subdominant_group
        assert ChordFunction.D.is_dominant_group
        assert ChordFunction.K64.is_dominant_group

    def test_inversion_properties(self):
        assert Inversion.ROOT.symbol == "5/3"
        assert Inversion.SEXTA.symbol == "6"
        assert Inversion.QUARTSEXTA.symbol == "6/4"
        assert Inversion.SEPTIMA.symbol == "7"
        assert Inversion.QUINTSEXTA.symbol == "6/5"
        assert Inversion.TERZQUART.symbol == "4/3"
        assert Inversion.SECUNDA.symbol == "2"

        assert Inversion.ROOT.is_triad
        assert Inversion.SEPTIMA.is_seventh
        assert Inversion.SEXTA.bass_factor == "third"
        assert Inversion.QUARTSEXTA.bass_factor == "fifth"
        assert Inversion.SECUNDA.bass_factor == "seventh"

    def test_chord_tones_c_major(self, c_major):
        # Tonic T 5/3
        t = ChordDefinition(ChordFunction.T, Inversion.ROOT, c_major)
        assert t.root == PitchClass.C
        assert t.third == PitchClass.E
        assert t.fifth == PitchClass.G
        assert t.seventh is None
        assert t.bass_pitch_class == PitchClass.C
        assert t.pitch_classes == frozenset({PitchClass.C, PitchClass.E, PitchClass.G})

        # Subdominant S 6
        s6 = ChordDefinition(ChordFunction.S, Inversion.SEXTA, c_major)
        assert s6.root == PitchClass.F
        assert s6.third == PitchClass.A
        assert s6.fifth == PitchClass.C
        assert s6.bass_pitch_class == PitchClass.A  # 3rd in bass!

        # Dominant seventh D7
        d7 = ChordDefinition(ChordFunction.D, Inversion.SEPTIMA, c_major)
        assert d7.root == PitchClass.G
        assert d7.third == PitchClass.B
        assert d7.fifth == PitchClass.D
        assert d7.seventh == PitchClass.F
        assert d7.bass_pitch_class == PitchClass.G

        # Cadential K64
        k64 = ChordDefinition(ChordFunction.K64, Inversion.QUARTSEXTA, c_major)
        assert k64.root == PitchClass.C
        assert k64.third == PitchClass.E
        assert k64.fifth == PitchClass.G
        assert k64.bass_pitch_class == PitchClass.G  # Bass is fifth!

    def test_chord_tones_a_minor_harmonic(self, a_minor):
        # In minor harmonic, Dominant has raised third (G# leading tone!)
        d = ChordDefinition(ChordFunction.D, Inversion.ROOT, a_minor)
        assert d.root == PitchClass.E
        assert d.third == PitchClass.G_SHARP
        assert d.fifth == PitchClass.B

        # D7 in minor
        d7 = ChordDefinition(ChordFunction.D, Inversion.SEPTIMA, a_minor)
        assert d7.seventh == PitchClass.D

    def test_from_string(self, c_major):
        assert ChordDefinition.from_string("T", c_major).inversion == Inversion.ROOT
        assert ChordDefinition.from_string("T6", c_major).inversion == Inversion.SEXTA
        assert ChordDefinition.from_string("K64", c_major).function == ChordFunction.K64
        assert ChordDefinition.from_string("D7", c_major).is_seventh
        assert ChordDefinition.from_string("D43", c_major).inversion == Inversion.TERZQUART

    def test_doubling_rules_brigade(self, c_major, a_minor):
        # 1. Main triad T: doubling root is standard
        t = ChordDefinition(ChordFunction.T, Inversion.ROOT, c_major)
        # S=E4(64), A=C4(60), T=G3(55), B=C3(48) -> C:2, E:1, G:1 -> doubled root
        valid, msg = t.validate_voicing([Pitch(64), Pitch(60), Pitch(55), Pitch(48)])
        assert valid, msg

        # Doubling third in T 5/3 is strictly forbidden!
        # S=E4(64), A=E4(64), T=G3(55), B=C3(48) -> C:1, E:2, G:1
        invalid, msg = t.validate_voicing([Pitch(64), Pitch(64), Pitch(55), Pitch(48)])
        assert not invalid
        assert "forbidden" in msg.lower() or "third" in msg.lower()

        # 2. K64 strictly requires doubled bass (fifth)!
        k64 = ChordDefinition(ChordFunction.K64, Inversion.QUARTSEXTA, c_major)
        # S=E4(64), A=C4(60), T=G3(55), B=G2(43) -> G:2, C:1, E:1
        valid, msg = k64.validate_voicing([Pitch(64), Pitch(60), Pitch(55), Pitch(43)])
        assert valid, msg

        # K64 with doubled root -> invalid!
        # S=C5(72), A=C4(60), T=E3(52), B=G2(43) -> C:2, E:1, G:1
        invalid, msg = k64.validate_voicing([Pitch(72), Pitch(60), Pitch(52), Pitch(43)])
        assert not invalid
        assert "double the bass" in msg.lower()

        # 3. Deceptive cadence VI in A minor: double third (tonic note A)!
        vi = ChordDefinition(ChordFunction.VI, Inversion.ROOT, a_minor)
        # VI in A minor: root=F, third=A, fifth=C. Bass=F.
        # Voicing: S=A4(69), A=C4(60), T=A3(57), B=F2(41) -> A:2, C:1, F:1 -> doubled third!
        valid, msg = vi.validate_voicing([Pitch(69), Pitch(60), Pitch(57), Pitch(41)], is_deceptive_cadence=True)
        assert valid, msg

        # Voicing with doubled root F in deceptive cadence -> invalid!
        invalid, msg = vi.validate_voicing([Pitch(69), Pitch(65), Pitch(60), Pitch(41)], is_deceptive_cadence=True)
        assert not invalid
        assert "doubling the third" in msg.lower()
