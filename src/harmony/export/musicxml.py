"""
MusicXML exporter for classical four-part harmony (SATB).
Produces valid MusicXML 3.1 / 4.0 partwise score files readable by MuseScore, Sibelius, Dorico, and Finale.
Supports variable durations, dotted notes, and time signature changes across measures.
"""

from typing import Any, Sequence
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.harmony.core.types import (
    Voicing,
    Key,
    Chord,
    TimeSignature,
    to_satb,
    parse_key,
    quarters_to_xml_type_and_dots,
    calculate_metric_structure,
)

STEP_NAMES = ("C", "C", "D", "D", "E", "F", "F", "G", "G", "A", "A", "B")
ALTERS = (0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0)

FIFTHS_TABLE = {
    # Major
    ("C", "MAJOR"): 0, ("G", "MAJOR"): 1, ("D", "MAJOR"): 2, ("A", "MAJOR"): 3,
    ("E", "MAJOR"): 4, ("B", "MAJOR"): 5, ("F#", "MAJOR"): 6, ("C#", "MAJOR"): 7,
    ("F", "MAJOR"): -1, ("BB", "MAJOR"): -2, ("EB", "MAJOR"): -3, ("AB", "MAJOR"): -4,
    ("DB", "MAJOR"): -5, ("GB", "MAJOR"): -6,
    # Minor
    ("A", "MINOR"): 0, ("E", "MINOR"): 1, ("B", "MINOR"): 2, ("F#", "MINOR"): 3,
    ("C#", "MINOR"): 4, ("G#", "MINOR"): 5, ("D#", "MINOR"): 6, ("A#", "MINOR"): 7,
    ("D", "MINOR"): -1, ("G", "MINOR"): -2, ("C", "MINOR"): -3, ("F", "MINOR"): -4,
    ("BB", "MINOR"): -5, ("EB", "MINOR"): -6,
}


