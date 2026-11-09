"""
Tests for state_generator and ViterbiSolver.
Verifies candidate generation and global optimal voice leading over benchmark tasks.
"""

import pytest
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.solver.viterbi import ViterbiSolver
from tests.corpus.benchmark_tasks import BENCHMARK_TASKS


def test_state_generator_tonic_c_major():
    key = Key(tonic="C", mode="Major")
    chord_t = Chord(function="T")
    # Soprano = E4 (64)
    candidates = generate_candidate_voicings(soprano_pitch=64, chord=chord_t, key=key)
    assert len(candidates) > 0

    for v in candidates:
        assert v.soprano == 64
        # Ordering
        assert v.soprano >= v.alto >= v.tenor >= v.bass
        # Spacing limits
        assert v.soprano - v.alto <= 12
        assert v.alto - v.tenor <= 12
        assert v.tenor - v.bass <= 24
        # Range limits
        assert 55 <= v.alto <= 74
        assert 48 <= v.tenor <= 67
        assert 40 <= v.bass <= 60
        # Doublings: in T, root C must be doubled (at least 2 C's)
        pcs = v.pitch_classes()
        assert pcs.count(0) >= 2  # C is doubled


def test_state_generator_k64_bass_doubling():
    key = Key(tonic="G", mode="Major")
    chord_k64 = Chord(function="K64")
    # Soprano = B4 (71)
    candidates = generate_candidate_voicings(soprano_pitch=71, chord=chord_k64, key=key)
    assert len(candidates) > 0

    for v in candidates:
        # In G-dur K64, bass is D (PC 2). Bass MUST be doubled!
        pcs = v.pitch_classes()
        assert v.bass % 12 == 2  # Bass is D
        assert pcs.count(2) >= 2  # D is doubled


@pytest.mark.parametrize("task", BENCHMARK_TASKS, ids=[t["id"] for t in BENCHMARK_TASKS])
def test_viterbi_solves_all_benchmarks(task):
    solver = ViterbiSolver()
    key = Key(tonic=task["key"]["tonic"], mode=task["key"]["mode"])
    result = solver.solve(
        melody=task["melody"],
        chords=task["ground_truth_functions"],
        key=key,
    )

    assert result.is_success, f"Viterbi failed on {task['id']}: {result.message}"
    assert result.voicings is not None
    assert len(result.voicings) == len(task["melody"])
    assert result.total_cost < float("inf")

    # Verify that each solved voicing has matching soprano pitch
    for v, mel in zip(result.voicings, task["melody"]):
        assert v.soprano == mel["pitch"]
