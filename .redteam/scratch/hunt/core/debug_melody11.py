import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.harmony.pipeline import Harmonizer
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.core.types import Key

h = Harmonizer()
g = HarmonicGrammar(Key.parse("C Major"))

# Let's inspect Melody #11 from fuzz_core.py
# Melody #11 was: C Major, 6/8, len 2
# Let's re-run generation with seed 42 to get the exact notes of #11
import random
random.seed(42)
from fuzz_core import generate_melodies
mels = generate_melodies()
k_str, meter, notes, tag = mels[11]
print(f"Melody #11: key={k_str}, meter={meter}, notes={notes}, tag={tag}")

res = h.harmonize(notes, k_str, time_signature=meter)
print(f"Success: {res.is_success}")
if res.best_solution:
    print(f"Chords: {[c.function for c in res.best_solution.chords]}")
    for i, v in enumerate(res.best_solution.voicings):
        print(f"  {i}: {v}")

# Now let's inspect what plans the grammar generated for Melody #11:
plans = g.generate_plans([{"pitch": p, "is_downbeat": i==0} for i, p in enumerate(notes)], Key.parse(k_str))
print("Grammar plans generated:")
for p in plans[:10]:
    print(" ", [c.function for c in p])
