import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing, Chord, Key
from src.harmony.rules.resolutions import check_seventh_resolution

# D7 to D65 in C major:
# G, B, D, F -> G, B, D, F where F (7th) stays on the same note!
# D7: S=F4 (65), A=D4 (62), T=B3 (59), B=G2 (43)
# D65: S=G4 (67), A=F4 (65), T=D4 (62), B=B2 (47)
# In D7, S had F4 (65). In D65, S moves to G4 (67). Alto takes F4 (65).
# Voice 0 (Soprano) had 7th F4, moved to G4 (+2) in dominant repositioning!
v_d7 = Voicing(soprano=65, alto=62, tenor=59, bass=43)
v_d65 = Voicing(soprano=67, alto=65, tenor=62, bass=47)
chord_d7 = Chord(function="D7")
chord_d65 = Chord(function="D65")
key_c = Key(tonic="C", mode="Major")

viol = check_seventh_resolution(v_d7, v_d65, chord_d7, chord_d65, key=key_c)
print("Violations when D7 moves to D65 with voice repositioning:", viol)

# What if F stays in the same voice: delta = 0
v_d7_2 = Voicing(soprano=65, alto=62, tenor=59, bass=43)
v_d65_2 = Voicing(soprano=65, alto=62, tenor=55, bass=47)  # S stays on F4 (65)
viol2 = check_seventh_resolution(v_d7_2, v_d65_2, chord_d7, chord_d65, key=key_c)
print("Violations when 7th stays in same voice (delta=0) between D7 inversions:", viol2)
