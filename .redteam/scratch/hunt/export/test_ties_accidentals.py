import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing
from src.harmony.export.musicxml import export_to_musicxml
from backend.exporters import build_colored_musicxml

def test_ties_and_accidentals():
    # Test 1: Note crossing barline in 3/4 with duration "whole" (4 beats > 3 beats)
    v = [Voicing(60, 55, 52, 48)]
    xml = export_to_musicxml(
        voicings=v,
        time_signature="3/4",
        durations=["whole"]
    )
    root = ET.fromstring(xml)
    measures = root.findall(".//measure")
    print(f"Measures for 'whole' in 3/4: {len(measures)}")
    assert len(measures) == 2, f"Expected 2 measures, got {len(measures)}"
    
    # Check measure 1 voice 1 note
    m1_n1 = measures[0].find("note")
    tie1 = m1_n1.findall("tie")
    tied1 = m1_n1.findall(".//tied")
    print(f"M1 note ties: {[t.attrib.get('type') for t in tie1]}, tied: {[t.attrib.get('type') for t in tied1]}")
    
    # Check measure 2 voice 1 note
    m2_n1 = measures[1].find("note")
    tie2 = m2_n1.findall("tie")
    tied2 = m2_n1.findall(".//tied")
    print(f"M2 note ties: {[t.attrib.get('type') for t in tie2]}, tied: {[t.attrib.get('type') for t in tied2]}")
    
    # Test 2: Keys and accidentals
    # Check all 24 canonical keys
    from backend.key_detector import CANONICAL_KEYS
    print("\nTesting accidental spellings across keys:")
    for k in CANONICAL_KEYS:
        tonic, mode, fifths = k["tonic"], k["mode"], k["fifths"]
        # SATB with some chromatic/altered notes
        v_test = [Voicing(61, 58, 54, 46)] # C#4/Db4, Bb3/A#3, F#3/Gb3, Bb2/A#2
        xml_k = export_to_musicxml(
            voicings=v_test,
            key={"tonic": tonic, "mode": mode},
            time_signature="4/4",
            durations=["whole"]
        )
        root_k = ET.fromstring(xml_k)
        # Check fifths in attributes
        f_val = int(root_k.find(".//fifths").text)
        assert f_val == fifths, f"Fifth mismatch for {tonic} {mode}: got {f_val}, expected {fifths}"
        
        # Check accidental spelling of voice 1 (pitch 61 = C# or Db)
        n1 = root_k.find(".//measure/note")
        p_el = n1.find("pitch")
        step = p_el.find("step").text
        alt_el = p_el.find("alter")
        alt = int(alt_el.text) if alt_el is not None else 0
        
        if fifths < 0 or (fifths == 0 and "b" in tonic.lower()):
            # Should be Db (step D, alter -1)
            assert step == "D" and alt == -1, f"Expected Db for {tonic} {mode} (fifths={fifths}), got {step}{alt}"
        elif fifths > 0:
            # Should be C# (step C, alter 1)
            assert step == "C" and alt == 1, f"Expected C# for {tonic} {mode} (fifths={fifths}), got {step}{alt}"

    print("All key/fifths tests passed!")

if __name__ == "__main__":
    test_ties_and_accidentals()
