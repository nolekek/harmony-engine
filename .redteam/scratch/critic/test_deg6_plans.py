# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.pipeline import Harmonizer

h = Harmonizer()
r6 = h.harmonize([60, 62, 64, 65, 67, 69], key="C Major")
print("Number of solutions:", len(r6.solutions))
for s in r6.solutions:
    print([c.function for c in s.chords], "cost:", s.cost)
