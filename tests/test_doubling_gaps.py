"""Unit tests for doubling gaps (VII 5/3, passing 6/4, hyphenated chord symbol normalization)."""

import pytest
from src.harmony.core.types import Voicing, parse_chord_symbol
from src.harmony.rules.doubling import (
    check_doubling,
    check_main_triad_doubling,
    check_sextaccord_doubling,
    check_triad_completeness,
)


@pytest.fixture
def c_major():
    return "C Major"


def test_vii_triad_root_doubling_forbidden(c_major):
    # In C major: VII is B, D, F. Leading tone is B (PC 11).
    # Bad voicing doubles B: S=B3(59), A=F3(53), T=D3(50), B=B2(47)
    v_vii_bad = Voicing(soprano=59, alto=53, tenor=50, bass=47)
    viols = check_doubling(v_vii_bad, "VII", key=c_major)
    assert any(v.rule_id == "DOUBLING_VII_LEADING_TONE" and v.is_hard for v in viols)


def test_vii_triad_doubled_third_allowed(c_major):
    # In C major: VII is B, D, F. Doubling third D (PC 2) is classical canon!
    # S=D4(62), A=F3(53), T=D3(50), B=B2(47) -> B:1, D:2, F:1
    v_vii_good = Voicing(soprano=62, alto=53, tenor=50, bass=47)
    viols = check_doubling(v_vii_good, "VII", key=c_major)
    vii_leading_viols = [v for v in viols if v.rule_id == "DOUBLING_VII_LEADING_TONE"]
    assert len(vii_leading_viols) == 0


def test_vii_triad_missing_fifth_forbidden(c_major):
    # Incomplete VII 5/3 without fifth (missing F, tripled third or doubled third + root):
    # S=D4(62), A=D4(62), T=D3(50), B=B2(47) -> no F!
    v_vii_no_fifth = Voicing(soprano=62, alto=62, tenor=50, bass=47)
    viols = check_doubling(v_vii_no_fifth, "VII", key=c_major)
    # Must fail completeness / doubling
    assert any(v.rule_id in ("DOUBLING_VII_LEADING_TONE", "CHORD_FIFTH_MISSING") for v in viols)


def test_passing_t64_doubled_bass_required(c_major):
    # T64 in C major: C-E-G with G in bass.
    # Good: bass G2(43) is doubled: S=E4(64), A=G3(55), T=C4(60), B=G2(43) -> G:2, C:1, E:1
    v_t64_good = Voicing(soprano=64, alto=60, tenor=55, bass=43)
    viols = check_doubling(v_t64_good, "T64", key=c_major)
    p64_viols = [v for v in viols if v.rule_id == "DOUBLING_PASSING_64"]
    assert len(p64_viols) == 0


def test_passing_t64_doubled_third_forbidden(c_major):
    # T64 with doubled third E: S=E4(64), A=C4(60), T=E3(52), B=G2(43) -> E:2, C:1, G:1
    v_t64_bad_third = Voicing(soprano=64, alto=60, tenor=52, bass=43)
    viols = check_doubling(v_t64_bad_third, "T64", key=c_major)
    assert any(v.rule_id == "DOUBLING_PASSING_64" and v.is_hard for v in viols)


def test_passing_s64_doubled_third_forbidden(c_major):
    # S64 in C major: F-A-C with C in bass.
    # Bad: doubled third A: S=A4(69), A=F4(65), T=A3(57), B=C3(48)
    v_s64_bad_third = Voicing(soprano=69, alto=65, tenor=57, bass=48)
    viols = check_doubling(v_s64_bad_third, "S64", key=c_major)
    assert any(v.rule_id == "DOUBLING_PASSING_64" and v.is_hard for v in viols)


def test_parse_chord_symbol_hyphen_normalization():
    # Suffix '-6', '-7', '-65', '-43', '-2', '-53' normalization
    assert parse_chord_symbol("VII-6") == "VII6"
    assert parse_chord_symbol("II-6") == "II6"
    assert parse_chord_symbol("T-6") == "T6"
    assert parse_chord_symbol("S-6") == "S6"
    assert parse_chord_symbol("D-6") == "D6"
    assert parse_chord_symbol("D-7") == "D7"
    assert parse_chord_symbol("D-65") == "D65"
    assert parse_chord_symbol("D-43") == "D43"
    assert parse_chord_symbol("D-2") == "D2"
    assert parse_chord_symbol("T-53") in ("T", "T53")


def test_check_sextaccord_doubling_not_bypassed_by_hyphens(c_major):
    # VII-6 with doubled leading tone (B):
    # Bass D3(50), Tenor B3(59), Alto B4(71), Soprano F4(65).
    v_vii6_bad = Voicing(soprano=65, alto=71, tenor=59, bass=50)

    res_dash = check_sextaccord_doubling(v_vii6_bad, "VII-6", key=c_major)
    res_norm = check_sextaccord_doubling(v_vii6_bad, "VII6", key=c_major)

    assert len(res_dash) > 0, "VII-6 must NOT bypass check_sextaccord_doubling!"
    assert [v.rule_id for v in res_dash] == [v.rule_id for v in res_norm]
    assert any(v.rule_id == "DOUBLING_VII6_LEADING_TONE" for v in res_dash)
