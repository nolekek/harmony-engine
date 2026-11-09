"""
File importers for MusicXML and MIDI formats.
Extracts soprano melodies or full SATB voicings without altering core modules.
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from typing import Any

STEP_TO_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
PC_TO_STEP = {0: "C", 2: "D", 4: "E", 5: "F", 7: "G", 9: "A", 11: "B"}


def midi_to_note_name(pitch: int) -> str:
    """Converts MIDI pitch to readable note name like C4, F#3, Bb4."""
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (pitch // 12) - 1
    pc = pitch % 12
    return f"{names[pc]}{octave}"


def parse_text_melody(text: str, key_tonic: str = "C", key_mode: str = "Major") -> list[dict[str, Any]]:
    """
    Parses melody from text string.
    Supports:
    1. Note names with octave: 'C4 E4 F4 G4 E4 D4 C4' or comma-separated 'C4, E4, F4, G4'
    2. Note names with duration: 'C4:half E4:quarter F4:quarter'
    3. Scale degrees for theorists: '1 3 4 5 3 2 1' (maps relative to key_tonic in octave 4)
    4. Comma-separated MIDI pitch numbers: '60, 64, 65, 67, 64, 62, 60'
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    tokens = [t.strip().rstrip(",") for t in re.split(r"[\s,]+", cleaned) if t.strip().rstrip(",")]
    if not tokens:
        return []

    # Check if tokens are all scale degrees (e.g. '1', '3', '4', '5')
    all_degrees = all(t.isdigit() and 1 <= int(t) <= 8 for t in tokens)
    # Check if tokens are MIDI numbers (>= 36 and <= 96)
    all_midi = all(t.isdigit() and int(t) >= 36 for t in tokens)

    from src.harmony.core.types import Key
    parsed_key = Key(tonic=key_tonic, mode=key_mode)
    scale_pcs = parsed_key.scale_pcs

    melody: list[dict[str, Any]] = []

    if all_degrees:
        for i, tok in enumerate(tokens):
            deg = int(tok)
            # Map degree 1-7 to scale PC
            deg_idx = (deg - 1) % 7
            pc = scale_pcs[deg_idx]
            # Place in octave 4 or 5
            pitch = 60 + pc
            if pitch < 60:
                pitch += 12
            melody.append({
                "pitch": pitch,
                "is_downbeat": (i % 2 == 0),
                "duration": "half",
                "name": midi_to_note_name(pitch),
            })
        return melody

    if all_midi:
        for i, tok in enumerate(tokens):
            p = int(tok)
            melody.append({
                "pitch": p,
                "is_downbeat": (i % 2 == 0),
                "duration": "half",
                "name": midi_to_note_name(p),
            })
        return melody

    # Parse note names like C4, D#4, Eb4, G5
    note_pattern = re.compile(r"^([A-Ga-g])([#bB]?)(-?\d+)?(?::(\w+))?$")
    for i, tok in enumerate(tokens):
        m = note_pattern.match(tok)
        if not m:
            continue
        step = m.group(1).upper()
        acc = m.group(2)
        oct_str = m.group(3)
        dur_str = m.group(4) or "half"

        octave = int(oct_str) if oct_str is not None else 4
        pc = STEP_TO_PC.get(step, 0)
        if acc in ("#", "S"):
            pc = (pc + 1) % 12
        elif acc in ("B", "b"):
            pc = (pc - 1) % 12

        pitch = (octave + 1) * 12 + pc
        melody.append({
            "pitch": pitch,
            "is_downbeat": (i % 2 == 0),
            "duration": dur_str,
            "name": midi_to_note_name(pitch),
        })

    return melody


def parse_musicxml_content(xml_text: str) -> dict[str, Any]:
    """
    Parses MusicXML string to extract:
    - soprano melody (highest line / Voice 1)
    - full SATB voicings if available (for the Grader)
    - key signature (fifths, mode)
    - time signature
    """
    root = ET.fromstring(xml_text)

    # 1. Detect key attributes
    fifths = 0
    mode = "major"
    time_beats = 4
    time_beat_type = 4

    key_elem = root.find(".//key")
    if key_elem is not None:
        f_elem = key_elem.find("fifths")
        if f_elem is not None and f_elem.text:
            try:
                fifths = int(f_elem.text.strip())
            except ValueError:
                pass
        m_elem = key_elem.find("mode")
        if m_elem is not None and m_elem.text:
            mode = m_elem.text.strip().lower()

    time_elem = root.find(".//time")
    if time_elem is not None:
        b_elem = time_elem.find("beats")
        if b_elem is not None and b_elem.text:
            try:
                time_beats = int(b_elem.text.strip())
            except ValueError:
                pass
        bt_elem = time_elem.find("beat-type")
        if bt_elem is not None and bt_elem.text:
            try:
                time_beat_type = int(bt_elem.text.strip())
            except ValueError:
                pass

    # Extract all notes grouped by measure and voice/staff
    soprano_melody: list[dict[str, Any]] = []
    # Collect all measures
    measures = root.findall(".//measure")

    satb_voicings: list[dict[str, Any]] = []
    chords_extracted: list[str] = []

    for m_idx, measure in enumerate(measures, start=1):
        # Read notes in this measure
        # Group notes by (staff, voice) or collect SATB
        notes_in_measure = measure.findall("note")
        
        # We look for Soprano: staff=1 voice=1 (or first voice on staff 1)
        # Alto: staff=1 voice=2
        # Tenor: staff=2 voice=3 (or voice 1 on staff 2)
        # Bass: staff=2 voice=4 (or voice 2 on staff 2)

        s_notes = []
        a_notes = []
        t_notes = []
        b_notes = []

        for note in notes_in_measure:
            # Check if rest
            if note.find("rest") is not None:
                continue

            pitch_elem = note.find("pitch")
            if pitch_elem is None:
                continue

            step_elem = pitch_elem.find("step")
            alter_elem = pitch_elem.find("alter")
            octave_elem = pitch_elem.find("octave")

            if step_elem is None or octave_elem is None or not step_elem.text or not octave_elem.text:
                continue

            step = step_elem.text.strip().upper()
            octave = int(octave_elem.text.strip())
            alter = int(alter_elem.text.strip()) if alter_elem is not None and alter_elem.text else 0
            pc = (STEP_TO_PC.get(step, 0) + alter) % 12
            pitch = (octave + 1) * 12 + pc

            voice_elem = note.find("voice")
            staff_elem = note.find("staff")
            voice_val = voice_elem.text.strip() if voice_elem is not None and voice_elem.text else "1"
            staff_val = staff_elem.text.strip() if staff_elem is not None and staff_elem.text else "1"

            type_elem = note.find("type")
            duration_name = type_elem.text.strip() if type_elem is not None and type_elem.text else "half"

            lyric_elem = note.find(".//lyric/text")
            lyric_text = lyric_elem.text.strip() if lyric_elem is not None and lyric_elem.text else ""

            note_info = {
                "pitch": pitch,
                "name": midi_to_note_name(pitch),
                "duration": duration_name,
                "voice": voice_val,
                "staff": staff_val,
                "lyric": lyric_text,
            }

            # Classify into SATB
            if staff_val == "1":
                if voice_val == "1":
                    s_notes.append(note_info)
                else:
                    a_notes.append(note_info)
            else:
                if voice_val in ("1", "3"):
                    t_notes.append(note_info)
                else:
                    b_notes.append(note_info)

        # For soprano melody: take all s_notes
        for i, s_n in enumerate(s_notes):
            soprano_melody.append({
                "pitch": s_n["pitch"],
                "name": s_n["name"],
                "duration": s_n["duration"],
                "is_downbeat": (i == 0),
            })

        # Synchronize into SATB slices for this measure
        min_len = min(len(s_notes), len(a_notes), len(t_notes), len(b_notes)) if (s_notes and a_notes and t_notes and b_notes) else 0
        for i in range(min_len):
            satb_voicings.append({
                "soprano": s_notes[i]["pitch"],
                "alto": a_notes[i]["pitch"],
                "tenor": t_notes[i]["pitch"],
                "bass": b_notes[i]["pitch"],
                "measure": m_idx,
                "is_downbeat": (i == 0),
            })
            chord_lbl = s_notes[i]["lyric"] or b_notes[i]["lyric"]
            chords_extracted.append(chord_lbl)

    # Fifth to Key Tonic mapping
    FIFTHS_TO_MAJOR = {
        0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#",
        -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db", -6: "Gb"
    }
    FIFTHS_TO_MINOR = {
        0: "A", 1: "E", 2: "B", 3: "F#", 4: "C#", 5: "G#", 6: "D#",
        -1: "D", -2: "G", -3: "C", -4: "F", -5: "Bb", -6: "Eb"
    }
    is_min = "min" in mode
    detected_tonic = (FIFTHS_TO_MINOR if is_min else FIFTHS_TO_MAJOR).get(fifths, "C")
    detected_mode = "MinorHarmonic" if is_min else "Major"

    return {
        "soprano_melody": soprano_melody,
        "satb_voicings": satb_voicings,
        "chords": chords_extracted,
        "detected_key": {"tonic": detected_tonic, "mode": detected_mode, "fifths": fifths},
        "time_signature": {"beats": time_beats, "beat_type": time_beat_type},
    }


def parse_midi_file(data: bytes) -> dict[str, Any]:
    """
    Parses binary MIDI file data using mido.
    Extracts soprano melody from the top melodic line.
    """
    import mido

    mid = mido.MidiFile(file=io.BytesIO(data))
    
    # Collect note-on events with timestamp
    events: list[dict[str, Any]] = []

    for track_idx, track in enumerate(mid.tracks):
        current_time = 0
        for msg in track:
            current_time += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                events.append({
                    "pitch": msg.note,
                    "time": current_time,
                    "channel": getattr(msg, "channel", 0),
                    "track": track_idx,
                })

    if not events:
        return {"soprano_melody": [], "satb_voicings": []}

    # Sort events by time
    events.sort(key=lambda e: e["time"])

    # Group notes that occur at roughly the same time (within 30 ticks)
    time_clusters: list[list[dict[str, Any]]] = []
    for ev in events:
        if not time_clusters:
            time_clusters.append([ev])
        else:
            last_time = time_clusters[-1][0]["time"]
            if abs(ev["time"] - last_time) <= 30:
                time_clusters[-1].append(ev)
            else:
                time_clusters.append([ev])

    soprano_melody: list[dict[str, Any]] = []
    satb_voicings: list[dict[str, Any]] = []

    for i, cluster in enumerate(time_clusters):
        # Sort notes by pitch descending (highest is soprano, lowest is bass)
        sorted_notes = sorted(cluster, key=lambda x: x["pitch"], reverse=True)
        soprano_note = sorted_notes[0]
        soprano_melody.append({
            "pitch": soprano_note["pitch"],
            "name": midi_to_note_name(soprano_note["pitch"]),
            "is_downbeat": (i % 2 == 0),
            "duration": "half",
        })

        if len(sorted_notes) >= 4:
            satb_voicings.append({
                "soprano": sorted_notes[0]["pitch"],
                "alto": sorted_notes[1]["pitch"],
                "tenor": sorted_notes[2]["pitch"],
                "bass": sorted_notes[3]["pitch"],
                "measure": (i // 2) + 1,
                "is_downbeat": (i % 2 == 0),
            })

    return {
        "soprano_melody": soprano_melody,
        "satb_voicings": satb_voicings,
    }
