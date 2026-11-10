"""
Tests for voice ranges, crossing, and texture spacing.
"""

import pytest
from src.harmony.rules.spacing import (
    check_voice_ranges,
    check_voice_crossing,
    check_voice_unison,
    check_texture_spacing,
    validate_spacing,
)
from src.harmony.core.types import Voicing


def test_standard_voice_ranges():
    # Valid voicing: S=64 (E4), A=60 (C4), T=52 (E3), B=48 (C3)
    valid = Voicing(64, 60, 52, 48)
    assert len(check_voice_ranges(valid)) == 0

    # Soprano out of bounds (< 60 or > 81)
    s_low = Voicing(59, 58, 52, 48)
    violations = check_voice_ranges(s_low)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 0 in v.voices for v in violations)

    s_high = Voicing(82, 70, 60, 50)
    violations = check_voice_ranges(s_high)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 0 in v.voices for v in violations)

    # Alto out of bounds (< 55 or > 74)
    a_low = Voicing(65, 54, 50, 45)
    violations = check_voice_ranges(a_low)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 1 in v.voices for v in violations)

    # Tenor out of bounds (< 48 or > 67)
    t_low = Voicing(65, 60, 47, 45)
    violations = check_voice_ranges(t_low)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 2 in v.voices for v in violations)

    # Bass out of bounds (< 40 or > 60)
    b_low = Voicing(65, 60, 53, 39)
    violations = check_voice_ranges(b_low)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 3 in v.voices for v in violations)

    b_high = Voicing(67, 64, 62, 61)
    violations = check_voice_ranges(b_high)
    assert any(v.rule_id == "VOICE_RANGE_BOUNDS" and 3 in v.voices for v in violations)


def test_extended_ranges():
    # Final cadential bass at C2 = 36
    c2_bass = Voicing(60, 60, 48, 36)
    assert len(check_voice_ranges(c2_bass, allow_extended=False)) == 1
    assert len(check_voice_ranges(c2_bass, allow_extended=True)) == 0


def test_voice_crossing():
    # Valid descending order: S >= A >= T >= B
    valid = (65, 60, 53, 45)
    assert len(check_voice_crossing(valid)) == 0

    # Unisons are prohibited (strict descending order S > A > T > B)
    unison = (60, 60, 48, 48)
    u_viol = check_voice_unison(unison)
    assert len(u_viol) >= 1
    assert any(violation.rule_id == "VOICE_UNISON" for violation in u_viol)

    # S < A
    crossing_sa = (59, 60, 52, 48)
    v = check_voice_crossing(crossing_sa)
    assert any(violation.rule_id == "VOICE_CROSSING" and violation.voices == (0, 1) for violation in v)

    # A < T
    crossing_at = (67, 50, 55, 43)
    v = check_voice_crossing(crossing_at)
    assert any(violation.rule_id == "VOICE_CROSSING" and violation.voices == (1, 2) for violation in v)

    # T < B
    crossing_tb = (67, 62, 45, 48)
    v = check_voice_crossing(crossing_tb)
    assert any(violation.rule_id == "VOICE_CROSSING" and violation.voices == (2, 3) for violation in v)


def test_texture_spacing():
    # Close spacing
    close = (64, 60, 55, 48)  # S-A = 4, A-T = 5, T-B = 7
    assert len(check_texture_spacing(close)) == 0

    # Open spacing at limit (12 semitones between upper voices, 24 between T-B)
    limit = (72, 60, 48, 24)  # S-A = 12, A-T = 12, T-B = 24
    assert len(check_texture_spacing(limit)) == 0

    # S-A gap > 12
    gap_sa = (73, 60, 55, 48)  # S-A = 13
    v = check_texture_spacing(gap_sa)
    assert any(violation.rule_id == "UPPER_VOICE_SPACING_LIMIT" and violation.voices == (0, 1) for violation in v)

    # A-T gap > 12
    gap_at = (72, 65, 52, 45)  # A-T = 13
    v = check_texture_spacing(gap_at)
    assert any(violation.rule_id == "UPPER_VOICE_SPACING_LIMIT" and violation.voices == (1, 2) for violation in v)

    # T-B gap > 24
    gap_tb = (72, 64, 55, 30)  # T-B = 25
    v = check_texture_spacing(gap_tb)
    assert any(violation.rule_id == "BASS_TENOR_SPACING_LIMIT" and violation.voices == (2, 3) for violation in v)


def test_validate_spacing_combined():
    # Completely clean voicing
    clean = Voicing(64, 60, 52, 48)
    assert len(validate_spacing(clean)) == 0

    # Combined defect: crossing and upper spacing
    defect = (50, 65, 52, 40)
    v = validate_spacing(defect)
    rule_ids = {violation.rule_id for violation in v}
    assert "VOICE_RANGE_BOUNDS" in rule_ids
    assert "VOICE_CROSSING" in rule_ids
