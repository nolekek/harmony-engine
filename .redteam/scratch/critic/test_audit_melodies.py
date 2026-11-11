# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

harmonizer = Harmonizer()

melodies = [
    # 1. C major scale ascending
    {"name": "C major scale up", "key": Key("C", "Major"), "pitches": [60, 62, 64, 65, 67, 69, 71, 72]},
    # 2. C major scale descending
    {"name": "C major scale down", "key": Key("C", "Major"), "pitches": [72, 71, 69, 67, 65, 64, 62, 60]},
    # 3. A minor scale ascending
    {"name": "A minor scale up", "key": Key("A", "minor"), "pitches": [69, 71, 72, 74, 76, 77, 80, 81]},
    # 4. A minor scale descending
    {"name": "A minor scale down", "key": Key("A", "minor"), "pitches": [81, 79, 77, 76, 74, 72, 71, 69]},
    # 5. C major arpeggio
    {"name": "C major arpeggio", "key": Key("C", "Major"), "pitches": [60, 64, 67, 72, 67, 64, 60]},
    # 6. A minor arpeggio
    {"name": "A minor arpeggio", "key": Key("A", "minor"), "pitches": [69, 72, 76, 81, 76, 72, 69]},
    # 7. Neapolitan line in C major (Db4=61, C4=60)
    {"name": "Neapolitan N6 line (C maj)", "key": Key("C", "Major"), "pitches": [65, 61, 59, 60]}, # F4, Db4, B3, C4
    # 8. Chromatic bVI line in C major (Ab4=68)
    {"name": "Chromatic bVI line (C maj)", "key": Key("C", "Major"), "pitches": [67, 68, 67, 60]}, # G4, Ab4, G4, C4
    # 9. Repeated notes stasis
    {"name": "Repeated notes stasis", "key": Key("C", "Major"), "pitches": [60, 60, 60, 60]},
    # 10. Half-cadence ending on D (deg 2)
    {"name": "Half cadence ending on 2", "key": Key("C", "Major"), "pitches": [64, 65, 67, 62]}, # E4, F4, G4, D4
    # 11. Deceptive cadence ending on A (deg 6)
    {"name": "Deceptive cadence ending on 6", "key": Key("C", "Major"), "pitches": [64, 65, 67, 69]}, # E4, F4, G4, A4
    # 12. Leap-heavy melody
    {"name": "Leap heavy", "key": Key("C", "Major"), "pitches": [60, 67, 64, 72, 65, 62, 59, 60]},
    # 13. Short 3-note cadence
    {"name": "Short 3-note cadence", "key": Key("C", "Major"), "pitches": [64, 62, 60]},
    # 14. N6 in A minor (Bb4=70, G#4=68, A4=69)
    {"name": "Neapolitan N6 line (A min)", "key": Key("A", "minor"), "pitches": [74, 70, 68, 69]}, # D5, Bb4, G#4, A4
    # 15. bVI ending test
    {"name": "Ending on bVI", "key": Key("C", "Major"), "pitches": [64, 65, 67, 68]},
]

print("=== RUNNING HARMONIZER AUDIT SUITE ===")
for m in melodies:
    melody_objs = [{"pitch": p, "duration": "quarter", "is_downbeat": (i % 2 == 0)} for i, p in enumerate(m["pitches"])]
    try:
        res = harmonizer.harmonize(melody_objs, key=m["key"])
        if res.is_success and res.solutions:
            sol = res.solutions[0]
            fns = [c.function for c in sol.chords]
            voicings = [(v.s, v.a, v.t, v.b) for v in sol.voicings]
            print(f"[{m['name']}] SUCCESS: {' -> '.join(fns)} (cost={sol.cost:.1f})")
            # Check voice leading flaws: parallel octaves/fifths in result?
            # Bass line
            bass_line = [v.b for v in sol.voicings]
            print(f"   Bass: {bass_line}")
        else:
            print(f"[{m['name']}] FAILED: no solutions! (res.is_success={res.is_success})")
    except Exception as e:
        print(f"[{m['name']}] EXCEPTION: {type(e).__name__}: {e}")
