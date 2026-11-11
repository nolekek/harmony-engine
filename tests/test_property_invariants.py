"""
Property-based invariant tests across generated classical melodies.
Verifies T23 requirements:
- >= 100 melodies with < 40% refusal rate
- Invariants hold on all successful solutions:
  1. cost >= 0.0
  2. Strict SATB order without unisons (S > A > T > B)
  3. Third present in chord tones
  4. Alto/Tenor/Bass in chord tones
  5. Soprano in chord tones or non-chord tone
  6. No hard parallel fifths/octaves
  7. No hard hidden fifths/octaves
"""

import random
import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, parse_key
from src.harmony.rules.doubling import get_triad_tones
from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
)
from src.harmony.syntax.grammar import HarmonicGrammar
from scripts.generate_dataset import generate_classical_melody


@pytest.fixture(scope="module")
def harmonizer():
    return Harmonizer()


@pytest.fixture(scope="module")
def grammar():
    return HarmonicGrammar()


def test_property_invariants_100_melodies(harmonizer, grammar):
    """
    Generate 100 classical diatonic melodies with fixed seed.
    Verify refusal rate < 40% and all structural invariants on solutions.
    """
    rnd = random.Random(42)
    total = 100
    successes = 0
    refusals = 0

    for i in range(total):
        tonic = "C" if i % 2 == 0 else "A"
        mode = "Major" if i % 2 == 0 else "MinorHarmonic"
        length = rnd.randint(4, 10)
        mel = generate_classical_melody(tonic, mode, length=length, rng=rnd)
        key = Key(tonic, mode)

        res = harmonizer.harmonize(mel, key, allow_replanning=True)
        if not res.is_success:
            refusals += 1
            continue

        successes += 1
        sol = res.best_solution
        assert sol is not None
        assert sol.cost >= 0.0, f"Negative cost {sol.cost} for melody {mel}"

        tonic_pc, mode_str = parse_key(key)

        # 1. Per-chord / per-voicing invariants
        for idx, v in enumerate(sol.voicings):
            # Strict SATB voice order without unisons
            assert v.soprano > v.alto > v.tenor > v.bass, (
                f"Voice crossing/unison at {idx}: S={v.soprano}, A={v.alto}, T={v.tenor}, B={v.bass}"
            )

            chord_fn = sol.chords[idx].function

            # Third present in voicing
            _, third_pc, _ = get_triad_tones(chord_fn, tonic_pc, mode_str)
            v_pcs = {v.soprano % 12, v.alto % 12, v.tenor % 12, v.bass % 12}
            assert third_pc in v_pcs, f"Third missing in chord {chord_fn} at {idx}: voicing={v}"

            # Alto, Tenor, Bass strictly in chord pitch classes
            chord_pcs = grammar.get_chord_pitch_classes(chord_fn, key)
            assert v.alto % 12 in chord_pcs, f"Alto {v.alto} not in chord {chord_fn} ({chord_pcs})"
            assert v.tenor % 12 in chord_pcs, f"Tenor {v.tenor} not in chord {chord_fn} ({chord_pcs})"
            assert v.bass % 12 in chord_pcs, f"Bass {v.bass} not in chord {chord_fn} ({chord_pcs})"

        # 2. Voice-leading transition invariants
        for idx in range(len(sol.voicings) - 1):
            v1 = sol.voicings[idx]
            v2 = sol.voicings[idx + 1]

            p_viols = check_parallel_fifths_and_octaves(v1, v2)
            hard_p = [p for p in p_viols if p.is_hard]
            assert not hard_p, f"Parallel 5/8 between {idx} and {idx+1}: {hard_p}"

            h_viols = check_hidden_fifths_and_octaves(v1, v2)
            hard_h = [h for h in h_viols if h.is_hard]
            assert not hard_h, f"Hidden 5/8 between {idx} and {idx+1}: {hard_h}"

    refusal_rate = refusals / total
    assert refusal_rate < 0.40, f"Refusal rate too high: {refusal_rate:.2%} (limit is 40%)"
    assert successes >= 60, f"Too few successes: {successes}/{total}"
