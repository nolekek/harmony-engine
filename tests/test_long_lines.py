"""
Tests for long melodic lines (32-note arch, 16-note scale).
Verifies beam search adaptation, non-starvation, and performance thresholds.
"""

import time
import pytest
from src.harmony.pipeline import Harmonizer


def test_32_note_arch_harmonization():
    """32-note arch melody in C Major must successfully harmonize in < 3000 ms."""
    mel = [
        60, 62, 64, 65, 67, 69, 71, 72, 74, 72, 71, 69, 67, 65, 64, 62,
        60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60, 60,
    ]
    harmonizer = Harmonizer()
    # Warm-up run
    harmonizer.harmonize([60, 62, 64, 60], key="C Major")

    t_start = time.perf_counter()
    res = harmonizer.harmonize(mel, key="C Major")
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert len(res.solutions) > 0, "No solutions returned"
    assert res.best_solution is not None
    assert elapsed_ms < 3000.0, f"32-note arch took {elapsed_ms:.2f} ms (threshold: 3000 ms)"


def test_16_note_scale_harmonization():
    """16-note diatonic scale contour (гамма) in C Major must successfully harmonize in < 1200 ms."""
    mel = [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60, 60]
    harmonizer = Harmonizer()
    # Warm-up run
    harmonizer.harmonize([60, 62, 64, 60], key="C Major")

    t_start = time.perf_counter()
    res = harmonizer.harmonize(mel, key="C Major")
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert len(res.solutions) > 0, "No solutions returned"
    assert res.best_solution is not None
    assert elapsed_ms < 1200.0, f"16-note scale took {elapsed_ms:.2f} ms (threshold: 1200 ms)"
