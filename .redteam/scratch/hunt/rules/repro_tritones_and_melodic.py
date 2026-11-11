"""
Reproduction script for Tritone, Diminished/Augmented leaps, and Melodic intervals:
1. ч.5 -> ум.5 in similar motion is completely unchecked (false negative)
2. F4 -> B3 (augmented 4th down, -6 semitones) is missed (treated as dim 5th down)
3. B3 -> F4 (diminished 5th up, +6 semitones) is falsely banned as augmented 4th (+6)
4. Augmented 2nd leap (3 st) in Harmonic Major is missed (checked only if 'is_minor')
5. MELODIC_TWO_LEAPS_SAME_DIRECTION is dead code in RuleEngine.validate (prev2_voicing never passed)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_melodic_intervals,
    validate_voice_leading,
)
from src.harmony.rules.engine import RuleEngine
from src.harmony.core.types import Voicing

def run_tests():
    print("=== TEST 1: Perfect 5th -> Diminished 5th in similar motion ===")
    # S=72, A=67, T=60, B=48 -> int A-T = 7 (P5)
    # Move to: S=72, A=66 (F#4 or Gb4), T=60 (C4)?
    # Similar motion: both move down!
    # Alto moves 67 (G4) -> 66 (F#4), delta = -1
    # Tenor moves 60 (C4) -> 53 (F3)? delta = -7
    # Wait, in C: A: 67 (G4) -> 65 (F4), T: 60 (C4) -> 59 (B3).
    # Prev A-T: 67 - 60 = 7 (P5).
    # Curr A-T: 65 - 59 = 6 (dim 5th F-B!).
    # Both voices step down: dA = -2, dT = -1 (similar motion).
    v_prev1 = Voicing(76, 67, 60, 48)
    v_curr1 = Voicing(76, 65, 59, 45)
    res1 = check_parallel_fifths_and_octaves(v_prev1, v_curr1)
    print("P5 -> dim5 in similar motion violations:", [r.rule_id for r in res1], "(Empty = False Negative / Not caught!)")

    print("\n=== TEST 2: Augmented 4th leap DOWN (-6 semitones: F4 -> B3) ===")
    # In C major: F4 (65) to B3 (59) is augmented 4th DOWN (-6 semitones).
    # Classical harmony strictly forbids augmented 4th leaps!
    v_prev2 = Voicing(65, 60, 57, 48) # Soprano = F4
    v_curr2 = Voicing(59, 60, 57, 48) # Soprano = B3 (-6 semitones)
    res2 = check_melodic_intervals(v_prev2, v_curr2, key="C Major")
    print("Aug 4th down (F4->B3) violations:", [(r.rule_id, r.description) for r in res2], "(Empty = False Negative / Missed!)")

    print("\n=== TEST 3: Diminished 5th leap UP (+6 semitones: B3 -> F4) ===")
    # In C major: B3 (59) to F4 (65) is diminished 5th UP (+6 semitones).
    # Code description blindly claims it is augmented 4th!
    v_prev3 = Voicing(59, 60, 57, 48) # Soprano = B3
    v_curr3 = Voicing(65, 60, 57, 48) # Soprano = F4 (+6 semitones)
    res3 = check_melodic_intervals(v_prev3, v_curr3, key="C Major")
    print("Dim 5th up (B3->F4) violations:", [(r.rule_id, r.description) for r in res3])

    print("\n=== TEST 4: Augmented 2nd leap in Harmonic Major (Ab4 -> B4) ===")
    # In C Harmonic Major: Ab4 (68) -> B4 (71) is an augmented second (3 semitones).
    v_prev4 = Voicing(68, 60, 55, 48)
    v_curr4 = Voicing(71, 60, 55, 48)
    res4 = check_melodic_intervals(v_prev4, v_curr4, key="C Major")
    print("Augmented 2nd in Major key violations:", [r.rule_id for r in res4], "(Empty = False Negative / Missed!)")

    print("\n=== TEST 5: Two consecutive leaps in same direction via RuleEngine.validate ===")
    # S moves 60 -> 65 (+5) -> 71 (+6) - two consecutive upward leaps in soprano!
    re = RuleEngine()
    v_a = Voicing(60, 55, 52, 48)
    v_b = Voicing(65, 57, 52, 45)
    v_c = Voicing(71, 60, 55, 43)
    # validate v_b -> v_c
    res5 = re.validate(prev_voicing=v_b, curr_voicing=v_c, prev_chord="S", curr_chord="D", key="C Major")
    two_leaps = [r for r in res5.violations if r.rule_id == "MELODIC_TWO_LEAPS_SAME_DIRECTION"]
    print("RuleEngine.validate two leaps violations:", two_leaps, "(Empty = Dead Code in Engine!)")

if __name__ == "__main__":
    run_tests()
