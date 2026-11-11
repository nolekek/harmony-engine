# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.core.types import Key
from src.harmony.pipeline import Harmonizer

key = Key("C", "Major")
pitches = [60, 64, 62, 65] # C4, E4, D4, F4
melody_objs = [{"pitch": p, "duration": "quarter", "is_downbeat": (i % 2 == 0)} for i, p in enumerate(pitches)]

harmonizer = Harmonizer()
res = harmonizer.harmonize(melody_objs, key=key)
print("Result for melody ending on degree 4 (F4):", res.is_success)
if res.is_success:
    sol = res.solutions[0]
    print("Chords:", [c.function for c in sol.chords])
