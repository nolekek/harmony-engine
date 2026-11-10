import sys
from pathlib import Path
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import calculate_metric_structure, TimeSignature
from src.harmony.export.musicxml import export_to_musicxml

melody = [
    {"pitch": 64, "duration": "half"},
    {"pitch": 65, "duration": "half"},
    {"pitch": 67, "duration": "half"},
    {"pitch": 64, "duration": "half"},
    {"pitch": 62, "duration": "half"},
    {"pitch": 60, "duration": "whole"},
]

info = calculate_metric_structure(melody, default_time_signature="4/4")
for i, item in enumerate(info):
    print(f"Note {i}: pitch={item['pitch']}, dur={item['duration']}, dur_q={item['duration_quarters']}, meas={item['measure']}, offset={item['offset_in_measure']}, db={item['is_downbeat']}")

voicings = [(64, 60, 55, 48), (65, 60, 57, 45), (67, 64, 55, 48), (64, 60, 55, 48), (62, 59, 55, 43), (60, 60, 55, 48)]
xml = export_to_musicxml(voicings=voicings, durations=[m["duration"] for m in melody], time_signature="4/4")
print("\n--- MEASURE 3 IN XML ---")
import xml.etree.ElementTree as ET
root = ET.fromstring(xml)
for m in root.findall(".//measure"):
    m_num = m.attrib.get("number")
    durations = [n.find("duration").text for n in m.findall("note") if n.find("duration") is not None]
    backups = [b.find("duration").text for b in m.findall("backup") if b.find("duration") is not None]
    types = [n.find("type").text for n in m.findall("note") if n.find("type") is not None]
    print(f"Measure {m_num}: notes={len(durations)}, durations={durations[:4]}, types={types[:4]}, backups={backups}")
