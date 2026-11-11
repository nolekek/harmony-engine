"""
Property-based and scale matrix tests across all canonical classical keys.
12 tonics x (Major, MinorHarmonic) x (scale ascending, scale descending) = 48 cases.
Target: 0 failures (100% success rate with replanning assistance).
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

MAJOR_TONICS = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
MINOR_TONICS = ["A", "E", "B", "F#", "C#", "G#", "Eb", "Bb", "F", "C", "G", "D"]


def build_scale_8(key_obj: Key) -> tuple[list[int], list[int]]:
    """Builds canonical 8-note ascending and descending scales in Soprano compass."""
    scale_pcs = key_obj.scale_pcs
    tonic_pc = key_obj.tonic_pc
    tonic_pitches = [p for p in range(60, 82) if p % 12 == tonic_pc]
    base_tonic = tonic_pitches[0] if tonic_pitches else 60

    asc = [base_tonic]
    curr = base_tonic
    for step in range(1, 8):
        next_pc = scale_pcs[step % 7]
        curr = next((p for p in range(curr + 1, curr + 4) if p % 12 == next_pc), curr + 1)
        asc.append(curr)

    if max(asc) > 81:
        if min(asc) - 12 >= 60:
            asc = [p - 12 for p in asc]

    desc = list(reversed(asc))
    return asc, desc


@pytest.fixture(scope="module")
def harmonizer():
    return Harmonizer()


SCALE_CASES = []
for tonic in MAJOR_TONICS:
    k = Key(tonic, "Major")
    asc, desc = build_scale_8(k)
    SCALE_CASES.append((f"{tonic} Major asc", k, asc))
    SCALE_CASES.append((f"{tonic} Major desc", k, desc))

for tonic in MINOR_TONICS:
    k = Key(tonic, "MinorHarmonic")
    asc, desc = build_scale_8(k)
    SCALE_CASES.append((f"{tonic} MinorHarmonic asc", k, asc))
    SCALE_CASES.append((f"{tonic} MinorHarmonic desc", k, desc))


@pytest.mark.parametrize("name, key_obj, melody", SCALE_CASES, ids=[c[0] for c in SCALE_CASES])
def test_scale_matrix_case(harmonizer, name, key_obj, melody):
    """
    Every scale in the 48-case matrix must resolve successfully without failure.
    Replanning automatically rescues micro-infeasible functional lattices.
    """
    # B/Bb octave scales exceed the strict C4-A5 soprano compass by one tone,
    # so the matrix exercises the documented extended-range mode.
    res = harmonizer.harmonize(melody, key_obj, allow_extended_ranges=True)
    assert res.is_success, f"Failed on {name}: {res.message}"
    assert res.best_solution is not None
    assert len(res.best_solution.voicings) == 8
    assert len(res.best_solution.chords) == 8
