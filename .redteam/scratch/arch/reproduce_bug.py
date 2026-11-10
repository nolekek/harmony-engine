import json
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver

harmonizer = Harmonizer()
key = Key("C", "Major")

# Test 1: Default UI melody (E4 F4 G4 E4 D4 C4)
melody_default = [
    {"pitch": 64, "duration": "half", "is_downbeat": True},   # E4
    {"pitch": 65, "duration": "half", "is_downbeat": False},  # F4
    {"pitch": 67, "duration": "half", "is_downbeat": True},   # G4
    {"pitch": 64, "duration": "half", "is_downbeat": False},  # E4
    {"pitch": 62, "duration": "half", "is_downbeat": True},   # D4
    {"pitch": 60, "duration": "whole", "is_downbeat": False}, # C4
]

res1 = harmonizer.harmonize(melody=melody_default, key=key)
print(f"Default melody: success={res1.is_success}, solutions={len(res1.solutions)}")
if res1.best_solution:
    print("Top-1 voicings:")
    for i, v in enumerate(res1.best_solution.voicings):
        ch = res1.best_solution.chords[i].function
        print(f"  Step {i} ({ch}): S={v.s}, A={v.a}, T={v.t}, B={v.b} | TB_diff={v.t - v.b}, SA_diff={v.s - v.a}")

# Test 2: Melody with a non-chord passing note on weak beat (e.g. E4 -> D4 -> C4, D4 passing)
# E4 (64), D4 (62), C4 (60)
melody_passing = [
    {"pitch": 64, "duration": "half", "is_downbeat": True},   # E4
    {"pitch": 62, "duration": "quarter", "is_downbeat": False},# D4 (passing)
    {"pitch": 60, "duration": "half", "is_downbeat": True},   # C4
]
res2 = harmonizer.harmonize(melody=melody_passing, key=key)
print(f"\nPassing note melody: success={res2.is_success}, message='{res2.message}'")

# Test 3: Melody with leap and minor key
key_am = Key("A", "MinorHarmonic")
# Melody: A4 (69) -> C5 (72) -> B4 (71) -> G#4 (68) -> A4 (69)
melody_minor = [
    {"pitch": 69, "duration": "half", "is_downbeat": True},
    {"pitch": 72, "duration": "half", "is_downbeat": False},
    {"pitch": 71, "duration": "half", "is_downbeat": True},
    {"pitch": 68, "duration": "half", "is_downbeat": False},
    {"pitch": 69, "duration": "whole", "is_downbeat": True},
]
res3 = harmonizer.harmonize(melody=melody_minor, key=key_am)
print(f"\nMinor melody with G#: success={res3.is_success}, solutions={len(res3.solutions)}, message='{res3.message}'")

# Test 4: Melody where all plans are rejected
# Melody ending with leap into degree 4 on downbeat: C4 -> F4
melody_fail = [
    {"pitch": 60, "duration": "half", "is_downbeat": True},
    {"pitch": 65, "duration": "half", "is_downbeat": True},
]
res4 = harmonizer.harmonize(melody=melody_fail, key=key)
print(f"\nLeap melody: success={res4.is_success}, solutions={len(res4.solutions)}, message='{res4.message}'")
