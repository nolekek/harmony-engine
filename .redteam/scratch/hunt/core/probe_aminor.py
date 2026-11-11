import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.harmony.pipeline import Harmonizer
from src.harmony.rules.doubling import get_triad_tones
from src.harmony.core.types import parse_key

h = Harmonizer()

# A MinorHarmonic ascending
scale = [69, 71, 72, 74, 76, 77, 80, 81]
res = h.harmonize(scale, "A MinorHarmonic")
sol = res.best_solution
print("Chords:", [c.function for c in sol.chords])
for i, (v, c) in enumerate(zip(sol.voicings, sol.chords)):
    print(f"  {i}: chord={c.function:5} S={v.soprano} A={v.alto} T={v.tenor} B={v.bass} pcs={v.pitch_classes()}")
