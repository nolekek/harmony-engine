"""
MusicXML exporter for classical four-part harmony (SATB).
Produces valid MusicXML 3.1 / 4.0 partwise score files readable by MuseScore, Sibelius, Dorico, and Finale.
Supports variable durations, dotted notes, and time signature changes across measures.
"""

from typing import Any, Sequence
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from xml.dom import minidom
from src.harmony.core.types import (
    Voicing,
    Key,
    Chord,
    TimeSignature,
    to_satb,
    parse_key,
    parse_duration_quarters,
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


@dataclass
class NoteSlice:
    satb: tuple[int, int, int, int]
    dur_divs: int
    xml_type: str
    dots: int
    chord_sym: str | None
    tie_start: bool
    tie_stop: bool
    is_rest: bool = False


@dataclass
class MeasureSliceData:
    measure_num: int
    time_signature: TimeSignature
    time_sig_changed: bool
    slices: list[NoteSlice]
    total_divisions: int


def make_note_element(
    pitch_num: int,
    dur_divs: int,
    xml_type: str,
    dots: int,
    voice_num: int,
    staff_num: int,
    tie_start: bool = False,
    tie_stop: bool = False,
    chord_sym: str | None = None,
    is_rest: bool = False,
) -> ET.Element:
    note = ET.Element("note")
    if is_rest:
        ET.SubElement(note, "rest")
    else:
        note.append(midi_to_pitch_element(pitch_num))

    dur_elem = ET.SubElement(note, "duration")
    dur_elem.text = str(dur_divs)

    if not is_rest:
        if tie_stop:
            ET.SubElement(note, "tie", type="stop")
        if tie_start:
            ET.SubElement(note, "tie", type="start")

    voice_elem = ET.SubElement(note, "voice")
    voice_elem.text = str(voice_num)

    ntype = ET.SubElement(note, "type")
    ntype.text = xml_type

    if dots > 0:
        for _ in range(dots):
            ET.SubElement(note, "dot")

    staff_elem = ET.SubElement(note, "staff")
    staff_elem.text = str(staff_num)

    if not is_rest and (tie_start or tie_stop):
        notations = ET.SubElement(note, "notations")
        if tie_stop:
            ET.SubElement(notations, "tied", type="stop")
        if tie_start:
            ET.SubElement(notations, "tied", type="start")

    if chord_sym and not is_rest:
        lyric = ET.SubElement(note, "lyric", number="1")
        ltext = ET.SubElement(lyric, "text")
        ltext.text = chord_sym

    return note


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
    - Dynamic measure grouping based on exact time signature beats and divisions
    - Note splitting across barlines with <tie> and <notations><tied> elements
    - Constant measure duration sums without overflow or underflow
    - 4 independent polyphonic SATB voices across two staves with safe <backup> boundaries
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

    divisions_per_quarter = 4
    default_ts = TimeSignature.parse(time_signature)

    curr_ts = default_ts
    prev_ts = None
    curr_measure_num = 1
    offset_in_measure_q = 0.0

    current_slices: list[NoteSlice] = []
    measures_data: list[MeasureSliceData] = []

    STANDARD_REST_DURS = [
        (4.0, "whole", 0),
        (3.0, "half", 1),
        (2.0, "half", 0),
        (1.5, "quarter", 1),
        (1.0, "quarter", 0),
        (0.75, "eighth", 1),
        (0.5, "eighth", 0),
        (0.25, "sixteenth", 0),
    ]

    def close_current_measure():
        nonlocal curr_measure_num, offset_in_measure_q, current_slices, prev_ts, curr_ts
        rem_space = curr_ts.measure_duration_quarters - offset_in_measure_q
        while rem_space > 1e-4:
            found = False
            for q_val, xml_t, dots in STANDARD_REST_DURS:
                if q_val <= rem_space + 1e-4:
                    divs = int(round(q_val * divisions_per_quarter))
                    current_slices.append(
                        NoteSlice(
                            satb=(0, 0, 0, 0),
                            dur_divs=divs,
                            xml_type=xml_t,
                            dots=dots,
                            chord_sym=None,
                            tie_start=False,
                            tie_stop=False,
                            is_rest=True,
                        )
                    )
                    rem_space -= q_val
                    found = True
                    break
            if not found:
                break

        m_total_divs = int(round(curr_ts.measure_duration_quarters * divisions_per_quarter))
        time_changed = (curr_ts != prev_ts)
        measures_data.append(
            MeasureSliceData(
                measure_num=curr_measure_num,
                time_signature=curr_ts,
                time_sig_changed=time_changed,
                slices=current_slices,
                total_divisions=m_total_divs,
            )
        )
        prev_ts = curr_ts
        curr_measure_num += 1
        offset_in_measure_q = 0.0
        current_slices = []

    for i, v in enumerate(voicings):
        dur_raw = durations[i] if durations and i < len(durations) else "half"
        if isinstance(dur_raw, dict):
            dur_name = dur_raw.get("duration", "half")
            if "time_signature" in dur_raw and dur_raw["time_signature"]:
                note_ts = TimeSignature.parse(dur_raw["time_signature"])
                if note_ts != curr_ts:
                    if offset_in_measure_q > 1e-4:
                        close_current_measure()
                    curr_ts = note_ts
        else:
            dur_name = dur_raw

        dur_q = parse_duration_quarters(dur_name)
        chord_sym = (
            (chords[i].function if hasattr(chords[i], "function") else str(chords[i]))
            if chords and i < len(chords)
            else None
        )

        rem_q = dur_q
        is_first_slice = True

        while rem_q > 1e-4:
            space_q = curr_ts.measure_duration_quarters - offset_in_measure_q
            if space_q <= 1e-4:
                close_current_measure()
                space_q = curr_ts.measure_duration_quarters

            slice_q = min(rem_q, space_q)
            will_continue = (slice_q < rem_q - 1e-4)
            is_continuation = not is_first_slice

            slice_divs = int(round(slice_q * divisions_per_quarter))
            xml_type, dots = quarters_to_xml_type_and_dots(slice_q)

            current_slices.append(
                NoteSlice(
                    satb=to_satb(v),
                    dur_divs=slice_divs,
                    xml_type=xml_type,
                    dots=dots,
                    chord_sym=chord_sym,
                    tie_start=will_continue,
                    tie_stop=is_continuation,
                    is_rest=False,
                )
            )

            offset_in_measure_q += slice_q
            rem_q -= slice_q
            is_first_slice = False

    if offset_in_measure_q > 1e-4 or current_slices:
        close_current_measure()

    for m_data in measures_data:
        m_num = m_data.measure_num
        m_time_sig = m_data.time_signature
        time_changed = m_data.time_sig_changed
        m_total_divisions = m_data.total_divisions

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

        # Voice 1 (Soprano) - Staff 1
        for s in m_data.slices:
            note = make_note_element(
                pitch_num=s.satb[0],
                dur_divs=s.dur_divs,
                xml_type=s.xml_type,
                dots=s.dots,
                voice_num=1,
                staff_num=1,
                tie_start=s.tie_start,
                tie_stop=s.tie_stop,
                chord_sym=s.chord_sym,
                is_rest=s.is_rest,
            )
            measure.append(note)

        # Voice 2 (Alto) - Staff 1
        backup = ET.SubElement(measure, "backup")
        b_dur = ET.SubElement(backup, "duration")
        b_dur.text = str(m_total_divisions)

        for s in m_data.slices:
            note = make_note_element(
                pitch_num=s.satb[1],
                dur_divs=s.dur_divs,
                xml_type=s.xml_type,
                dots=s.dots,
                voice_num=2,
                staff_num=1,
                tie_start=s.tie_start,
                tie_stop=s.tie_stop,
                chord_sym=None,
                is_rest=s.is_rest,
            )
            measure.append(note)

        # Voice 3 (Tenor) - Staff 2
        backup2 = ET.SubElement(measure, "backup")
        b_dur2 = ET.SubElement(backup2, "duration")
        b_dur2.text = str(m_total_divisions)

        for s in m_data.slices:
            note = make_note_element(
                pitch_num=s.satb[2],
                dur_divs=s.dur_divs,
                xml_type=s.xml_type,
                dots=s.dots,
                voice_num=3,
                staff_num=2,
                tie_start=s.tie_start,
                tie_stop=s.tie_stop,
                chord_sym=None,
                is_rest=s.is_rest,
            )
            measure.append(note)

        # Voice 4 (Bass) - Staff 2
        backup3 = ET.SubElement(measure, "backup")
        b_dur3 = ET.SubElement(backup3, "duration")
        b_dur3.text = str(m_total_divisions)

        for s in m_data.slices:
            note = make_note_element(
                pitch_num=s.satb[3],
                dur_divs=s.dur_divs,
                xml_type=s.xml_type,
                dots=s.dots,
                voice_num=4,
                staff_num=2,
                tie_start=s.tie_start,
                tie_stop=s.tie_stop,
                chord_sym=None,
                is_rest=s.is_rest,
            )
            measure.append(note)

    rough_string = ET.tostring(root, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