def get_fifths(tonic: str, mode: str) -> int:
    t_clean = tonic.strip().upper().replace("H", "B")
    m_clean = "MINOR" if "MINOR" in mode.upper() else "MAJOR"
    return FIFTHS_TABLE.get((t_clean, m_clean), 0)


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
    voicings: Sequence[Voicing | tuple[int, int, int, int] | dict[str, int]],
    chords: Sequence[Chord | str] | None = None,
    key: Any = None,
    title: str = "Harmonization Exercise",
    composer: str = "Brigade Harmony Engine",
    durations: Sequence[Any] | None = None,
    time_signature: Any = "4/4",
) -> str:
    """
    Exports a sequence of SATB voicings to a standard MusicXML 3.1 Partwise document.
    Properly formats:
    - Custom time signatures (e.g. 3/4, 2/4, 6/8, 4/4) and meter changes
    - Dotted notes (<type> + <dot/> elements)
    - Dynamic measure grouping based on accumulated duration
    - 4 independent polyphonic SATB voices across two staves
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

    if not voicings:
        rough_string = ET.tostring(root, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    # Key signature
    tonic_str = "C"
    mode_str = "Major"
    if key is not None:
        if isinstance(key, Key):
            tonic_str = key.tonic
            mode_str = key.mode
        elif isinstance(key, str):
            parts = key.split()
            tonic_str = parts[0] if parts else "C"
            mode_str = parts[1] if len(parts) > 1 else "Major"

    fifths_val = get_fifths(tonic_str, mode_str)

    # Build metric structure
    melody_items = []
    for i, v in enumerate(voicings):
        dur = durations[i] if durations and i < len(durations) else "half"
        melody_items.append({"pitch": to_satb(v)[0], "duration": dur})

    metric_info = calculate_metric_structure(melody_items, default_time_signature=time_signature)

    # Group note indices by measure
    measures_dict: dict[int, list[int]] = {}
    for idx, info in enumerate(metric_info):
        m_num = info["measure"]
        measures_dict.setdefault(m_num, []).append(idx)

    measure_numbers = sorted(measures_dict.keys())
    divisions_per_quarter = 4

    for m_num in measure_numbers:
        m_indices = measures_dict[m_num]
        first_info = metric_info[m_indices[0]]
        m_time_sig = first_info["time_signature"]
        time_changed = first_info["time_sig_changed"]

        measure = ET.SubElement(part, "measure", number=str(m_num))

        # Attributes on measure 1 or upon meter change
        if m_num == 1 or time_changed:
            attrs = ET.SubElement(measure, "attributes")
            if m_num == 1:
                divs = ET.SubElement(attrs, "divisions")
                divs.text = str(divisions_per_quarter)

                key_elem = ET.SubElement(attrs, "key")
                fifths_elem = ET.SubElement(key_elem, "fifths")
                fifths_elem.text = str(fifths_val)
                mode_elem = ET.SubElement(key_elem, "mode")
                mode_elem.text = "minor" if "MINOR" in mode_str.upper() else "major"

            time_elem = ET.SubElement(attrs, "time")
            beats = ET.SubElement(time_elem, "beats")
            beats.text = str(m_time_sig.beats)
            beat_type = ET.SubElement(time_elem, "beat-type")
            beat_type.text = str(m_time_sig.beat_type)

            if m_num == 1:
                staves = ET.SubElement(attrs, "staves")
                staves.text = "2"

                clef1 = ET.SubElement(attrs, "clef", number="1")
                sign1 = ET.SubElement(clef1, "sign")
                sign1.text = "G"
                line1 = ET.SubElement(clef1, "line")
                line1.text = "2"

                clef2 = ET.SubElement(attrs, "clef", number="2")
                sign2 = ET.SubElement(clef2, "sign")
                sign2.text = "F"
                line2 = ET.SubElement(clef2, "line")
                line2.text = "4"

        m_total_divisions = sum(
            int(round(metric_info[idx]["duration_quarters"] * divisions_per_quarter))
            for idx in m_indices
        )

        # Voice 1 (Soprano) - Staff 1
        for idx in m_indices:
            v = voicings[idx]
            info = metric_info[idx]
            dur_divs = int(round(info["duration_quarters"] * divisions_per_quarter))
            xml_type, dots = quarters_to_xml_type_and_dots(info["duration_quarters"])
            satb = to_satb(v)

            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[0]))
            dur = ET.SubElement(note, "duration")
            dur.text = str(dur_divs)
            voice = ET.SubElement(note, "voice")
            voice.text = "1"
            ntype = ET.SubElement(note, "type")
            ntype.text = xml_type
            if dots > 0:
                for _ in range(dots):
                    ET.SubElement(note, "dot")
            staff = ET.SubElement(note, "staff")
            staff.text = "1"

            if chords and idx < len(chords):
                c = chords[idx]
                c_sym = c.function if hasattr(c, "function") else str(c)
                lyric = ET.SubElement(note, "lyric", number="1")
                ltext = ET.SubElement(lyric, "text")
                ltext.text = c_sym

        # Voice 2 (Alto) - Staff 1
        backup = ET.SubElement(measure, "backup")
        b_dur = ET.SubElement(backup, "duration")
        b_dur.text = str(m_total_divisions)

        for idx in m_indices:
            v = voicings[idx]
            info = metric_info[idx]
            dur_divs = int(round(info["duration_quarters"] * divisions_per_quarter))
            xml_type, dots = quarters_to_xml_type_and_dots(info["duration_quarters"])
            satb = to_satb(v)

            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[1]))
            dur = ET.SubElement(note, "duration")
            dur.text = str(dur_divs)
            voice = ET.SubElement(note, "voice")
            voice.text = "2"
            ntype = ET.SubElement(note, "type")
            ntype.text = xml_type
            if dots > 0:
                for _ in range(dots):
                    ET.SubElement(note, "dot")
            staff = ET.SubElement(note, "staff")
            staff.text = "1"

        # Voice 3 (Tenor) - Staff 2
        backup2 = ET.SubElement(measure, "backup")
        b_dur2 = ET.SubElement(backup2, "duration")
        b_dur2.text = str(m_total_divisions)

        for idx in m_indices:
            v = voicings[idx]
            info = metric_info[idx]
            dur_divs = int(round(info["duration_quarters"] * divisions_per_quarter))
            xml_type, dots = quarters_to_xml_type_and_dots(info["duration_quarters"])
            satb = to_satb(v)

            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[2]))
            dur = ET.SubElement(note, "duration")
            dur.text = str(dur_divs)
            voice = ET.SubElement(note, "voice")
            voice.text = "3"
            ntype = ET.SubElement(note, "type")
            ntype.text = xml_type
            if dots > 0:
                for _ in range(dots):
                    ET.SubElement(note, "dot")
            staff = ET.SubElement(note, "staff")
            staff.text = "2"

        # Voice 4 (Bass) - Staff 2
        backup3 = ET.SubElement(measure, "backup")
        b_dur3 = ET.SubElement(backup3, "duration")
        b_dur3.text = str(m_total_divisions)

        for idx in m_indices:
            v = voicings[idx]
            info = metric_info[idx]
            dur_divs = int(round(info["duration_quarters"] * divisions_per_quarter))
            xml_type, dots = quarters_to_xml_type_and_dots(info["duration_quarters"])
            satb = to_satb(v)

            note = ET.SubElement(measure, "note")
            note.append(midi_to_pitch_element(satb[3]))
            dur = ET.SubElement(note, "duration")
            dur.text = str(dur_divs)
            voice = ET.SubElement(note, "voice")
            voice.text = "4"
            ntype = ET.SubElement(note, "type")
            ntype.text = xml_type
            if dots > 0:
                for _ in range(dots):
                    ET.SubElement(note, "dot")
            staff = ET.SubElement(note, "staff")
            staff.text = "2"

    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
