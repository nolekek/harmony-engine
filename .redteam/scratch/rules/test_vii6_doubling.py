import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.core.types import Voicing, Chord, Key
from src.harmony.rules.doubling import check_sextaccord_doubling, check_doubling

# C major: VII6 is D - F - B (bass D)
# Leading tone is B. Suppose B is doubled (disaster in classical harmony!):
# Bass D3 (50), Tenor B3 (59), Alto F4 (65), Soprano B4 (71) -> doubled leading tone B!
v_vii6_doubled_lt = Voicing(soprano=71, alto=65, tenor=59, bass=50)
chord_vii6 = Chord(function="VII6")
key_c = Key(tonic="C", mode="Major")

print("check_sextaccord_doubling on VII6 with doubled leading tone:", check_sextaccord_doubling(v_vii6_doubled_lt, chord_vii6, key=key_c))
print("check_doubling on VII6 with doubled leading tone:", check_doubling(v_vii6_doubled_lt, chord_vii6, key=key_c))
