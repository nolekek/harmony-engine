"""
Automated Stress-Test Harness for Brigade Harmony Engine.
Executes 24-key iterations across escalating difficulty levels.
Target: 5 consecutive iterations of 24/24 successful, rule-compliant harmonizations without bugfixes.
"""

import sys
import os
import random
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.harmony.core.types import Key, Chord, Voicing, parse_key
from src.harmony.pipeline import Harmonizer
from src.harmony.rules.engine import RuleEngine
from scripts.generate_dataset import get_scale_pitches, NOTE_TO_PC

# The canonical 24 classical keys
TWENTY_FOUR_KEYS = [
    # 12 Majors
    ("C", "Major"),
    ("G", "Major"),
    ("D", "Major"),
    ("A", "Major"),
    ("E", "Major"),
    ("B", "Major"),
    ("F#", "Major"),
    ("Db", "Major"),
    ("Ab", "Major"),
    ("Eb", "Major"),
    ("Bb", "Major"),
    ("F", "Major"),
    # 12 Harmonic Minors
    ("A", "MinorHarmonic"),
    ("E", "MinorHarmonic"),
    ("B", "MinorHarmonic"),
    ("F#", "MinorHarmonic"),
    ("C#", "MinorHarmonic"),
    ("G#", "MinorHarmonic"),
    ("Eb", "MinorHarmonic"),
    ("Bb", "MinorHarmonic"),
    ("F", "MinorHarmonic"),
    ("C", "MinorHarmonic"),
    ("G", "MinorHarmonic"),
    ("D", "MinorHarmonic"),
]


def generate_level_melody(tonic: str, mode: str, level: int, seed: int) -> list[int]:
    """
    Synthesizes a textbook soprano cantus firmus adhering to Brigade rules across difficulty levels:
    - L1/L2: Length 6, stepwise motion with consonant 3rds.
    - L3: Length 8, 3rds and 4ths.
    - L4/L5: Length 8, 3rds, 4ths, and 5ths with classical contrary motion balance.
    """
    r = random.Random(seed)
    pitches = get_scale_pitches(tonic, mode)
    if not pitches:
        pitches = [60, 62, 64, 65, 67, 69, 71, 72]

    tonic_pc = NOTE_TO_PC.get(tonic, 0)
    is_minor = "minor" in mode.lower()
    deg7_pc = (tonic_pc + 11) % 12
    deg2_pc = (tonic_pc + 2) % 12
    deg6_pc = (tonic_pc + 8) % 12

    length = 6 if level <= 2 else 8
    max_leap = 4 if level <= 2 else (5 if level == 3 else 7)

    def is_step_ok(p1: int, p2: int) -> bool:
        d = p2 - p1
        ad = abs(d)
        if ad > max_leap or ad == 6:  # No excessive leap or tritone
            return False
        if is_minor and ad == 3 and {p1 % 12, p2 % 12} == {deg6_pc, deg7_pc}:
            return False  # No augmented second leap
        if p1 % 12 == deg7_pc and d != 1:
            return False  # Leading tone must step up to tonic
        if is_minor and p1 % 12 == deg6_pc and d > 0:
            return False  # Scale degree 6 in harmonic minor resolves downward
        return True

    for attempt in range(500):
        start_pcs = [tonic_pc, (tonic_pc + (3 if is_minor else 4)) % 12, (tonic_pc + 7) % 12]
        starts = [p for p in pitches if p % 12 in start_pcs and 60 <= p <= 74]
        path = [r.choice(starts or pitches)]

        success = True
        for i in range(1, length):
            curr = path[-1]
            if i == length - 1:
                # Cadence: resolve to tonic
                if curr % 12 == deg7_pc:
                    cand = curr + 1
                elif curr % 12 == deg2_pc:
                    cand = curr - 2
                else:
                    success = False
                    break
                if cand in pitches and 60 <= cand <= 78:
                    path.append(cand)
                else:
                    success = False
                    break
            elif i == length - 2:
                # Penultimate cadence preparation: must be scale degree 2 or 7
                cands = [p for p in pitches if p % 12 in (deg2_pc, deg7_pc) and is_step_ok(curr, p)]
                if not cands:
                    success = False
                    break
                path.append(r.choice(cands))
            else:
                # Melodic continuation
                cands = [p for p in pitches if is_step_ok(curr, p) and 60 <= p <= 78]
                # Classical rule: avoid more than 2 consecutive identical notes in vocal cantus
                if len(path) >= 2 and path[-1] == path[-2]:
                    cands = [p for p in cands if p != curr]
                if not cands:
                    success = False
                    break
                weights = [4 if 1 <= abs(p - curr) <= 2 else 1 for p in cands]
                path.append(r.choices(cands, weights=weights)[0])

        if success and len(path) == length:
            return path

    return path


