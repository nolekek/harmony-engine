"""
Tests for T15: Non-Chord Tones (NCT) layer and classification.
"""

from src.harmony.core.types import Key, Chord
from src.harmony.rules.non_chord_tones import classify_nct
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.pipeline import Harmonizer


class TestClassifyNCTUnit:
    """(г) Exhaustive unit tests for classify_nct."""

    def test_chord_tone_recognition(self):
        c_major = {0, 4, 7}  # C, E, G
        # Any octave of chord tones is recognized as chord_tone
        assert classify_nct(59, 60, 62, c_major) == "chord_tone"
        assert classify_nct(62, 64, 65, c_major) == "chord_tone"
        assert classify_nct(65, 67, 69, c_major) == "chord_tone"
        assert classify_nct(None, 72, None, c_major) == "chord_tone"

    def test_passing_tone_ascending_and_descending(self):
        c_major = {0, 4, 7}
        # Ascending: C4 (60) -> D4 (62) -> E4 (64)
        assert classify_nct(60, 62, 64, c_major, is_downbeat=False) == "passing"
        # Ascending semitone step: E4 (64) -> F4 (65) -> G4 (67)
        assert classify_nct(64, 65, 67, c_major, is_downbeat=False) == "passing"
        # Descending: G4 (67) -> F4 (65) -> E4 (64)
        assert classify_nct(67, 65, 64, c_major, is_downbeat=False) == "passing"
        # Descending: E4 (64) -> D4 (62) -> C4 (60)
        assert classify_nct(64, 62, 60, c_major, is_downbeat=False) == "passing"

    def test_neighbor_tone_upper_and_lower(self):
        c_major = {0, 4, 7}
        # Upper neighbor: C4 (60) -> D4 (62) -> C4 (60)
        assert classify_nct(60, 62, 60, c_major, is_downbeat=False) == "neighbor"
        # Upper neighbor: G4 (67) -> A4 (69) -> G4 (67)
        assert classify_nct(67, 69, 67, c_major, is_downbeat=False) == "neighbor"
        # Lower neighbor: E4 (64) -> D#4 (63) -> E4 (64)
        assert classify_nct(64, 63, 64, c_major, is_downbeat=False) == "neighbor"
        # Lower neighbor: C4 (60) -> B3 (59) -> C4 (60)
        assert classify_nct(60, 59, 60, c_major, is_downbeat=False) == "neighbor"

    def test_suspension_recognition(self):
        # Tone held into new chord (e.g. G major chord {7, 11, 2}) on downbeat, resolving down
        # prev = C4 (60), curr = C4 (60, 4th over G), next = B3 (59, 3rd over G)
        g_major = {7, 11, 2}
        assert classify_nct(60, 60, 59, g_major, is_downbeat=True) == "suspension"
        assert classify_nct(60, 60, 58, g_major, is_downbeat=True) == "suspension"  # down by 2 semitones
        # Suspension on weak beat is not a classical suspension
        assert classify_nct(60, 60, 59, g_major, is_downbeat=False) is None

    def test_illegal_leaps_and_boundary_conditions(self):
        c_major = {0, 4, 7}
        # Leaps into non-chord tone
        assert classify_nct(60, 66, 62, c_major) is None
        # Leaps out of non-chord tone
        assert classify_nct(60, 62, 67, c_major) is None
        # Boundary: missing predecessor or successor
        assert classify_nct(None, 62, 64, c_major) is None
        assert classify_nct(60, 62, None, c_major) is None


class TestNCTStateGeneratorAndHarmonizer:
    """Verifies NCT behavior in candidate voicing generation and full pipeline harmonization."""

    def test_state_generator_downbeat_rejection_and_weakbeat_allowance(self):
        # (в) NCT on downbeat is rejected, allowed on weak beat
        key = Key("C", "Major")
        chord = Chord("T")
        # Over T, D4 (62) is NCT. With is_downbeat=True:
        cands_downbeat = generate_candidate_voicings(
            soprano_pitch=62,
            chord=chord,
            key=key,
            prev_soprano=60,
            next_soprano=64,
            is_downbeat=True,
        )
        assert len(cands_downbeat) == 0, "NCT on downbeat must produce 0 candidate voicings"

        # With is_downbeat=False, candidate voicings must be generated
        cands_weakbeat = generate_candidate_voicings(
            soprano_pitch=62,
            chord=chord,
            key=key,
            prev_soprano=60,
            next_soprano=64,
            is_downbeat=False,
        )
        assert len(cands_weakbeat) > 0, "Passing tone on weak beat must produce candidate voicings"
        # Every generated voicing must have a complete triad in the lower 3 voices (A, T, B)
        for v in cands_weakbeat:
            lower_pcs = {v.alto % 12, v.tenor % 12, v.bass % 12}
            assert {0, 4, 7}.issubset(lower_pcs)

    def test_harmonize_nct_over_t_t_t(self):
        # (а) Harmonizer().harmonize([60,62,64], key="C Major", chords=["T","T","T"]) -> success
        harmonizer = Harmonizer()
        res = harmonizer.harmonize(
            melody=[60, 62, 64],
            key="C Major",
            chords=["T", "T", "T"],
        )
        assert res.is_success is True, f"Harmonization failed: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == 3
        assert [c.function for c in res.best_solution.chords] == ["T", "T", "T"]

    def test_harmonize_scalar_phrase(self):
        # (б) Phrase [60,62,64,65,67,65,64,62,60] (C-D-E-F-G-F-E-D-C) -> success
        melody = [60, 62, 64, 65, 67, 65, 64, 62, 60]
        harmonizer = Harmonizer()
        res = harmonizer.harmonize(
            melody=melody,
            key="C Major",
        )
        assert res.is_success is True, f"Harmonization failed: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == 9
        # Final chord must resolve to tonic
        assert res.best_solution.chords[-1].function in ("T", "t")

    def test_nct_on_explicit_downbeat_rejected(self):
        # (в) NCT on explicit downbeat (is_downbeat=True) -> not allowed
        melody = [
            {"pitch": 60, "duration": "half", "is_downbeat": False},
            {"pitch": 62, "duration": "half", "is_downbeat": True},  # Explicit downbeat NCT!
            {"pitch": 64, "duration": "half", "is_downbeat": False},
        ]
        harmonizer = Harmonizer()
        res = harmonizer.harmonize(
            melody=melody,
            key="C Major",
            chords=["T", "T", "T"],
        )
        assert res.is_success is False, "NCT on explicit downbeat must not succeed"
