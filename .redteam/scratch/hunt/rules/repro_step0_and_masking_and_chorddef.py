"""
Reproduction script for Step 0, Hard Violation Masking, and ChordDefinition crashes:
1. Step 0 (prev=None):
   - validate_voice_leading(None, curr) raises ValueError (cannot parse None)
   - core.types.Chord(function='T', inversion=1) drops inversion=1 in parse_chord_symbol!
2. Masking of hard violations with soft penalties:
   - In viterbi.py, relax_soprano_intervals=True intercepts MELODIC_AUGMENTED_INTERVAL,
     bypasses hard_violations pruning, and substitutes trans_cost with compute_soft_cost.
3. ChordDefinition crashes:
   - VI + SECUNDA and III + SECUNDA crash with KeyError: 'seventh' on bass_pitch_class
     and validate_voicing()
   - from_string crashes with ValueError on T-6, S-6, D-6, CAD64, DD, DD7, DD65, DD43, DD2
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "src"))

from src.harmony.rules.voice_leading import validate_voice_leading
from src.harmony.core.types import Voicing, Chord, parse_chord_symbol
from src.harmony.core.chord import ChordDefinition, ChordFunction, Inversion
from src.harmony.core.key import Key, Mode
from src.harmony.core.pitch import PitchClass
from src.harmony.rules.engine import RuleEngine

def run_tests():
    print("=== TEST 1: Step 0 (prev=None) ===")
    v = Voicing(72, 67, 64, 48)
    try:
        validate_voice_leading(None, v)
        print("validate_voice_leading(None, v) did not crash")
    except Exception as e:
        print(f"validate_voice_leading(None, v) crashed with: {type(e).__name__}: {e}")

    # Chord(T, inversion=1) symbol bug
    c_t6 = Chord(function="T", inversion=1)
    sym = parse_chord_symbol(c_t6)
    print(f"parse_chord_symbol(Chord('T', inversion=1)) = {sym!r} (Expected 'T6', got 'T' - Inversion ignored!)")

    print("\n=== TEST 2: ChordDefinition KeyError on SECUNDA (VI2, III2) ===")
    k = Key(tonic=PitchClass(0), mode=Mode.MAJOR)
    for fn in (ChordFunction.VI, ChordFunction.III):
        cd = ChordDefinition(function=fn, inversion=Inversion.SECUNDA, key=k)
        try:
            b_pc = cd.bass_pitch_class
            print(f"{fn.name}2 bass_pitch_class = {b_pc}")
        except Exception as e:
            print(f"FAILED (Crash): {fn.name}2.bass_pitch_class crashed with {type(e).__name__}: {e}")

        try:
            is_val, reason = cd.validate_voicing([72, 69, 64, 55])
            print(f"{fn.name}2 validate_voicing result = {is_val}")
        except Exception as e:
            print(f"FAILED (Crash): {fn.name}2.validate_voicing crashed with {type(e).__name__}: {e}")

    print("\n=== TEST 3: ChordDefinition.from_string crashes ===")
    broken_symbols = ["T-6", "S-6", "D-6", "CAD64", "DD", "DD7", "DD65", "DD43", "DD2", "D7/V"]
    for s in broken_symbols:
        try:
            cd = ChordDefinition.from_string(s, k)
            print(f"from_string('{s}') succeeded")
        except Exception as e:
            print(f"FAILED (Crash): from_string('{s}') crashed with {type(e).__name__}: {e}")

    print("\n=== TEST 4: Masking of hard violations by soft cost in Viterbi ===")
    # Demonstrate that in viterbi.py line 244-251, relax_soprano_intervals=True
    # replaces float('inf') cost from MELODIC_AUGMENTED_INTERVAL with compute_soft_cost:
    re = RuleEngine()
    # Voicing transition with augmented 4th leap in soprano: F4(65) -> B4(71) (+6)
    v1 = Voicing(65, 60, 57, 48)
    v2 = Voicing(71, 60, 55, 43)
    res = re.validate(prev_voicing=v1, curr_voicing=v2, prev_chord="S", curr_chord="D", key="C Major")
    hard_viols = [v for v in res.violations if v.is_hard and v.rule_id == "MELODIC_AUGMENTED_INTERVAL"]
    print(f"RuleEngine detects hard violation: {[v.rule_id for v in hard_viols]}, cost={res.cost}")
    soft_replacement = re.compute_soft_cost(v1, v2)
    print(f"Viterbi falls back to compute_soft_cost = {soft_replacement:.2f} (Masking hard gate!)")

if __name__ == "__main__":
    run_tests()
