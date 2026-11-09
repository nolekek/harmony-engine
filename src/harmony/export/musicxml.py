"""
MusicXML exporter for classical four-part harmony (SATB).
Produces valid MusicXML 3.1 / 4.0 partwise score files readable by MuseScore, Sibelius, Dorico, and Finale.
"""

from typing import Any, Sequence
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.harmony.core.types import Voicing, Key, Chord, to_satb, parse_key

STEP_NAMES = ("C", "C", "D", "D", "E", "F", "F", "G", "G", "A", "A", "B")
ALTERS = (0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0)


def midi_to_pitch_element(midi_pitch: int) -> ET.Element:
    pitch_elem = ET.Element("pitch")
    pc = midi_pitch % 12
    octave = (midi_pitch // 12) - 1

    step = STEP_NAMES[pc]
    alter = ALTERS[pc]

    step_elem = ET.SubElement(pitch_elem, "step")
    step_elem.text = step

    if alter != 0:
        alter_elem = ET.SubElement(pitch_elem, "alter")
        alter_elem.text = str(alter)

    octave_elem = ET.SubElement(pitch_elem, "octave")
    octave_elem.text = str(octave)

    return pitch_elem


def export_to_musicxml(
    voicings: Sequence[Voicing | tuple[int, int, int, int]],
    chords: Sequence[Chord | str] | None = None,
    key: Any = None,
    title: str = "Harmonization Exercise",
    composer: str = "Brigade Harmony Engine",
) -> str:
    """
    Exports a sequence of SATB voicings to a standard MusicXML 3.1 Partwise document.
    """
    root = ET.Element("score-partwise", version="3.1")

    # Header: Work / Identification
    work = ET.SubElement(root, "work")
    work_title = ET.SubElement(work, "work-title")
    work_title.text = title

    identification = ET.SubElement(root, "identification")
    creator = ET.SubElement(identification, "creator", type="composer")
    creator.text = composer

    # Part-list
    part_list = ET.SubElement(root, "part-list")
    score_part = ET.SubElement(part_list, "score-part", id="P1")
    part_name = ET.SubElement(score_part, "part-name")
    part_name.text = "SATB Choir"

    # Part
    part = ET.SubElement(root, "part", id="P1")

    # Group chords into measures (e.g., 2 chords per measure for half notes in 4/4)
    chords_per_measure = 2
    total_voicings = len(voicings)

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")

    measure_idx = 1
    for m_start in range(0, total_voicings, chords_per_measure):
        m_slice = voicings[m_start : m_start + chords_per_measure]
        m_chords = chords[m_start : m_start + chords_per_measure] if chords else []

        measure = ET.SubElement(part, "measure", number=str(measure_idx))

        # Attributes on measure 1
        if measure_idx == 1:
            attrs = ET.SubElement(measure, "attributes")
            divs = ET.SubElement(attrs, "divisions")
            divs.text = "2"  # 2 divisions per quarter note

            # Key
            key_elem = ET.SubElement(attrs, "key")
            fifths_elem = ET.SubElement(key_elem, "fifths")
            fifths_elem.text = "0"  # Default 0 fifths

            # Time 4/4
            time_elem = ET.SubElement(attrs, "time")
            beats = ET.SubElement(time_elem, "beats")
            beats.text = "4"
            beat_type = ET.SubElement(time_elem, "beat-type")
            beat_type.text = "4"

            # 2 staves (treble and bass)
            staves = ET.SubElement(attrs, "staves")
            staves.text = "2"

            # Clef 1: Treble
            clef1 = ET.SubElement(attrs, "clef", number="1")
            sign1 = ET.SubElement(clef1, "sign")
            sign1.text = "G"
            line1 = ET.SubElement(clef1, "line")
            line1.text = "2"

            # Clef 2: Bass
            clef2 = ET.SubElement(attrs, "clef", number="2")
            sign2 = ET.SubElement(clef2, "sign")
            sign2.text = "F"
            line2 = ET.SubElement(clef2, "line")
            line2.text = "4"

        # Write notes: Staff 1 (Soprano & Alto), Staff 2 (Tenor & Bass)
        duration_val = "4"  # Half note = 4 divisions
        type_val = "half"

        # Staff 1: Voice 1 (Soprano)
        for i, v in enumerate(m_slice):
            satb = to_satb(v)
            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[0]))
            dur = ET.SubElement(note, "duration")
            dur.text = duration_val
            voice = ET.SubElement(note, "voice")
            voice.text = "1"
            ntype = ET.SubElement(note, "type")
            ntype.text = type_val
            staff = ET.SubElement(note, "staff")
            staff.text = "1"

            # Add harmonic Roman numeral as lyric under the first beat if available
            chord_idx = m_start + i
            if chords and chord_idx < len(chords):
                c_sym = chords[chord_idx].function if hasattr(chords[chord_idx], "function") else str(chords[chord_idx])
                lyric = ET.SubElement(note, "lyric", number="1")
                ltext = ET.SubElement(lyric, "text")
                ltext.text = c_sym

        # Staff 1: Voice 2 (Alto)
        # Backup to start of measure for Voice 2
        backup = ET.SubElement(measure, "backup")
        b_dur = ET.SubElement(backup, "duration")
        b_dur.text = str(int(duration_val) * len(m_slice))

        for v in m_slice:
            satb = to_satb(v)
            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[1]))
            dur = ET.SubElement(note, "duration")
            dur.text = duration_val
            voice = ET.SubElement(note, "voice")
            voice.text = "2"
            ntype = ET.SubElement(note, "type")
            ntype.text = type_val
            staff = ET.SubElement(note, "staff")
            staff.text = "1"

        # Staff 2: Voice 3 (Tenor)
        backup2 = ET.SubElement(measure, "backup")
        b_dur2 = ET.SubElement(backup2, "duration")
        b_dur2.text = str(int(duration_val) * len(m_slice))

        for v in m_slice:
            satb = to_satb(v)
            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[2]))
            dur = ET.SubElement(note, "duration")
            dur.text = duration_val
            voice = ET.SubElement(note, "voice")
            voice.text = "3"
            ntype = ET.SubElement(note, "type")
            ntype.text = type_val
            staff = ET.SubElement(note, "staff")
            staff.text = "2"

        # Staff 2: Voice 4 (Bass)
        backup3 = ET.SubElement(measure, "backup")
        b_dur3 = ET.SubElement(backup3, "duration")
        b_dur3.text = str(int(duration_val) * len(m_slice))

        for v in m_slice:
            satb = to_satb(v)
            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[3]))
            dur = ET.SubElement(note, "duration")
            dur.text = duration_val
            voice = ET.SubElement(note, "voice")
            voice.text = "4"
            ntype = ET.SubElement(note, "type")
            ntype.text = type_val
            staff = ET.SubElement(note, "staff")
            staff.text = "2"

        measure_idx += 1

    # Pretty print XML string
    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
