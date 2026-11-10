import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
    check_voice_overlapping,
    check_melodic_intervals,
    check_unisons,
)
from src.harmony.rules.spacing import (
    check_voice_ranges,
    check_voice_crossing,
    check_texture_spacing,
)
from src.harmony.rules.doubling import (
    check_doubling,
    get_triad_tones,
    check_main_triad_doubling,
    check_k64_doubling,
    check_seventh_chord_doubling,
)
from src.harmony.rules.resolutions import (
    check_seventh_resolution,
    check_d43_resolution,
    check_d2_resolution,
    check_leading_tone_resolution,
    check_vii7_resolution,
)
from src.harmony.rules.chromatic import check_false_relation
from src.harmony.core.types import Voicing, Key, Chord

print("--- Checking D43 vs D2 logic in resolutions.py ---")
# D43 in C major: notes are G (7), B (11), D (2), F (5).
# Bass of D43 in classical music is D (2) - the fifth!
# Target: T (C, E, G) - bass D goes to C (or E).
v_d43_classical = Voicing(soprano=67, alto=60, tenor=53, bass=50) # G4, C4? No: D43 = G, B, D, F -> S=G4(67), A=B3(59), T=F3(53), B=D3(50)
# In code: resolutions.py line 74 says:
# "D43 has the seventh in the bass (scale degree IV)."
# Let's test what check_d43_resolution does when D43 has D (fifth) in bass:
v_d43_real = Voicing(soprano=67, alto=59, tenor=53, bass=50) # B=50 (D3 = scale deg II)
v_t_res = Voicing(soprano=67, alto=60, tenor=52, bass=48)   # B=48 (C3 = scale deg I)
viols_d43 = check_d43_resolution(v_d43_real, v_t_res, prev_chord="D43", curr_chord="T", key="C")
print("Violations when D43 has classical bass (D3->C3 into T):")
for v in viols_d43:
    print(" -", v.rule_id, ":", v.description)

# What if D43 resolves to T6 as code expects with bass F3(53) -> E3(52)?
v_d43_bogus = Voicing(soprano=67, alto=59, tenor=50, bass=53) # B=53 (F3 = scale deg IV!)
v_t6 = Voicing(soprano=67, alto=60, tenor=48, bass=52)        # B=52 (E3 = scale deg III)
viols_bogus = check_d43_resolution(v_d43_bogus, v_t6, prev_chord="D43", curr_chord="T6", key="C")
print("Violations when D43 has F3 in bass resolving to T6:")
for v in viols_bogus:
    print(" -", v.rule_id, ":", v.description)

print("\n--- Checking Melodic Intervals in voice_leading.py ---")
# check_melodic_intervals:
# Does it check augmented 4th / dim 5th? step == 6
# What about augmented 5th (8 semitones, e.g. C to G#)?
# What about diminished 4th (4 semitones, e.g. G# down to E)?
# What about diminished 7th (9 semitones, e.g. B down to Ab)?
v_m1 = Voicing(soprano=68, alto=60, tenor=52, bass=48) # S = G#4 (68)
v_m2 = Voicing(soprano=60, alto=60, tenor=52, bass=48) # S = C4 (60) -> step = 8 (aug 5th or min 6th?)
# In 12-TET step 8 is minor 6th or aug 5th.
# But what about augmented 2nd in major? (e.g. Eb to F#)?
# In code: step == 3 and is_minor: only checks deg 6 to 7 in minor!
print("Melodic check for step=8 (could be aug 5th):", [v.rule_id for v in check_melodic_intervals(v_m1, v_m2, key="C")])

print("\n--- Checking Voice Overlapping in voice_leading.py ---")
# Overlapping:
# Line 187: if curr_satb[1] > prev_satb[0]: Alto rose above previous Soprano
# Line 225: if curr_satb[0] < prev_satb[1]: Soprano fell below previous Alto
# Is this strictly correct?
# In Brigade harmony: "Ни один голос не должен подниматься выше предшествующего звука соседнего верхнего голоса или опускаться ниже предшествующего звука соседнего нижнего голоса."
# What if curr == prev?curr_satb[1] == prev_satb[0]? The code uses strictly > and <. That matches!
