"""
Reproduction script for Hidden (Direct) 5ths and 8ves (Item 3):
1. Only S-B are checked (inner voices exempt)
2. Stepwise soprano (|dS| <= 2) into 5th/8ve is NOT banned (correct)
3. Leap in soprano (|dS| > 2) into 5th/8ve in direct motion is banned (correct)
4. S-B direct motion into UNISON is falsely called "Hidden octave in outer voices"
5. Simultaneous double penalty: PARALLEL_OCTAVES and HIDDEN_FIFTHS_OCTAVES triggered together
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.voice_leading import (
    check_hidden_fifths_and_octaves,
    check_parallel_fifths_and_octaves,
    validate_voice_leading,
)
from src.harmony.core.types import Voicing

def run_tests():
    print("=== TEST 1: Stepwise soprano into pure 5th/8ve (not banned) ===")
    # S moves 65 -> 67 (+2), B moves 36 -> 48 (+12).
    # S and B both move up. Current int S-B = 67 - 48 = 19 (12th).
    # Soprano stepped (+2). Hidden 5th should NOT trigger.
    v_prev1 = Voicing(65, 60, 55, 36)
    v_curr1 = Voicing(67, 60, 55, 48)
    res1 = check_hidden_fifths_and_octaves(v_prev1, v_curr1)
    print("Stepwise soprano hidden 5th violations:", [r.rule_id for r in res1], "(Empty = OK)")

    print("\n=== TEST 2: Leaping soprano into pure 5th/8ve (banned) ===")
    # S moves 64 -> 67 (+3), B moves 36 -> 48 (+12).
    # Soprano leaped (+3). Hidden 5th should trigger.
    v_prev2 = Voicing(64, 60, 55, 36)
    v_curr2 = Voicing(67, 60, 55, 48)
    res2 = check_hidden_fifths_and_octaves(v_prev2, v_curr2)
    print("Leaping soprano hidden 5th violations:", [(r.rule_id, r.description) for r in res2])

    print("\n=== TEST 3: S-B direct motion into UNISON ===")
    # S and B both move down to 60 (unison). S moves 67 -> 60 (-7), B moves 53 -> 60 (+7 is contrary, let both move down:)
    # S moves 72 -> 60 (-12), B moves 64 -> 60 (-4).
    # Both move down into unison (60 - 60 = 0).
    v_prev3 = Voicing(72, 67, 64, 64)
    v_curr3 = Voicing(60, 60, 60, 60)
    res3 = check_hidden_fifths_and_octaves(v_prev3, v_curr3)
    print("Direct motion into unison violations:", [(r.rule_id, r.description) for r in res3])

    print("\n=== TEST 4: Double penalty on parallel octaves with soprano leap ===")
    # S moves 72 -> 76 (+4), B moves 60 -> 64 (+4). Both move up by major third.
    # Prev S-B = 12, Curr S-B = 12 (parallel octaves).
    # But because dS = +4 > 2, check_hidden_fifths_and_octaves ALSO triggers!
    v_prev4 = Voicing(72, 67, 64, 60)
    v_curr4 = Voicing(76, 71, 67, 64)
    all_res = validate_voice_leading(v_prev4, v_curr4)
    sb_rules = [r.rule_id for r in all_res if r.voices == (0, 3)]
    print("Simultaneous rules on S-B parallel leap:", sb_rules)

if __name__ == "__main__":
    run_tests()
