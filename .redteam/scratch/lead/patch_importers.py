# -*- coding: utf-8 -*-
"""One-shot refactor: multi-part SATB MusicXML support in backend/importers.py."""
from pathlib import Path

path = Path(r"D:\aitraining\backend\importers.py")
text = path.read_text(encoding="utf-8")

start_marker = "    # Extract all notes grouped by measure and voice/staff"
end_marker = "    # Fifth to Key Tonic mapping"
start = text.index(start_marker)
end = text.index(end_marker)

new_block = '''    # Extract all notes grouped by measure and voice/staff
    def _extract_note(note: ET.Element) -> dict[str, Any] | None:
        if note.find("rest") is not None:
            return None
        pitch_elem = note.find("pitch")
        if pitch_elem is None:
            return None
        step_elem = pitch_elem.find("step")
        alter_elem = pitch_elem.find("alter")
        octave_elem = pitch_elem.find("octave")
        if step_elem is None or octave_elem is None or not step_elem.text or not octave_elem.text:
            return None
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
        duration_name = type_elem.text.strip().lower() if type_elem is not None and type_elem.text else "half"
        if note.find("dot") is not None:
            duration_name = f"dotted_{duration_name}"
        lyric_elem = note.find(".//lyric/text")
        lyric_text = lyric_elem.text.strip() if lyric_elem is not None and lyric_elem.text else ""
        return {
            "pitch": pitch,
            "name": midi_to_note_name(pitch),
            "duration": duration_name,
            "voice": voice_val,
            "staff": staff_val,
            "lyric": lyric_text,
        }

    parts = root.findall(".//part")
    satb_voicings: list[dict[str, Any]] = []
    chords_extracted: list[str] = []
    soprano_melody: list[dict[str, Any]] = []
    parts_have_measures = [p for p in parts if p.findall("measure")]

    if len(parts_have_measures) >= 4:
        # Choral SATB export (MuseScore/Sibelius): one <part> per voice,
        # ordered Soprano, Alto, Tenor, Bass. Staff/voice tags are then useless.
        voice_notes: list[list[dict[str, Any]]] = [[] for _ in range(4)]
        for vi, part in enumerate(parts_have_measures[:4]):
            for measure in part.findall("measure"):
                for note in measure.findall("note"):
                    info = _extract_note(note)
                    if info is not None:
                        voice_notes[vi].append(info)
        s_notes, a_notes, t_notes, b_notes = voice_notes

        for i, s_n in enumerate(s_notes):
            soprano_melody.append({
                "pitch": s_n["pitch"],
                "name": s_n["name"],
                "duration": s_n["duration"],
                "is_downbeat": (i == 0),
            })
        min_len = min(len(s_notes), len(a_notes), len(t_notes), len(b_notes))
        for i in range(min_len):
            satb_voicings.append({
                "soprano": s_notes[i]["pitch"],
                "alto": a_notes[i]["pitch"],
                "tenor": t_notes[i]["pitch"],
                "bass": b_notes[i]["pitch"],
                "measure": None,
                "is_downbeat": (i == 0),
            })
            chords_extracted.append(s_notes[i]["lyric"] or b_notes[i]["lyric"])
    else:
        # Two-staff or single-staff layout: classify by (staff, voice) tags.
        for m_idx, measure in enumerate(root.findall(".//measure"), start=1):
            s_notes, a_notes, t_notes, b_notes = [], [], [], []
            for note in measure.findall("note"):
                info = _extract_note(note)
                if info is None:
                    continue
                if info["staff"] == "1":
                    if info["voice"] == "1":
                        s_notes.append(info)
                    else:
                        a_notes.append(info)
                else:
                    if info["voice"] in ("1", "3"):
                        t_notes.append(info)
                    else:
                        b_notes.append(info)

            for i, s_n in enumerate(s_notes):
                soprano_melody.append({
                    "pitch": s_n["pitch"],
                    "name": s_n["name"],
                    "duration": s_n["duration"],
                    "is_downbeat": (i == 0),
                })

            min_len = (
                min(len(s_notes), len(a_notes), len(t_notes), len(b_notes))
                if (s_notes and a_notes and t_notes and b_notes)
                else 0
            )
            for i in range(min_len):
                satb_voicings.append({
                    "soprano": s_notes[i]["pitch"],
                    "alto": a_notes[i]["pitch"],
                    "tenor": t_notes[i]["pitch"],
                    "bass": b_notes[i]["pitch"],
                    "measure": m_idx,
                    "is_downbeat": (i == 0),
                })
                chords_extracted.append(s_notes[i]["lyric"] or b_notes[i]["lyric"])

'''

text = text[:start] + new_block + text[end:]
path.write_text(text, encoding="utf-8")
print("patched importers.py")
