import sys
sys.path.insert(0, r"D:\aitraining")
from backend.key_detector import detect_key_from_melody

# A natural minor scale descending: A4 G4 F4 E4 D4 C4 B3 A3
# Pitches: 69, 67, 65, 64, 62, 60, 59, 57
nat_minor_a = [69, 67, 65, 64, 62, 60, 59, 57]
det = detect_key_from_melody(nat_minor_a)
print("A natural minor detected as:", det["name"])
print("Expected: a-moll (Ля минор)")

# What if melody has accidentals in text parser?
from backend.importers import parse_text_melody
parsed_sharp = parse_text_melody("C#4 D#4 E#4 F#4 G#4 A#4 B#4 C#5")
print("Parsed C# Major text:", [p["pitch"] for p in parsed_sharp])
det_sharp = detect_key_from_melody(parsed_sharp)
print("Detected key for C# Major text:", det_sharp["name"])
