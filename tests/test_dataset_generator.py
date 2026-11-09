"""
Tests for Synthetic SATB Harmony Dataset Generator (scripts/generate_dataset.py).
"""

import pytest
from pathlib import Path
from scripts.generate_dataset import (
    generate_classical_melody,
    get_scale_pitches,
    harmonize_single_sample,
)
from src.harmony.core.types import Key


def test_get_scale_pitches_c_major():
    pitches = get_scale_pitches("C", "Major")
    assert len(pitches) > 0
    # All pitches must belong to C-major diatonic scale (C, D, E, F, G, A, B)
    c_major_pcs = {0, 2, 4, 5, 7, 9, 11}
    for p in pitches:
        assert p % 12 in c_major_pcs
        assert 60 <= p <= 77


def test_get_scale_pitches_a_minor():
    pitches = get_scale_pitches("A", "MinorHarmonic")
    assert len(pitches) > 0
    # Harmonic minor: A, B, C, D, E, F, G#
    a_minor_pcs = {9, 11, 0, 2, 4, 5, 8}
    for p in pitches:
        assert p % 12 in a_minor_pcs


def test_generate_classical_melody_cadence():
    melody = generate_classical_melody("C", "Major", length=8)
    assert len(melody) == 8
    # Soprano range
    for p in melody:
        assert 60 <= p <= 77
    # Final note should be tonic (C)
    assert melody[-1] % 12 == 0


def test_harmonize_single_sample_valid():
    rec = harmonize_single_sample(
        sample_id=1,
        tonic="C",
        mode="Major",
        length=6,
        seed=42,
    )
    assert rec is not None
    assert rec["id"] == "sample_000001"
    assert rec["key"] == {"tonic": "C", "mode": "Major"}
    assert len(rec["melody"]) == 6
    assert len(rec["functions"]) == 6
    assert len(rec["satb"]) == 6
    assert rec["cost"] < float("inf")

    # Verify that each SATB voicing matches the melody soprano
    for note, satb in zip(rec["melody"], rec["satb"]):
        assert satb["soprano"] == note
        assert satb["soprano"] >= satb["alto"] >= satb["tenor"] >= satb["bass"]
