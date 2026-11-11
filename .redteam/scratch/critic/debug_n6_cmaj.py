# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.pipeline import Harmonizer

key = Key("C", "Major")
grammar = HarmonicGrammar(key=key)
pitches = [65, 61, 59, 60] # F4, Db4, B3, C4
melody_objs = [{"pitch": p, "duration": "quarter", "is_downbeat": (i % 2 == 0)} for i, p in enumerate(pitches)]

plans = grammar.generate_plans(melody_objs, key=key)
print(f"Grammar generated {len(plans)} plans:")
for p in plans[:10]:
    print(" -> ".join(c.function for c in p))

harmonizer = Harmonizer()
res = harmonizer.harmonize(melody_objs, key=key)
print("Harmonizer result:", res.is_success)
if not res.is_success:
    print("Diagnostics:", res.diagnostics)
