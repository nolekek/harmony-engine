import sys
import os
import xml.etree.ElementTree as ET

# Add D:\aitraining to sys.path
sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing, Key, Chord, TimeSignature
from src.harmony.export.musicxml import export_to_musicxml
from backend.exporters import build_colored_musicxml

def inspect_xml(xml_str, label=""):
    print(f"=== Testing: {label} ===")
    try:
        root = ET.fromstring(xml_str)
    except Exception as e:
        print(f"FAILED PARSE: {e}")
        return False
    
    part_list = root.find("part-list")
    if part_list is None:
        print("FAIL: No part-list found!")
        return False
        
    part = root.find("part")
    if part is None:
        print("FAIL: No part found!")
        return False
        
    measures = part.findall("measure")
    print(f"Total measures: {len(measures)}")
    
    divisions = None
    divisions_per_quarter = 4
    
    for m in measures:
        m_num = m.attrib.get("number", "?")
        attrs = m.find("attributes")
        if attrs is not None:
            div_el = attrs.find("divisions")
            if div_el is not None and div_el.text:
                divisions = int(div_el.text)
                
            time_el = attrs.find("time")
            if time_el is not None:
                beats = int(time_el.find("beats").text)
                beat_type = int(time_el.find("beat-type").text)
                print(f"Measure {m_num} time sig: {beats}/{beat_type}, divisions: {divisions}")
        
        # Check notes by voice
        voice_durations = {1: 0, 2: 0, 3: 0, 4: 0}
        backups = m.findall("backup")
        notes = m.findall("note")
        
        for n in notes:
            v_el = n.find("voice")
            v = int(v_el.text) if v_el is not None and v_el.text else 1
            d_el = n.find("duration")
            d = int(d_el.text) if d_el is not None and d_el.text else 0
            voice_durations[v] = voice_durations.get(v, 0) + d
            
        # Check backups
        backup_durs = [int(b.find("duration").text) for b in backups if b.find("duration") is not None]
        
        print(f"Measure {m_num}: voice durations: {voice_durations}, backups: {backup_durs}")
        
    return True

if __name__ == "__main__":
    v_c_major = [
        Voicing(64, 60, 55, 48), # C4
        Voicing(65, 60, 57, 45), # A minor
        Voicing(67, 60, 55, 48), # C4
        Voicing(62, 59, 55, 43), # G
    ]
    
    time_signatures = ["4/4", "3/4", "2/4", "6/8", "3/8"]
    durations_sets = [
        ["half", "half", "half", "half"],
        ["quarter", "quarter", "quarter", "quarter"],
        ["dotted_half", "quarter", "half", "half"],
        ["whole", "half", "quarter", "eighth"],
        ["dotted_quarter", "eighth", "dotted_half", "sixteenth"],
    ]
    
    for ts in time_signatures:
        for ds in durations_sets:
            xml = export_to_musicxml(
                voicings=v_c_major,
                chords=["T", "VI", "T", "D"],
                key="C Major",
                time_signature=ts,
                durations=ds
            )
            inspect_xml(xml, f"TS={ts}, durs={ds}")
