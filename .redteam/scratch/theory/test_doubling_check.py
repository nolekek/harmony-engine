import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.rules.doubling import check_main_triad_doubling
from src.harmony.core.types import Voicing

# Triad C major: C, E, G
# What if T5/3 has NO fifth (G)? E.g. Bass C3 (48), Tenor C3 (48), Alto E4 (64), Soprano C5 (72)
# Root = C (0), counts[0] = 3. Third = E (4), counts[4] = 1. Fifth = G (7), counts[7] = 0.
v_no_fifth = Voicing(soprano=72, alto=64, tenor=48, bass=48)
viols = check_main_triad_doubling(v_no_fifth, "T", key="C")
print("Violations for T with no fifth (C-C-E-C, T=B=C3):", [v.rule_id for v in viols])

# What about S=A unison? E.g. Bass C3(48), Tenor G3(55), Alto C4(60), Soprano C4(60)
v_sa_unison = Voicing(soprano=60, alto=60, tenor=55, bass=48)
viols_sa = check_main_triad_doubling(v_sa_unison, "T", key="C")
print("Violations for T with S=A=C4 (C-G-C-C):", [v.rule_id for v in viols_sa])
