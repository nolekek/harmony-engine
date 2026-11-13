"""
Tests for cadence finals: authentic and half cadences.
Verifies melodies ending on degrees 1, 2, 5, 7 yield legal final chords
(D or VI for half cadence, T for authentic), and never D7, T6, or K64.
"""

from src.harmony.pipeline import Harmonizer


def test_half_cadence_degree_2_melody():
    """Melody ending on degree 2 (D4 in C Major) must harmonize and end strictly on D or VI triad."""
    mel = [62, 64, 65, 67, 69, 62]  # D E F G A D
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(mel, key="C Major")

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    final_chord = res.best_solution.chords[-1].function
    assert final_chord in ("D", "VI", "d", "vi"), f"Unexpected final chord: {final_chord}"
    assert final_chord not in ("D7", "d7", "T6", "t6", "K64", "k64", "D6", "d6", "D65", "d65")


def test_half_cadence_degree_7_melody():
    """Melody ending on degree 7 (B4 in C Major) must harmonize and end strictly on D or VI triad."""
    mel = [60, 64, 65, 67, 69, 71]  # C E F G A B
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(mel, key="C Major")

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    final_chord = res.best_solution.chords[-1].function
    assert final_chord in ("D", "VI", "d", "vi"), f"Unexpected final chord: {final_chord}"
    assert final_chord not in ("D7", "d7", "T6", "t6", "K64", "k64", "D6", "d6", "D65", "d65")


def test_cadence_degree_5_melody():
    """Melody ending on degree 5 (G4 in C Major) must harmonize and end on legal triad (T, D, VI)."""
    mel = [60, 62, 64, 65, 67]  # C D E F G
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(mel, key="C Major")

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    final_chord = res.best_solution.chords[-1].function
    assert final_chord in ("T", "D", "VI", "t", "d", "vi"), f"Unexpected final chord: {final_chord}"
    assert final_chord not in ("D7", "d7", "T6", "t6", "K64", "k64")


def test_authentic_cadence_degree_1_melody():
    """Melody ending on degree 1 (C4 in C Major) must harmonize and end on root position T."""
    mel = [64, 65, 62, 60]
    harmonizer = Harmonizer()
    res = harmonizer.harmonize(mel, key="C Major")

    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    final_chord = res.best_solution.chords[-1].function
    assert final_chord in ("T", "t"), f"Final authentic cadence must be T, got: {final_chord}"
