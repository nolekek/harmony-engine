import sys
sys.path.insert(0, ".")
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Key, Chord
from src.harmony.rules.doubling import get_triad_tones

k_c_maj = Key("C", "Major")
k_c_min = Key("C", "MinorHarmonic")
k_a_min = Key("A", "MinorHarmonic")

def check_chord_generator(sym, key):
    tonic_pc, mode = (0, "MAJOR") if "Major" in key.mode else (0 if key.tonic=="C" else 9, "MINORHARMONIC")
    # Soprano pitch from root
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)
    cands = generate_candidate_voicings(root + 60, Chord(sym), key=key)
    print(f"Chord: {sym:6s} in {key.name:18s} -> {len(cands):2d} candidates")
    if cands:
        basses = sorted(set(v.bass % 12 for v in cands))
        print(f"       Bass pitch classes produced: {basses}")

print("=== CHECKING SEVENTH CHORD INVERSIONS IN C MAJOR ===")
for ch in ["D7", "D65", "D43", "D2", "VII7", "VII65", "VII43", "VII2", "II7", "II65", "II43", "II2"]:
    try:
        check_chord_generator(ch, k_c_maj)
    except Exception as e:
        print(f"Error on {ch}: {e}")

print("\n=== CHECKING SEVENTH CHORD INVERSIONS IN A MINOR ===")
for ch in ["D7", "D65", "D43", "D2", "VII7", "VII65", "VII43", "VII2", "II7", "II65", "II43", "II2"]:
    try:
        check_chord_generator(ch, k_a_min)
    except Exception as e:
        print(f"Error on {ch}: {e}")
