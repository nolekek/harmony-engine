# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.core.types import Key
from src.harmony.pipeline import Harmonizer

harmonizer = Harmonizer()
key = Key("C", "Major")
pitches = [77, 73, 71, 72] # F5, Db5, B4, C5
melody_objs = [{"pitch": p, "duration": "quarter", "is_downbeat": (i % 2 == 0)} for i, p in enumerate(pitches)]
res = harmonizer.harmonize(melody_objs, key=key)
print("Result with F5, Db5, B4, C5:", res.is_success)
if res.is_success:
    sol = res.solutions[0]
    print("Plan:", " -> ".join(c.function for c in sol.chords))
    print("Voicings:", [(v.s, v.a, v.t, v.b) for v in sol.voicings])
