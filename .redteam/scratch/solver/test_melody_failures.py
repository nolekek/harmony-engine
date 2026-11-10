import sys
sys.path.insert(0, ".")
from src.harmony.pipeline import Harmonizer
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.core.types import Key

h = Harmonizer()
g = HarmonicGrammar(Key("C", "Major"))

test_cases = [
    ("E4-E4-G4-E4-D4-C4 (repeated E4)", [64, 64, 67, 64, 62, 60]),
    ("E4-F4-E4-E4-D4-C4 (neighbor F4)", [64, 65, 64, 64, 62, 60]),
    ("C4-D4-E4-F4-G4-C4 (scale rise)", [60, 62, 64, 65, 67, 72]),
    ("E4-G4-A4-G4-F4-E4 (rising peak)", [64, 67, 69, 67, 65, 64]),
    ("C4-E4-G4-E4-C4 (arpeggio)", [60, 64, 67, 64, 60]),
    ("G4-F4-E4-D4-C4 (descending line)", [67, 65, 64, 62, 60]),
    ("E4-F4-G4-A4-G4-F4-E4-D4-C4", [64, 65, 67, 69, 67, 65, 64, 62, 60]),
    ("B3-C4-D4-C4 (low B3 below standard range 60)", [59, 60, 62, 60]),
]

for name, mel in test_cases:
    res = h.harmonize(mel, key="C Major")
    plans = g.generate_plans(mel, Key("C", "Major"))
    print(f"{name:45s} -> Success: {str(res.is_success):5s} | Plans: {len(plans):2d} | Msg: {res.message}")
