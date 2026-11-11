"""
Reproduction script for Resolution Rules (Item 6):
1. VII6 (triad sextaccord) falsely treated as VII7 (seventh chord):
   - check_vii7_resolution throws RESOLUTION_VII7_DOUBLED_THIRD on normal VII6 -> T
   - check_main_triad_doubling forbids standard doubled root in T after VII6!
2. DD2 (Double dominant second chord) forced to resolve to T6:
   - check_d2_resolution throws RESOLUTION_D2_TO_T6 on canonical DD2 -> D6!
3. II7 (supertonic seventh) has ZERO resolution checks in resolutions.py:
   - Seventh of II7 can jump by an octave or move illegally without any rule firing!
4. D43 intra-dominant repositioning (e.g. D43 -> D65 or D7) is banned by check_d43_resolution:
   - Throws RESOLUTION_D43_TO_T6, demanding T/T6 even though dominant prolongation is valid.
5. D -> VI deceptive cadence third doubling:
   - Verified that third of VI (tonic pitch class) must be doubled.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.resolutions import (
    check_vii7_resolution,
    check_d2_resolution,
    check_d43_resolution,
    validate_resolutions,
)
from src.harmony.rules.doubling import check_main_triad_doubling
from src.harmony.core.types import Voicing

def run_tests():
    print("=== TEST 1: VII6 -> T falsely treated as VII7 ===")
    # In C major: VII6 notes are B, D, F. Bass = D3(50).
    # Normal authentic resolution to complete Tonic triad T (C, E, G, C - doubled root C!):
    # S=E4(64), A=C4(60), T=G3(55), B=C3(48).
    v_vii6 = Voicing(65, 62, 59, 50) # S=F4, A=D4, T=B3, B=D3
    v_t = Voicing(64, 60, 55, 48)    # S=E4, A=C4, T=G3, B=C3 (standard doubled root!)
    res1_vii7 = check_vii7_resolution(v_vii6, v_t, "VII6", "T", key="C Major")
    res1_doub = check_main_triad_doubling(v_t, "T", key="C Major", prev_chord="VII6")
    print("VII6 -> T check_vii7_resolution violations:")
    for r in res1_vii7:
        print(f"  FAILED (False Positive): {r.rule_id}: {r.description}")
    print("VII6 -> T check_main_triad_doubling violations:")
    for r in res1_doub:
        print(f"  FAILED (False Positive): {r.rule_id}: {r.description}")

    print("\n=== TEST 2: DD2 -> D6 canonical resolution banned ===")
    # In C major: DD2 (C-D-F#-A with C in bass).
    # Resolves canonically to D6 (dominant sextaccord with B in bass):
    # Bass steps down C3(48) -> B2(47).
    v_dd2 = Voicing(66, 62, 57, 48) # F#, D, A, C
    v_d6 = Voicing(67, 59, 55, 47)  # G, B, G, B
    res2 = check_d2_resolution(v_dd2, v_d6, "DD2", "D6", key="C Major")
    print("DD2 -> D6 check_d2_resolution violations:")
    for r in res2:
        print(f"  FAILED (False Positive): {r.rule_id}: {r.description}")

    print("\n=== TEST 3: II7 resolution missing in resolutions.py ===")
    # In C major: II7 is D-F-A-C. The 7th is C.
    # In II7 -> D, seventh C must step down to B.
    # What if 7th leaps up by 9 semitones to A (C4 -> A4)?
    v_ii7 = Voicing(60, 57, 53, 50) # S=C4 (7th), A=A3, T=F3, B=D3
    v_d_bad = Voicing(69, 59, 55, 43) # S=A4 (7th leaped up +9!), A=B3, T=G3, B=G2
    res3 = validate_resolutions(v_ii7, v_d_bad, "II7", "D", key="C Major")
    print("II7 -> D with illegal leaping seventh violations:", [r.rule_id for r in res3], "(Empty = False Negative / Missing check!)")

    print("\n=== TEST 4: D43 intra-dominant prolongation (D43 -> D65) banned ===")
    # D43 moving to D65 within dominant harmony (bass steps II -> III):
    # D43: B=D3(50), T=G3(55), A=B3(59), S=F4(65).
    # D65: B=F#3? No, in C: D43 bass is D, D65 bass is B (leading tone).
    # D43: D, F, G, B. Bass=50 (D3).
    # D7: Bass=43 (G2).
    v_d43 = Voicing(65, 59, 55, 50) # S=F4, A=B3, T=G3, B=D3
    v_d7 = Voicing(65, 59, 55, 43)  # S=F4, A=B3, T=G3, B=G2
    res4 = check_d43_resolution(v_d43, v_d7, "D43", "D7", key="C Major")
    print("D43 -> D7 check_d43_resolution violations:")
    for r in res4:
        print(f"  FAILED (False Positive): {r.rule_id}: {r.description}")

if __name__ == "__main__":
    run_tests()
