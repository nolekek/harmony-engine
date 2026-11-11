import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing
from backend.exporters import build_colored_musicxml

def test_tied_chords():
    # 2 chords: first chord crosses barline (e.g., 4/4 with "dotted_half" + "half" -> 3 beats + 2 beats = 5 beats -> crosses into m2)
    # or in 3/4 with "whole" (4 beats -> 3 in m1, 1 in m2) + "half" (2 beats in m2)
    voicings = [
        Voicing(64, 60, 55, 48), # Chord 0: T
        Voicing(62, 59, 55, 43), # Chord 1: D
    ]
    chords = ["T", "D"]
    xml = build_colored_musicxml(
        voicings=voicings,
        chords=chords,
        key={"tonic": "C", "mode": "Major"},
        time_signature="3/4",
        durations=["whole", "half"]
    )
    
    root = ET.fromstring(xml)
    measures = root.findall(".//measure")
    print(f"Measures count: {len(measures)}")
    for m_idx, m in enumerate(measures, 1):
        bass_notes = [n for n in m.findall("note") if n.find("voice") is not None and n.find("voice").text == "4"]
        print(f"Measure {m_idx} bass notes count: {len(bass_notes)}")
        for b_idx, b in enumerate(bass_notes, 1):
            lyric = b.find(".//lyric/text")
            l_text = lyric.text if lyric is not None else None
            tie = [t.attrib.get("type") for t in b.findall("tie")]
            dur = b.find("duration").text
            print(f"  Bass note {b_idx}: dur={dur}, lyric={l_text}, tie={tie}")

if __name__ == "__main__":
    test_tied_chords()
