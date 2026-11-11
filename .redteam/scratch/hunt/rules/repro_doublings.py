"""
Reproduction script for Doubling Rules (Item 7):
1. Root position diminished triad VII (5/3) allows doubled leading tone without any violation
2. Suffix '-6' (e.g. 'VII-6', 'II-6') completely bypasses check_sextaccord_doubling
3. Passing / auxiliary 6/4 (T64, S64) has zero doubling validation (allows doubled 3rd or doubled root)
4. Main triads T/S/D 5/3 doubling invariants verified (doubled root required, doubled 3rd banned)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.doubling import (
    check_doubling,
    check_main_triad_doubling,
    check_sextaccord_doubling,
)
from src.harmony.core.types import Voicing

def run_tests():
    print("=== TEST 1: Root-position VII (5/3) with doubled leading tone ===")
    # In C major: VII is B, D, F. Leading tone is B (PC 11).
    # Voicing doubles B: B2(47), D3(50), F3(53), B3(59).
    # Doubling the leading tone is strictly forbidden across all classical harmony!
    v_vii = Voicing(59, 53, 50, 47)
    res1 = check_doubling(v_vii, "VII", key="C Major")
    print("VII 5/3 doubled leading tone violations:", [r.rule_id for r in res1], "(Empty = False Negative / Complete Bypass!)")

    print("\n=== TEST 2: Suffix '-6' (VII-6, II-6) bypasses sextaccord checks ===")
    # VII-6 with doubled leading tone (B):
    # D3(50), B3(59), B4(71), F4(65).
    v_vii6_bad = Voicing(65, 71, 59, 50)
    res2_dash = check_sextaccord_doubling(v_vii6_bad, "VII-6", key="C Major")
    res2_norm = check_sextaccord_doubling(v_vii6_bad, "VII6", key="C Major")
    print("VII-6 (with dash) violations:", [r.rule_id for r in res2_dash], "(Empty = Bypassed!)")
    print("VII6 (standard) violations:", [r.rule_id for r in res2_norm], "(Caught when spelled VII6)")

    print("\n=== TEST 3: Passing T64 allows doubled third and doubled root ===")
    # In C major: T64 (C-E-G over G in bass).
    # Classical rule: passing/auxiliary 6/4 MUST double the bass (G)!
    # Here: doubled third E (E3=52, E4=64):
    v_t64_doubled_third = Voicing(64, 60, 52, 43) # E4, C4, E3, G2
    res3 = check_doubling(v_t64_doubled_third, "T64", key="C Major")
    print("T64 with doubled third violations:", [r.rule_id for r in res3], "(Empty = False Negative / No doubling rule!)")

    print("\n=== TEST 4: Main triad T 5/3 with doubled third (correctly caught) ===")
    v_t_bad = Voicing(64, 55, 52, 48) # E4, G3, E3, C3 (doubled third E)
    res4 = check_main_triad_doubling(v_t_bad, "T", key="C Major")
    print("T 5/3 with doubled third violations:", [r.rule_id for r in res4])

if __name__ == "__main__":
    run_tests()
