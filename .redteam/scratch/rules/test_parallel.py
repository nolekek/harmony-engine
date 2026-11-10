import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing
from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
)

print("--- Test 1: Repeating voice ---")
# Suppose Bass repeats C3 -> C3 (d2 = 0)
# Soprano leaps G4 -> G4 (d1 = 0) - stationary
# What if Bass repeats C3 -> C3 (d2 = 0) while Soprano moves G4 -> D4 (int 7 -> 2)
# What if Soprano moves G4 -> G5 (octave leap) while Bass repeats C3 -> C3?
v1 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
v2 = Voicing(soprano=79, alto=60, tenor=55, bass=48)
print("S leaps octave 67->79, B holds 48->48:")
print("Parallel:", check_parallel_fifths_and_octaves(v1, v2))
print("Contrary:", check_contrary_fifths_and_octaves(v1, v2))

print("\n--- Test 2: Octave leap in one voice with parallel motion in other voice ---")
# S: G4 (67) -> G3 (55) (-12 octave leap down)
# B: C3 (48) -> C2 (36) (-12 octave leap down)
# Parallel fifths? C-G to C-G
v3 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
v4 = Voicing(soprano=55, alto=60, tenor=55, bass=36)
print("S leaps -12, B leaps -12 (same chord, both octave leap down):")
print("Parallel:", check_parallel_fifths_and_octaves(v3, v4))

print("\n--- Test 3: Parallel fifths with octave leap in one voice ---")
# Chord 1: C major (B=C3: 48, S=G4: 67, int 19 = 5th)
# Chord 2: D minor (B=D3: 50, S=A3: 57, int 7 = 5th)
# S went 67 -> 57 (leap down -10)
# B went 48 -> 50 (+2)
v5 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
v6 = Voicing(soprano=57, alto=62, tenor=57, bass=50)
print("C-G -> D-A where B moves up +2, but S leaps down -10 to avoid parallel fifths:")
print("Parallel:", check_parallel_fifths_and_octaves(v5, v6))
print("Contrary:", check_contrary_fifths_and_octaves(v5, v6))

print("\n--- Test 4: What if S moves +2 (G4->A4=69) and B leaps down an octave (C3=48 -> D2=38)? ---")
# dS = +2, dB = 38 - 48 = -10.
# Both C-G -> D-A!
v7 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
v8 = Voicing(soprano=69, alto=62, tenor=57, bass=38)
print("Parallel:", check_parallel_fifths_and_octaves(v7, v8))
print("Contrary:", check_contrary_fifths_and_octaves(v7, v8))
