"""
Performance and regression tests for SATB Harmonization pipeline.
Verifies execution time thresholds and mathematical identity of solutions
against saved golden references.
"""

from __future__ import annotations

import time
import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Key, Chord


GOLDEN_BENCHMARKS = [
    {
        "name": "c_maj_4",
        "melody": [64, 65, 62, 60],
        "key": "C Major",
        "expected_top_chords": [
            ["T", "S6", "D65", "T"],
            ["T", "II6", "D7", "T"],
            ["T", "S", "D", "T"],
        ],
        "expected_best_cost": 9.4,
    },
    {
        "name": "c_maj_8",
        "melody": [64, 65, 64, 65, 64, 62, 62, 60],
        "key": "C Major",
        "expected_top_chords": [
            ["T", "S6", "T", "S6", "T", "II6", "D7", "T"],
            ["T", "S", "T", "S", "T", "II6", "D7", "T"],
            ["T", "S6", "T", "II6", "T", "II6", "D7", "T"],
        ],
        "expected_best_cost": 24.4,
    },
    {
        "name": "c_maj_brigade_1",
        "melody": [64, 65, 64, 65, 64, 62, 60],
        "key": "C Major",
        "expected_top_chords": [
            ["T", "S", "T", "S", "K64", "D7", "T"],
            ["T", "S6", "T", "S6", "T", "D", "T"],
            ["T", "S6", "T", "S6", "T", "D7", "T"],
        ],
        "expected_best_cost": 17.4,
    },
    {
        "name": "g_maj_7",
        "melody": [71, 69, 71, 72, 71, 69, 67],
        "key": "G Major",
        "expected_top_chords": [
            ["T", "II6", "T", "S6", "T", "D6", "T"],
            ["T", "D6", "T", "S6", "T", "D6", "T"],
            ["T", "II6", "T", "D65", "T", "D6", "T"],
        ],
        "expected_best_cost": 23.35,
    },
    {
        "name": "c_maj_16",
        "melody": [64, 65, 64, 65, 64, 62, 62, 60] * 2,
        "key": "C Major",
        "expected_top_chords": [
            [
                "T", "S", "T", "S", "T", "II", "II", "S",
                "T", "S", "T", "S", "T", "II6", "D7", "T",
            ],
        ],
        "expected_best_cost": 50.4,
    },
]


def test_performance_threshold_8_notes():
    """8 notes must harmonize in < 1200 ms (soft threshold for CI/load)."""
    mel = [64, 65, 64, 65, 64, 62, 62, 60]
    harmonizer = Harmonizer()

    # Warm-up run
    harmonizer.harmonize(mel, key="C Major")

    t_start = time.perf_counter()
    res = harmonizer.harmonize(mel, key="C Major")
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert len(res.solutions) > 0, "No solutions returned"
    assert elapsed_ms < 1200.0, f"8-note harmonization took {elapsed_ms:.2f} ms (threshold: 1200 ms)"


def test_performance_threshold_32_notes():
    """32 notes must harmonize in < 3000 ms (soft threshold for CI/load)."""
    mel = [64, 65, 64, 65, 64, 62, 62, 60] * 4
    harmonizer = Harmonizer()

    t_start = time.perf_counter()
    res = harmonizer.harmonize(mel, key="C Major")
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert len(res.solutions) > 0, "No solutions returned"
    assert elapsed_ms < 3000.0, f"32-note harmonization took {elapsed_ms:.2f} ms (threshold: 3000 ms)"


@pytest.mark.parametrize("benchmark", GOLDEN_BENCHMARKS, ids=[b["name"] for b in GOLDEN_BENCHMARKS])
def test_golden_reference_identities(benchmark):
    """Ensures that optimizations do not alter mathematical solutions, ranking, or costs."""
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(benchmark["melody"], key=benchmark["key"])

    assert res.is_success is True, f"Failed on {benchmark['name']}: {res.message}"
    assert res.best_solution is not None

    actual_top_chords = [
        [c.function for c in s.chords] for s in res.solutions
    ]
    expected_top_chords = benchmark["expected_top_chords"]

    # Verify best solution chords match exactly
    assert actual_top_chords[0] == expected_top_chords[0], (
        f"Top-1 chord mismatch in {benchmark['name']}: "
        f"got {actual_top_chords[0]} vs expected {expected_top_chords[0]}"
    )

    # Verify best solution cost matches
    assert pytest.approx(res.best_solution.cost, abs=1e-4) == benchmark["expected_best_cost"], (
        f"Cost mismatch in {benchmark['name']}: "
        f"got {res.best_solution.cost} vs expected {benchmark['expected_best_cost']}"
    )

    # Verify top-3 chord progressions match
    for idx in range(min(len(actual_top_chords), len(expected_top_chords))):
        assert actual_top_chords[idx] == expected_top_chords[idx], (
            f"Rank {idx+1} chord mismatch in {benchmark['name']}: "
            f"got {actual_top_chords[idx]} vs expected {expected_top_chords[idx]}"
        )


def test_state_generator_cache_safety_and_mutation():
    """Ensures candidate voicing generation is immutable and pure."""
    key = Key("C", "Major")
    chord = Chord("T")
    cands1 = generate_candidate_voicings(64, chord, key=key)
    cands2 = generate_candidate_voicings(64, chord, key=key)

    assert cands1 == cands2
    assert len(cands1) > 0

    # Ensure modifying one returned list does not affect future calls
    cands1.pop()
    cands3 = generate_candidate_voicings(64, chord, key=key)
    assert len(cands3) == len(cands2)
