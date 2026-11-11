# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.pipeline import Harmonizer

h = Harmonizer()
# Degree 3: C D E
r3 = h.harmonize([60, 62, 64], key="C Major")
print("Degree 3 (E4) success:", r3.is_success)
if r3.is_success:
    print("  Chords:", [c.function for c in r3.best_solution.chords])

# Degree 6: C D E F G A
r6 = h.harmonize([60, 62, 64, 65, 67, 69], key="C Major")
print("Degree 6 (A4) success:", r6.is_success)
if r6.is_success:
    print("  Chords:", [c.function for c in r6.best_solution.chords])
