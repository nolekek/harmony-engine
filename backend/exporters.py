"""
Exporters service wrapping core exporters and enriching MusicXML for OSMD rendering.
Adds voice-specific color attributes and places Sposobin functional analysis under the bass.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

from src.harmony.core.types import Chord, Key, Voicing
from src.harmony.export.ascii import format_ascii_score
from src.harmony.export.midi import export_to_midi
from src.harmony.export.musicxml import export_to_musicxml

VOICE_COLORS = {
    "1": "#2563eb",  # Soprano - Blue
    "2": "#16a34a",  # Alto - Green
    "3": "#ea580c",  # Tenor - Orange
    "4": "#dc2626",  # Bass - Red
}


def build_colored_musicxml(
    voicings: Sequence[Voicing | tuple[int, int, int, int] | dict[str, int]],
    chords: Sequence[Chord | str] | None = None,
    key: Any = None,
    title: str = "Гармонизация мелодии (Бригадный учебник)",
) -> str:
    """
    Generates standard MusicXML 3.1 partwise score and enriches it with:
    1. Color attributes per voice:
       - Voice 1 (Soprano): #2563eb (blue)
       - Voice 2 (Alto): #16a34a (green)
       - Voice 3 (Tenor): #ea580c (orange)
       - Voice 4 (Bass): #dc2626 (red)
    2. Relocates harmonic functional analysis (T, S, D, K64...) from soprano to Bass
       so OSMD renders Sposobin markings directly under the bass staff.
    """
    raw_xml = export_to_musicxml(voicings=voicings, chords=chords, key=key, title=title)
    
    root = ET.fromstring(raw_xml)

    # Process each measure
    measures = root.findall(".//measure")
    chord_idx = 0

    for measure in measures:
        notes = measure.findall("note")

        # Collect chords lyrics from voice 1 to transfer to voice 4 (Bass)
        measure_chords: list[str] = []
        for note in notes:
            voice_el = note.find("voice")
            v_val = voice_el.text.strip() if voice_el is not None and voice_el.text else "1"

            # Remove lyric from voice 1 if present
            if v_val == "1":
                lyric_el = note.find("lyric")
                if lyric_el is not None:
                    txt_el = lyric_el.find("text")
                    if txt_el is not None and txt_el.text:
                        measure_chords.append(txt_el.text.strip())
                    note.remove(lyric_el)

        # Apply voice colors and attach lyric to bass notes
        bass_note_counter = 0
        for note in notes:
            voice_el = note.find("voice")
            staff_el = note.find("staff")
            v_val = voice_el.text.strip() if voice_el is not None and voice_el.text else "1"
            staff_val = staff_el.text.strip() if staff_el is not None and staff_el.text else "1"

            # Color note
            color = VOICE_COLORS.get(v_val, "#000000")
            note.set("color", color)

            # If note is Bass (staff 2, voice 4), add lyric under bass
            if staff_val == "2" and v_val == "4":
                if bass_note_counter < len(measure_chords):
                    chord_text = measure_chords[bass_note_counter]
                    lyric = ET.SubElement(note, "lyric", number="1")
                    ltext = ET.SubElement(lyric, "text")
                    ltext.text = chord_text
                elif chords and chord_idx < len(chords):
                    c = chords[chord_idx]
                    sym = c.function if hasattr(c, "function") else str(c)
                    lyric = ET.SubElement(note, "lyric", number="1")
                    ltext = ET.SubElement(lyric, "text")
                    ltext.text = sym
                bass_note_counter += 1
                chord_idx += 1

    rough_string = ET.tostring(root, encoding="utf-8")
    from xml.dom import minidom
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def generate_midi_bytes(voicings: Sequence[Any], bpm: int = 80) -> bytes:
    """Generates standard MIDI file in-memory and returns raw bytes."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        export_to_midi(voicings=voicings, output_path=tmp_path, bpm=bpm)
        return tmp_path.read_bytes()
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
