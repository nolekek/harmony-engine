"""
Tests for MusicXML accidental spelling (REPORT #29, #30; T25).
Ensures flat keys (fifths < 0) write notes with flats (Bb, Eb, Ab, Db)
and sharp keys (fifths > 0) write notes with sharps (F#, C#, G#).
"""

import xml.etree.ElementTree as ET
import pytest

from src.harmony.core.types import Voicing
from src.harmony.export.musicxml import export_to_musicxml, midi_to_pitch_element


def test_musicxml_spelling_f_major_bb():
    """In F-dur (fifths=-1), note Bb (MIDI 70) must be written as step=B, alter=-1, not A#."""
    # F-dur tonic triad and subdominant with Bb (MIDI 70 in soprano)
    voicings = [
        Voicing(soprano=69, alto=65, tenor=60, bass=53),  # A4, F4, C4, F3 (T)
        Voicing(soprano=70, alto=65, tenor=62, bass=50),  # Bb4, F4, D4, D3 (S6 / IV)
    ]
    chords = ["T", "S6"]
    xml_str = export_to_musicxml(voicings, chords, key="F Major")

    root = ET.fromstring(xml_str)

    # Check key signature in attributes
    fifths_elem = root.find(".//key/fifths")
    assert fifths_elem is not None
    assert int(fifths_elem.text) == -1

    # Find the note with pitch 70 (Bb4)
    # Pitch 70 must be step B, alter -1, octave 4
    b_notes = []
    for note in root.findall(".//note"):
        pitch_elem = note.find("pitch")
        if pitch_elem is not None:
            step = pitch_elem.find("step")
            alter = pitch_elem.find("alter")
            pitch_elem.find("octave")
            if step is not None and step.text == "B" and alter is not None and alter.text == "-1":
                b_notes.append(note)

    assert len(b_notes) >= 1, "Expected to find note Bb with step=B, alter=-1"

    # Ensure no note in the entire XML has step=A with alter=1 (A#)
    for note in root.findall(".//note"):
        pitch_elem = note.find("pitch")
        if pitch_elem is not None:
            step = pitch_elem.find("step")
            alter = pitch_elem.find("alter")
            if step is not None and step.text == "A" and alter is not None and alter.text == "1":
                pytest.fail("Found A# in F-dur score, expected Bb!")


def test_musicxml_spelling_d_major_f_sharp():
    """In D-dur (fifths=2), note F# (MIDI 66) must be written as step=F, alter=1, not Gb."""
    # D-dur tonic triad with F# in soprano (MIDI 66)
    voicings = [
        Voicing(soprano=66, alto=62, tenor=57, bass=50),  # F#4, D4, A3, D3 (T)
        Voicing(soprano=67, alto=62, tenor=59, bass=55),  # G4, D4, B3, G3 (S)
    ]
    chords = ["T", "S"]
    xml_str = export_to_musicxml(voicings, chords, key="D Major")

    root = ET.fromstring(xml_str)

    # Check key signature in attributes
    fifths_elem = root.find(".//key/fifths")
    assert fifths_elem is not None
    assert int(fifths_elem.text) == 2

    # Find F# note
    f_sharp_notes = []
    for note in root.findall(".//note"):
        pitch_elem = note.find("pitch")
        if pitch_elem is not None:
            step = pitch_elem.find("step")
            alter = pitch_elem.find("alter")
            if step is not None and step.text == "F" and alter is not None and alter.text == "1":
                f_sharp_notes.append(note)

    assert len(f_sharp_notes) >= 1, "Expected to find note F# with step=F, alter=1 in D-dur"

    # Ensure no Gb (step G, alter -1)
    for note in root.findall(".//note"):
        pitch_elem = note.find("pitch")
        if pitch_elem is not None:
            step = pitch_elem.find("step")
            alter = pitch_elem.find("alter")
            if step is not None and step.text == "G" and alter is not None and alter.text == "-1":
                pytest.fail("Found Gb in D-dur score, expected F#!")


def test_musicxml_spelling_eb_major_flats():
    """In Eb-dur (fifths=-3), Eb (63), Ab (68), and Bb (70) must all be spelled with alter=-1."""
    voicings = [
        Voicing(soprano=63, alto=55, tenor=51, bass=39),  # Eb4, G3, Eb3, Eb2
        Voicing(soprano=68, alto=60, tenor=56, bass=44),  # Ab4, C4, Ab3, Ab2
        Voicing(soprano=70, alto=62, tenor=58, bass=46),  # Bb4, D4, Bb3, Bb2
    ]
    xml_str = export_to_musicxml(voicings, key="Eb Major")
    root = ET.fromstring(xml_str)

    for note in root.findall(".//note"):
        pitch_elem = note.find("pitch")
        if pitch_elem is not None:
            alter = pitch_elem.find("alter")
            if alter is not None and alter.text:
                # In Eb major, alterations must be flats (-1), not sharps (+1)
                assert alter.text == "-1", f"Found non-flat alteration {alter.text} in Eb major"


def test_midi_to_pitch_element_direct():
    """Unit test for midi_to_pitch_element with positive, negative, and zero fifths."""
    # Pitch 70 (Bb / A#)
    elem_flat = midi_to_pitch_element(70, fifths=-1)
    assert elem_flat.find("step").text == "B"
    assert elem_flat.find("alter").text == "-1"
    assert elem_flat.find("octave").text == "4"

    elem_sharp = midi_to_pitch_element(70, fifths=2)
    assert elem_sharp.find("step").text == "A"
    assert elem_sharp.find("alter").text == "1"
    assert elem_sharp.find("octave").text == "4"

    # Pitch 66 (F# / Gb)
    elem_f_sharp = midi_to_pitch_element(66, fifths=1)
    assert elem_f_sharp.find("step").text == "F"
    assert elem_f_sharp.find("alter").text == "1"
    assert elem_f_sharp.find("octave").text == "4"

    elem_gb = midi_to_pitch_element(66, fifths=-2)
    assert elem_gb.find("step").text == "G"
    assert elem_gb.find("alter").text == "-1"
    assert elem_gb.find("octave").text == "4"
