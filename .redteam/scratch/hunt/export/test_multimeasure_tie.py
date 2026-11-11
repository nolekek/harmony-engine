import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing
from src.harmony.export.musicxml import export_to_musicxml

def test_multimeasure_tie():
    v = [Voicing(60, 55, 52, 48)]
    xml = export_to_musicxml(
        voicings=v,
        time_signature="3/8",
        durations=["whole"]
    )
    root = ET.fromstring(xml)
    measures = root.findall(".//measure")
    print(f"Measures for 'whole' in 3/8: {len(measures)}")
    for i, m in enumerate(measures):
        n = m.find("note")
        ties = [t.attrib.get("type") for t in n.findall("tie")]
        tieds = [t.attrib.get("type") for t in n.findall(".//tied")]
        dur = n.find("duration").text
        is_rest = n.find("rest") is not None
        print(f"Measure {i+1} note: dur={dur}, rest={is_rest}, ties={ties}, tieds={tieds}")

if __name__ == "__main__":
    test_multimeasure_tie()
