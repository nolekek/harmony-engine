"""
Regression test suite for Red Team findings (REPORT.md §1.2-1.3, §1.15; BK-02; DEF-01).
Tests core default max_plans, plan ordering heuristics, and diatonic harmonization.
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key


def test_default_melody_harmonizes_without_explicit_max_plans():
    """
    REPORT §1.15 (#44, #45): Default frontend melody E4-F4-G4-E4-D4-C4 [64,65,67,64,62,60]
    with durations half*5 + whole in C Major must harmonize successfully via
    Harmonizer().harmonize(...) without explicitly providing max_plans.
    """
    melody = [
        {"pitch": 64, "duration": "half", "is_downbeat": True},
        {"pitch": 65, "duration": "half", "is_downbeat": False},
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 64, "duration": "half", "is_downbeat": False},
        {"pitch": 62, "duration": "half", "is_downbeat": True},
        {"pitch": 60, "duration": "whole", "is_downbeat": False},
    ]
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(
        melody=melody,
        key=Key("C", "Major"),
        time_signature="4/4",
    )
    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    assert len(res.best_solution.voicings) == 6
    # Final chord must resolve to tonic
    assert res.best_solution.chords[-1].function in ("T", "t")


def test_descending_diatonic_4_notes():
    """
    REPORT §1.2: C5-B4-A4-G4 [72,71,69,67] in C-dur.
    B4 descends into A4, requiring III or VII6 which are missing in ALL_FUNCTIONS (task T16).
    """
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(
        melody=[72, 71, 69, 67],
        key=Key("C", "Major"),
        time_signature="4/4",
    )
    assert res.is_success is True, f"Harmonization failed: {res.message}"


def test_descending_scale_8_notes():
    """
    REPORT §1.3: 8-note descending scale C5-B4-A4-G4-F4-E4-D4-C4 [72,71,69,67,65,64,62,60].
    Requires III/VII6 for descending leading tone (task T16).
    """
    melody = [72, 71, 69, 67, 65, 64, 62, 60]
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(
        melody=melody,
        key=Key("C", "Major"),
        time_signature="4/4",
    )
    assert res.is_success is True, f"Harmonization failed: {res.message}"


def test_soprano_melody_c5_e4_f4_g4_c5_deterministic():
    """
    REPORT §1.3 (#54): C5-E4-F4-G4-C5 [72,64,65,67,72] in C Major.
    F4->G4 is degree 4->5 in soprano, which previously hit broken S->D check or
    bad plan ordering. Verifies successful harmonization and strict determinism.
    """
    melody = [72, 64, 65, 67, 72]
    harmonizer = Harmonizer()

    res1 = harmonizer.harmonize(melody=melody, key=Key("C", "Major"), time_signature="4/4")
    res2 = harmonizer.harmonize(melody=melody, key=Key("C", "Major"), time_signature="4/4")

    assert res1.is_success == res2.is_success
    assert res1.is_success is True, f"Harmonization failed: {res1.message}"
    assert res1.best_solution is not None and res2.best_solution is not None

    chords1 = [c.function for c in res1.best_solution.chords]
    chords2 = [c.function for c in res2.best_solution.chords]
    assert chords1 == chords2

    from src.harmony.core.types import to_satb
    voicings1 = [to_satb(v) for v in res1.best_solution.voicings]
    voicings2 = [to_satb(v) for v in res2.best_solution.voicings]
    assert voicings1 == voicings2
