import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
    check_melodic_intervals,
)
from src.harmony.core.types import Voicing

# Test 1: Contrary octaves where octave goes to octave with voices exchanging?
# Say Bass C3 (48), Tenor C4 (60). Interval = 12.
# Next chord: Bass leaps down to F2 (41, delta = -7). Tenor leaps up to F4 (65, delta = +5).
# d1 = +5, d2 = -7. d1 * d2 < 0.
# abs(p1 - p2) = 12 % 12 = 0.
# abs(c1 - c2) = 24 % 12 = 0.
# Does check_contrary_fifths_and_octaves catch it?
v1 = Voicing(soprano=72, alto=64, tenor=60, bass=48)
v2 = Voicing(soprano=72, alto=64, tenor=65, bass=41)

contrary_violations = check_contrary_fifths_and_octaves(v1, v2)
print("Test 1 (contrary octave 12 -> 24 semitones):", [v.rule_id for v in contrary_violations])

# Test 2: Contrary octave where voices step: can voices step contrary from 8ve to 8ve?
# If Bass C3 (48), Tenor C4 (60).
# Next: Bass moves by step (e.g. D3 = 50, delta=+2).
# What would Tenor need to move to to get an octave or unison?
# If Tenor moves down, to D3 (50, unison, delta = -10 - not a step!), or D4 (62, delta = +2 - that's parallel, not contrary!).
# To move contrary and get an octave/unison, Tenor must move by delta = 2 - 12 = -10 (leap of a minor 7th!).
# Thus, between any adjacent voices moving by step, contrary 5th/8ve is IMPOSSIBLE without at least one voice leaping by 5 to 10 semitones!
print("Mathematical proof: for contrary 5ths/8ves, |d1| + |d2| must be >= 12.")

# Test 3: What about contrary motion from non-fifth into fifth?
# E.g. 6th -> 5th or 3rd -> 5th by contrary motion?
# In music theory, is contrary motion into a 5th forbidden if it wasn't a 5th before?
# NO! That's standard contrary motion! (e.g. 3rd expanding to 5th or 6th contracting to 5th is standard correct voice leading!)
# Only 5th -> 5th or 8ve -> 8ve by contrary motion is forbidden.
# But what if d1 or d2 is 0?
# E.g. Tenor stays on C4 (d1 = 0), Bass leaps C3 -> C2 (d2 = -12).
# If d1 = 0, d1 * d2 == 0, so d1 * d2 < 0 is FALSE!
v_stay = Voicing(soprano=72, alto=64, tenor=60, bass=48)
v_leap = Voicing(soprano=72, alto=64, tenor=60, bass=36)
print("Tenor stays, Bass leaps octave (octave -> double octave): contrary catches it?",
      [v.rule_id for v in check_contrary_fifths_and_octaves(v_stay, v_leap)])
print("Parallel catches it?",
      [v.rule_id for v in check_parallel_fifths_and_octaves(v_stay, v_leap)])
