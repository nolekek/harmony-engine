import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing
from src.harmony.export.musicxml import export_to_musicxml
from src.harmony.export.midi import export_to_midi
from backend.exporters import generate_midi_bytes

def test_meter_change():
    print("=== Testing Mid-Score Meter Change ===")
    voicings = [
        Voicing(64, 60, 55, 48), # m1: 4/4 half note (2 beats)
        Voicing(65, 60, 57, 45), # m1: 4/4 half note (2 beats) -> fills m1 (4 beats)
        Voicing(67, 60, 55, 48), # m2: switches to 3/4, dotted_half (3 beats) -> fills m2
        Voicing(62, 59, 55, 43), # m3: 3/4, dotted_half (3 beats) -> fills m3
    ]
    durations = [
        {"duration": "half", "time_signature": "4/4"},
        {"duration": "half", "time_signature": "4/4"},
        {"duration": "dotted_half", "time_signature": "3/4"},
        {"duration": "dotted_half", "time_signature": "3/4"},
    ]
    xml = export_to_musicxml(
        voicings=voicings,
        durations=durations,
        time_signature="4/4"
    )
    root = ET.fromstring(xml)
    measures = root.findall(".//measure")
    print(f"Total measures: {len(measures)}")
    for m in measures:
        m_num = m.attrib.get("number")
        time_el = m.find(".//time")
        ts_str = f"{time_el.find('beats').text}/{time_el.find('beat-type').text}" if time_el is not None else "no-change"
        durs = [int(n.find('duration').text) for n in m.findall('note') if n.find('voice').text == '1']
        backups = [int(b.find('duration').text) for b in m.findall('backup')]
        print(f"Measure {m_num}: time_sig={ts_str}, voice1 note durs={durs}, sum={sum(durs)}, backups={backups}")
        
    # Check MIDI
    midi_bytes = generate_midi_bytes(voicings, bpm=100, durations=durations, time_signature="4/4")
    import mido, io
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))
    for i, trk in enumerate(mid.tracks):
        ts_events = [msg for msg in trk if msg.type == "time_signature"]
        print(f"Track {i} TS events: {[f'{m.numerator}/{m.denominator} at t={m.time}' for m in ts_events]}")

if __name__ == "__main__":
    test_meter_change()
