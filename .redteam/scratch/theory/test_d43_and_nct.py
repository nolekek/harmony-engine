import sys
sys.path.insert(0, r"D:\aitraining")

from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Key, Chord

# Test 1: Generate candidates for D43 in C major
# D43 tones in C major: G (root=7), B (third=11), D (fifth=2), F (seventh=5).
# Classical bass of D43: D (scale degree II = 2).
# Let's see what bass pitches state_generator creates for D43 when soprano is G4 (67):
c_d43 = Chord(function="D43")
key = Key("C", "Major")
candidates_d43 = generate_candidate_voicings(soprano_pitch=67, chord=c_d43, key=key)
print(f"Total D43 candidates for soprano G4 (67): {len(candidates_d43)}")
if candidates_d43:
    basses = set(c.bass % 12 for c in candidates_d43)
    print(f"Bass pitch classes in D43 candidates: {basses}")
    print("Does D43 have scale degree II (2 = D) in bass?", 2 in basses)
    print("Does D43 have scale degree IV (5 = F) in bass?", 5 in basses)

# Test 2: Passing tone in melody
# Say melody has D4 (62) over T (C major: C=0, E=4, G=7).
# D is pitch class 2. It is NOT in {0, 4, 7}.
c_t = Chord(function="T")
candidates_nct = generate_candidate_voicings(soprano_pitch=62, chord=c_t, key=key)
print(f"\nCandidates for T when soprano is passing note D4 (62): {len(candidates_nct)}")
