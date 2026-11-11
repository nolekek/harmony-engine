"""
Reproduction script for K64 Cadential Syntax and Edge cases (Item 8):
1. K64 as the final chord of a piece is ACCEPTED as valid (false negative!):
   - When is_final_chord=True and curr_chord='K64', no subsequent chord exists,
     so SYNTAX_K64_MUST_RESOLVE_TO_D is never checked!
2. Incomplete K64 with tripled root and omitted fifth permitted on final chord:
   - doubling.py line 219 contains `group.upper() in ("T", "K64")`, permitting
     an absurd incomplete K64 that omits its own bass factor!
3. K64 on weak beat correctly banned (CADENCE_K64_STRONG_BEAT)
4. K64 as initial chord correctly banned (CADENCE_K64_INITIAL)
5. T64 != K64 syntax differentiation verified
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.engine import RuleEngine, check_syntax_rules
from src.harmony.rules.doubling import check_triad_completeness
from src.harmony.core.types import Voicing

def run_tests():
    print("=== TEST 1: K64 as final chord of a piece accepted as valid ===")
    re = RuleEngine()
    # Progression ending on K64: S -> K64 (is_final_chord=True)
    v_s = Voicing(65, 57, 48, 41) # S chord in C major (F4, A3, C3, F2)
    v_k = Voicing(64, 55, 48, 43) # K64 chord in C major (E4, G3, C3, G2)
    res1 = re.validate(
        prev_voicing=v_s,
        curr_voicing=v_k,
        prev_chord="S",
        curr_chord="K64",
        key="C Major",
        is_downbeat=True,
        is_final_chord=True,
    )
    print("K64 as final chord is_valid:", res1.is_valid)
    print("K64 as final chord violations:", [(r.rule_id, r.description) for r in res1.violations], "(Empty = False Negative / Piece ends on unresolved K64!)")

    print("\n=== TEST 2: Incomplete K64 with tripled root permitted on final chord ===")
    # Tripled root C (PC 0) and single third E (PC 4), omitting fifth G (PC 7):
    # In C major: C3(48), C4(60), C5(72), E4(64).
    v_incomplete_k64 = Voicing(72, 64, 60, 48)
    res2 = check_triad_completeness(v_incomplete_k64, "K64", key="C Major", is_final_chord=True)
    fifth_missing = [r for r in res2 if r.rule_id == "CHORD_FIFTH_MISSING"]
    print("Incomplete final K64 fifth missing violations:", fifth_missing, "(Empty = Incomplete K64 allowed without fifth!)")

    print("\n=== TEST 3: K64 on weak beat correctly banned ===")
    res3 = check_syntax_rules(prev_chord="S", curr_chord="K64", is_downbeat=False)
    print("K64 on weak beat violations:", [r.rule_id for r in res3])

    print("\n=== TEST 4: K64 as initial chord correctly banned ===")
    res4 = check_syntax_rules(prev_chord=None, curr_chord="K64", is_downbeat=True)
    print("K64 as initial chord violations:", [r.rule_id for r in res4])

    print("\n=== TEST 5: T64 != K64 syntax differentiation ===")
    res5 = check_syntax_rules(prev_chord=None, curr_chord="T64", is_downbeat=False)
    print("T64 on weak beat / initial chord violations:", [r.rule_id for r in res5], "(Empty = T64 exempt from K64 syntax rules)")

if __name__ == "__main__":
    run_tests()
