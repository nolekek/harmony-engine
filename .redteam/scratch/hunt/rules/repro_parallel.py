"""
Reproduction script for Parallel and Contrary 5ths/8ves edge cases:
1. Direct motion from 5th to 12th falsely flagged as PARALLEL_FIFTHS
2. Direct motion from 12th to 5th falsely flagged as PARALLEL_FIFTHS
3. Direct motion from Unison to Octave falsely flagged as PARALLEL_OCTAVES
4. Direct motion from Octave to Unison falsely flagged as PARALLEL_OCTAVES
5. Contrary 5ths: compound fifth of 31 semitones missed
6. Oblique motion into 5th/8ve: correctly not banned
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
)
from src.harmony.core.types import Voicing

def run_tests():
    print("=== TEST 1: Similar motion 5th -> 12th (octave leap in one voice) ===")
    # S=79 (G5), A=67 (G4), T=60 (C4), B=48 (C3)
    # Alto moves 67 -> 81 (+14 semitones: octave leap + step)
    # Tenor moves 60 -> 62 (+2 semitones: step)
    # Both move UP (dA*dT = 28 > 0). Previous int A-T = 7 (P5). Current int A-T = 19 (P12).
    # This is similar motion into a 12th, NOT parallel fifths!
    v_prev1 = Voicing(79, 67, 60, 48)
    v_curr1 = Voicing(81, 81, 62, 45)
    res1 = check_parallel_fifths_and_octaves(v_prev1, v_curr1)
    for r in res1:
        if r.voices == (1, 2):
            print(f"FAILED (False Positive): {r.rule_id} on A-T: {r.description}")

    print("\n=== TEST 2: Similar motion 12th -> 5th ===")
    # Alto moves 79 -> 65 (-14 semitones), Tenor moves 60 -> 58 (-2 semitones).
    # Prev int: 79 - 60 = 19 (P12). Curr int: 65 - 58 = 7 (P5).
    # Both move DOWN (dA*dT > 0). Similar motion, NOT parallel fifths.
    v_prev2 = Voicing(79, 79, 60, 48)
    v_curr2 = Voicing(72, 65, 58, 41)
    res2 = check_parallel_fifths_and_octaves(v_prev2, v_curr2)
    for r in res2:
        if r.voices == (1, 2):
            print(f"FAILED (False Positive): {r.rule_id} on A-T: {r.description}")

    print("\n=== TEST 3: Similar motion Unison -> Octave ===")
    # S=72, A=60, T=60 (unison), B=48.
    # Alto leaps 60 -> 74 (+14), Tenor steps 60 -> 62 (+2).
    # Both move UP. Previous int A-T = 0. Current int A-T = 12.
    v_prev3 = Voicing(72, 60, 60, 48)
    v_curr3 = Voicing(74, 74, 62, 45)
    res3 = check_parallel_fifths_and_octaves(v_prev3, v_curr3)
    for r in res3:
        if r.voices == (1, 2):
            print(f"FAILED (False Positive): {r.rule_id} on A-T: {r.description}")

    print("\n=== TEST 4: Similar motion Octave -> Unison ===")
    # S=79, A=72, T=60 (octave: 12), B=48.
    # Alto moves 72 -> 62 (-10), Tenor moves 60 -> 62 (+2)? No, similar:
    # S moves 79 -> 81 (+2), Alto leaps 67 -> 81 (+14). S-A was 12 (octave), became 0 (unison).
    v_prev4 = Voicing(79, 67, 60, 48)
    v_curr4 = Voicing(81, 81, 62, 45)
    res4 = check_parallel_fifths_and_octaves(v_prev4, v_curr4)
    for r in res4:
        if r.voices == (0, 1):
            print(f"FAILED (False Positive): {r.rule_id} on S-A: {r.description}")

    print("\n=== TEST 5: Contrary fifths with compound fifth of 31 semitones ===")
    # Bass=36 (C2), Soprano=67 (G4): distance 31 semitones (2 octaves + 5th).
    # Contrary motion: Bass moves 36 -> 43 (+7), Soprano moves 67 -> 62 (-5).
    # Current distance: 62 - 43 = 19 semitones (contrary 12th).
    v_prev5 = Voicing(67, 60, 55, 36)
    v_curr5 = Voicing(62, 59, 55, 43)
    res5 = check_contrary_fifths_and_octaves(v_prev5, v_curr5)
    print(f"Contrary fifths detected (31 -> 19): {[r.rule_id for r in res5]} (Empty = False Negative / Missed!)")

    print("\n=== TEST 6: Oblique motion into pure 5th / 8ve ===")
    # Tenor stays 60, Alto moves 65 -> 67 (+2). Prev int 5 (P4), Curr int 7 (P5).
    v_prev6 = Voicing(72, 65, 60, 48)
    v_curr6 = Voicing(72, 67, 60, 48)
    res6 = check_parallel_fifths_and_octaves(v_prev6, v_curr6)
    print(f"Oblique motion into 5th violations: {[r.rule_id for r in res6]} (Empty = OK)")

if __name__ == "__main__":
    run_tests()
