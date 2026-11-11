"""
Unit and integration tests for bounded replanning in the harmonization pipeline.
Addresses REPORT §4.2, §4.7; DEF-01: macro-grammar + micro-infeasibility recovery.
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key


@pytest.fixture
def harmonizer():
    return Harmonizer()


class TestReplanning:
    """Verifies that bounded replanning rescues melodies blocked by micro-infeasibility."""

    def test_replanning_aminor_scale_descending_succeeds(self, harmonizer):
        """(a) Melodies previously rejected now succeed under replanning."""
        m_down = [81, 80, 77, 76, 74, 72, 71, 69]
        key = Key("A", "MinorHarmonic")
        res = harmonizer.harmonize(m_down, key, allow_replanning=True)
        assert res.is_success, f"Expected success with replanning, got: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == 8
        assert len(res.best_solution.chords) == 8

    def test_replanning_aminor_scale_ascending_succeeds(self, harmonizer):
        """(a) Melodies previously rejected now succeed under replanning."""
        m_up = [69, 71, 72, 74, 76, 77, 80, 81]
        key = Key("A", "MinorHarmonic")
        res = harmonizer.harmonize(m_up, key, allow_replanning=True)
        assert res.is_success, f"Expected success with replanning, got: {res.message}"
        assert res.best_solution is not None
        assert len(res.best_solution.voicings) == 8
        assert len(res.best_solution.chords) == 8

    def test_replanning_determinism(self, harmonizer):
        """(b) Two identical runs produce byte-for-byte identical solutions (no unsorted sets)."""
        m_down = [81, 80, 77, 76, 74, 72, 71, 69]
        key = Key("A", "MinorHarmonic")

        res1 = harmonizer.harmonize(m_down, key, allow_replanning=True)
        res2 = harmonizer.harmonize(m_down, key, allow_replanning=True)

        assert res1.is_success == res2.is_success
        assert len(res1.solutions) == len(res2.solutions)
        assert res1.best_solution is not None and res2.best_solution is not None

        chords1 = [c.function for c in res1.best_solution.chords]
        chords2 = [c.function for c in res2.best_solution.chords]
        assert chords1 == chords2

        assert res1.best_solution.cost == res2.best_solution.cost

        v1 = [(v.soprano, v.alto, v.tenor, v.bass) for v in res1.best_solution.voicings]
        v2 = [(v.soprano, v.alto, v.tenor, v.bass) for v in res2.best_solution.voicings]
        assert v1 == v2

    def test_replanning_disabled_preserves_rejection(self, harmonizer):
        """(c) When allow_replanning=False, behavior is the former rejection (feature is explicit)."""
        m_down = [81, 80, 77, 76, 74, 72, 71, 69]
        key = Key("A", "MinorHarmonic")
        res_down = harmonizer.harmonize(m_down, key, allow_replanning=False)
        assert not res_down.is_success
        assert "rejected by hard voice-leading constraints" in res_down.message

        m_up = [69, 71, 72, 74, 76, 77, 80, 81]
        res_up = harmonizer.harmonize(m_up, key, allow_replanning=False)
        assert not res_up.is_success
        assert "rejected by hard voice-leading constraints" in res_up.message

    def test_replanning_rescues_stress_test_corner_cases(self, harmonizer):
        """Verifies replanning repairs dead-end progressions (e.g. C minor and G minor L1 melodies)."""
        # C minor L1 melody where initial grammar plans hit dead ends at steps 2-4
        mel_c = [63, 65, 67, 65, 62, 60]
        key_c = Key("C", "MinorHarmonic")
        res_c = harmonizer.harmonize(mel_c, key_c, allow_replanning=True)
        assert res_c.is_success
        assert res_c.best_solution is not None
        assert len(res_c.best_solution.voicings) == len(mel_c)

        # G minor L1 melody where initial grammar chose penultimate VII6 blocking final cadence
        mel_g = [62, 66, 67, 67, 66, 67]
        key_g = Key("G", "MinorHarmonic")
        res_g = harmonizer.harmonize(mel_g, key_g, allow_replanning=True)
        assert res_g.is_success
        assert res_g.best_solution is not None
        assert len(res_g.best_solution.voicings) == len(mel_g)
