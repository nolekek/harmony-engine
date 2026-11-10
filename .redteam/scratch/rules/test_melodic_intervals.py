import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing, Key
from src.harmony.rules.voice_leading import check_melodic_intervals

# 1. Diminished fifth leap down in Bass: IV (F2=41) -> VII (B2=47) in C major (step = 6)
# Or in A minor: Bass leaps F3 (53) -> B2 (47) (diminished 5th down = 6 semitones)
# In classical harmony, F -> B in bass followed by C is textbook!
v1 = Voicing(soprano=69, alto=65, tenor=60, bass=53)  # F in bass
v2 = Voicing(soprano=69, alto=64, tenor=59, bass=47)  # B in bass (dim 5th down: 53 -> 47, delta = -6)
key_a = Key(tonic="A", mode="MinorHarmonic")

viol = check_melodic_intervals(v1, v2, key=key_a)
print("Violations for legal diminished 5th leap down in bass:", viol)

# 2. Diminished 7th leap in soprano in A minor: G#4 (68) -> F5 (77) (delta = +9 semitones = dim 7th!)
v3 = Voicing(soprano=68, alto=64, tenor=59, bass=40)
v4 = Voicing(soprano=77, alto=64, tenor=57, bass=41)
viol_dim7 = check_melodic_intervals(v3, v4, key=key_a)
print("Violations for diminished 7th leap (9 semitones):", viol_dim7)

# 3. Augmented 5th leap in A minor: C4 (60) -> G#4 (68) (delta = +8 semitones = aug 5th!):
v5 = Voicing(soprano=60, alto=57, tenor=52, bass=45)
v6 = Voicing(soprano=68, alto=56, tenor=52, bass=40)
viol_aug5 = check_melodic_intervals(v5, v6, key=key_a)
print("Violations for augmented 5th leap (8 semitones):", viol_aug5)
