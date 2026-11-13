"""Unit tests for ChordDefinition robustness (SECUNDA inversions, from_string synonyms, DD support)."""

import pytest
from src.harmony.core.chord import ChordDefinition, ChordFunction, Inversion
from src.harmony.core.key import Key, Mode
from src.harmony.core.pitch import PitchClass


@pytest.fixture
def c_major():
    return Key(PitchClass.C, Mode.MAJOR)


@pytest.fixture
def a_minor():
    return Key(PitchClass.A, Mode.MINOR_HARMONIC)


def test_vi_and_iii_secunda_bass_pitch_class_no_crash(c_major):
    # In C major:
    # VI = A, C, E, G (7th is G, PC 7)
    # III = E, G, B, D (7th is D, PC 2)
    vi2 = ChordDefinition(ChordFunction.VI, Inversion.SECUNDA, key=c_major)
    iii2 = ChordDefinition(ChordFunction.III, Inversion.SECUNDA, key=c_major)

    assert vi2.bass_pitch_class == PitchClass(7)
    assert iii2.bass_pitch_class == PitchClass(2)

    # validate_voicing should not crash
    is_val_vi, _ = vi2.validate_voicing([72, 69, 64, 55])
    assert isinstance(is_val_vi, bool)

    is_val_iii, _ = iii2.validate_voicing([71, 67, 64, 50])
    assert isinstance(is_val_iii, bool)


def test_chord_definition_from_string_synonyms_and_hyphens(c_major):
    # Hyphenated triads and sevenths
    hyphenated = ["T-6", "S-6", "D-6", "D-7", "D-65", "D-43", "D-2", "T-53", "S-53"]
    for s in hyphenated:
        cd = ChordDefinition.from_string(s, c_major)
        assert cd is not None, f"Failed to parse {s}"

    assert ChordDefinition.from_string("T-6", c_major).inversion == Inversion.SEXTA
    assert ChordDefinition.from_string("D-7", c_major).is_seventh
    assert ChordDefinition.from_string("D-43", c_major).inversion == Inversion.TERZQUART


def test_chord_definition_cad64_equals_k64(c_major):
    cad64 = ChordDefinition.from_string("CAD64", c_major)
    k64 = ChordDefinition(function=ChordFunction.K64, inversion=Inversion.QUARTSEXTA, key=c_major)
    assert cad64 == k64
    assert cad64.function == ChordFunction.K64
    assert cad64.inversion == Inversion.QUARTSEXTA


def test_chord_definition_secondary_dominant_dd(c_major):
    # DD triad
    dd = ChordDefinition.from_string("DD", c_major)
    assert dd.function == ChordFunction.DD
    assert not dd.is_seventh
    assert dd.inversion == Inversion.ROOT
    # DD in C major: root D(2), third F#(6), fifth A(9)
    assert dd.root == PitchClass(2)
    assert dd.third == PitchClass(6)
    assert dd.fifth == PitchClass(9)

    # DD7
    dd7 = ChordDefinition.from_string("DD7", c_major)
    assert dd7.function == ChordFunction.DD
    assert dd7.is_seventh
    assert dd7.seventh == PitchClass(0)  # tonic PC

    # DD inversions
    dd65 = ChordDefinition.from_string("DD65", c_major)
    assert dd65.function == ChordFunction.DD
    assert dd65.inversion == Inversion.QUINTSEXTA
    assert dd65.is_seventh

    dd43 = ChordDefinition.from_string("DD43", c_major)
    assert dd43.function == ChordFunction.DD
    assert dd43.inversion == Inversion.TERZQUART
    assert dd43.is_seventh

    dd2 = ChordDefinition.from_string("DD2", c_major)
    assert dd2.function == ChordFunction.DD
    assert dd2.inversion == Inversion.SECUNDA
    assert dd2.is_seventh
