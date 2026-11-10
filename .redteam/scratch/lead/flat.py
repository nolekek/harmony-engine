import sys, xml.etree.ElementTree as ET
sys.path.insert(0, r"D:\aitraining")
from src.harmony.export.musicxml import export_to_musicxml
xml=export_to_musicxml([(70,65,60,53)], durations=["half"], key="F Major")
root=ET.fromstring(xml)
for n in root.findall(".//note")[:1]:
    p=n.find("pitch"); print("Bb4 written as", p.find("step").text, p.find("alter").text if p.find("alter") is not None else 0, p.find("octave").text)