def test_single_key(tonic: str, mode: str, level: int, seed: int, harmonizer: Harmonizer, engine: RuleEngine) -> tuple[bool, str, list[int], list[str]]:
    """Harmonizes and strictly verifies one key."""
    melody = generate_level_melody(tonic, mode, level, seed)
    key = Key(tonic=tonic, mode=mode)

    res = harmonizer.harmonize(melody=melody, key=key, max_plans=30)
    if not res.is_success or not res.best_solution:
        return False, f"Harmonizer rejected all plans: {res.message}", melody, []

    best = res.best_solution
    funcs = [c.function for c in best.chords]

    # Verify every single transition through RuleEngine
    prev_v = None
    prev_c = None
    for idx, (v, c) in enumerate(zip(best.voicings, best.chords)):
        is_downbeat = (idx % 2 == 0)
        vres = engine.validate(
            prev_voicing=prev_v,
            curr_voicing=v,
            prev_chord=prev_c,
            curr_chord=c,
            key=key,
            is_downbeat=is_downbeat,
        )
        if vres.has_hard_violations:
            errs = [f"{vi.rule_id}: {vi.description}" for vi in vres.hard_violations]
            return False, f"RuleEngine hard violation at chord {idx} ({c.function}): {errs}", melody, funcs

        prev_v = v
        prev_c = c

    return True, "OK", melody, funcs


def run_iteration(iteration_num: int, level: int, base_seed: int) -> tuple[int, list[dict[str, Any]]]:
    """Runs one full 24-key iteration."""
    harmonizer = Harmonizer()
    engine = RuleEngine()
    passed = 0
    failures = []

    print(f"\n{'='*70}")
    print(f"--- ИТЕРАЦИЯ {iteration_num} | УРОВЕНЬ СЛОЖНОСТИ {level} (24 тональности) ---")
    print(f"{'='*70}")

    for idx, (tonic, mode) in enumerate(TWENTY_FOUR_KEYS):
        key_seed = base_seed + iteration_num * 1000 + idx * 37
        ok, msg, melody, funcs = test_single_key(tonic, mode, level, key_seed, harmonizer, engine)
        key_name = f"{tonic} {mode}"
        if ok:
            passed += 1
            print(f"  [{idx+1:02d}/24] {key_name:<20} PASS | Chords: {' -> '.join(funcs)}")
        else:
            print(f"  [{idx+1:02d}/24] {key_name:<20} FAIL | Melody: {melody} | Error: {msg}")
            failures.append({
                "key": key_name,
                "melody": melody,
                "error": msg,
            })

    print(f"\nИТОГ ИТЕРАЦИИ {iteration_num}: {passed}/24 успешно.")
    return passed, failures


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter", type=int, default=1)
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--seed", type=int, default=100)
    parser.add_argument("--consecutive", type=int, default=1, help="Number of consecutive 24/24 iterations required")
    args = parser.parse_args()

    if args.consecutive > 1:
        print(f"\n🚀 Запуск марафона: требуется {args.consecutive} подряд успешных итераций 24/24 с эскалацией сложности!")
        consecutive_passed = 0
        current_iter = 1
        while consecutive_passed < args.consecutive and current_iter <= 20:
            lvl = min(consecutive_passed + 1, 5)
            passed, failures = run_iteration(current_iter, lvl, args.seed + current_iter * 77)
            if passed == 24:
                consecutive_passed += 1
                print(f"🔥 Серия побед: {consecutive_passed}/{args.consecutive} итераций 24/24!")
            else:
                consecutive_passed = 0
                print(f"💥 Сбой на итерации {current_iter}! Серия сброшена до 0.")
                sys.exit(1)
            current_iter += 1

        if consecutive_passed >= args.consecutive:
            print(f"\n🏆 ЦЕЛЬ ДОСТИГНУТА: {args.consecutive} ИТЕРАЦИЙ ПОДРЯД 24/24 БЕЗ ЕДИНОЙ ОШИБКИ!")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        passed, failures = run_iteration(args.iter, args.level, args.seed)
        if passed < 24:
            sys.exit(1)
        sys.exit(0)
