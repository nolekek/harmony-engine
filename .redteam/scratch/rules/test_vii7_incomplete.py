import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing, Chord, Key
from src.harmony.rules.doubling import check_seventh_chord_doubling

# C major, VII7 (B - D - F - Ab)
# Incomplete VII7 with doubled root B (leading tone!): B2 (47), B3 (59), D4 (62), Ab4 (68) - fifth F omitted!
v_bad_vii7 = Voicing(soprano=68, alto=62, tenor=59, bass=47)
chord_vii7 = Chord(function="VII7")
key_c = Key(tonic="C", mode="Major")

viol = check_seventh_chord_doubling(v_bad_vii7, chord_vii7, key=key_c)
print("Violations for VII7 with doubled leading tone and omitted fifth:", viol)
