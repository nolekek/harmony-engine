"""
Tests for harmonic rhythm quality, chord oscillation prevention,
mediant suppression in major keys, and cadence preparation.
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import TimeSignature, calculate_metric_structure


@pytest.fixture(scope="module")
def harmonizer():
    return Harmonizer()


TEN_DIATONIC_MELODIES = [
    {"name": "C_maj_scale_8", "key": "C Major", "ts": "4/4", "melody": [60, 62, 64, 65, 67, 69, 71, 72]},
    {"name": "C_maj_arch_15", "key": "C Major", "ts": "4/4", "melody": [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60]},
    {"name": "C_maj_chorale_8", "key": "C Major", "ts": "4/4", "melody": [67, 67, 69, 67, 65, 64, 62, 60]},
    {"name": "C_maj_waltz_6", "key": "C Major", "ts": "3/4", "melody": [64, 67, 65, 64, 62, 60]},
    {"name": "G_maj_scale_8", "key": "G Major", "ts": "4/4", "melody": [67, 69, 71, 72, 74, 76, 78, 79]},
    {"name": "G_maj_arch_13", "key": "G Major", "ts": "4/4", "melody": [67, 69, 71, 72, 74, 76, 74, 72, 71, 69, 71, 69, 67]},
    {"name": "G_maj_waltz_6", "key": "G Major", "ts": "3/4", "melody": [67, 71, 74, 72, 69, 67]},
    {"name": "F_maj_scale_8", "key": "F Major", "ts": "4/4", "melody": [65, 67, 69, 70, 72, 74, 76, 77]},
    {"name": "D_min_scale_8", "key": "D Minor", "ts": "4/4", "melody": [62, 64, 65, 67, 69, 70, 73, 74]},
    {"name": "E_min_scale_8", "key": "E Minor", "ts": "4/4", "melody": [64, 66, 67, 69, 71, 72, 75, 76]},
]


def test_harmonic_rhythm_rate_of_fast_chord_changes(harmonizer):
    """
    (1) Для 10 диатонических мелодий доля тактов с >2 сменами аккордов <= 10% (или == 0).
    """
    total_measures = 0
    measures_gt_2_changes = 0

    for item in TEN_DIATONIC_MELODIES:
        res = harmonizer.harmonize(item["melody"], key=item["key"], time_signature=item["ts"])
        assert res.is_success, f"Harmonization failed for {item['name']}: {res.message}"
        assert res.best_solution is not None

        sol = res.best_solution
        chords = [c.function for c in sol.chords]
        metric_info = sol.metric_info or calculate_metric_structure(
            item["melody"], default_time_signature=TimeSignature.parse(item["ts"])
        )

        measures_map: dict[int, list[str]] = {}
        for m_info, ch in zip(metric_info, chords):
            measures_map.setdefault(m_info["measure"], []).append(ch)

        for m_num, m_chords in measures_map.items():
            total_measures += 1
            changes = sum(1 for j in range(1, len(m_chords)) if m_chords[j] != m_chords[j - 1])
            if changes > 2:
                measures_gt_2_changes += 1

    rate = (measures_gt_2_changes / total_measures) if total_measures > 0 else 0.0
    assert rate <= 0.10, (
        f"Rate of measures with >2 chord changes is {rate:.1%} ({measures_gt_2_changes}/{total_measures}), "
        "must be <= 10%."
    )


def test_no_iii_in_major_motifs_and_no_consecutive_iii(harmonizer):
    """
    (2) Нет последовательности III, III6 и нет III в мажорных 6-нотных мотивах.
    """
    # 2a. Hard syntax grammar invariant: consecutive mediants forbidden
    g = harmonizer.grammar
    assert not g.is_valid_syntax_transition("III", "III6")
    assert not g.is_valid_syntax_transition("III6", "III")
    assert not g.is_valid_syntax_transition("III", "III")
    assert not g.is_valid_syntax_transition("III6", "III6")
    assert not g.is_valid_syntax_transition("iii", "iii6")
    assert not g.is_valid_syntax_transition("iii6", "iii")

    # 2b. 6-note major motifs must not contain III or III6
    major_6_motifs = [
        {"name": "C_maj_motif_6", "key": "C Major", "melody": [64, 67, 65, 64, 62, 60]},
        {"name": "C_maj_short_6", "key": "C Major", "melody": [60, 64, 67, 65, 62, 60]},
        {"name": "G_maj_motif_6", "key": "G Major", "melody": [67, 71, 74, 72, 69, 67]},
        {"name": "G_maj_short_6", "key": "G Major", "melody": [71, 72, 74, 71, 69, 67]},
        {"name": "F_maj_motif_6", "key": "F Major", "melody": [69, 70, 72, 67, 65, 65]},
        {"name": "F_maj_short_6", "key": "F Major", "melody": [65, 69, 72, 70, 67, 65]},
    ]

    for item in major_6_motifs:
        res = harmonizer.harmonize(item["melody"], key=item["key"])
        assert res.is_success, f"Failed for {item['name']}: {res.message}"
        chords = [c.function for c in res.best_solution.chords]
        for ch in chords:
            assert ch not in ("III", "III6", "iii", "iii6"), (
                f"{item['name']}: found forbidden mediant chord '{ch}' in major 6-note motif: {chords}"
            )

    # 2c. Long C-major arch must not use III in Major
    c_arch = [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60]
    res_arch = harmonizer.harmonize(c_arch, key="C Major")
    assert res_arch.is_success
    chords_arch = [c.function for c in res_arch.best_solution.chords]
    for ch in chords_arch:
        assert ch not in ("III", "III6"), (
            f"Found forbidden mediant '{ch}' in C Major arch: {chords_arch}"
        )


def test_no_t_s6_t_s6_oscillation(harmonizer):
    """
    (3) Нет осцилляции T,S6,T,S6 подряд.
    """
    melodies_to_check = [
        {"name": "C_maj_scale_8", "key": "C Major", "melody": [60, 62, 64, 65, 67, 69, 71, 72]},
        {"name": "C_maj_arch_15", "key": "C Major", "melody": [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60]},
        {"name": "G_maj_scale_8", "key": "G Major", "melody": [67, 69, 71, 72, 74, 76, 78, 79]},
        {"name": "G_maj_arch_13", "key": "G Major", "melody": [67, 69, 71, 72, 74, 76, 74, 72, 71, 69, 71, 69, 67]},
        {"name": "F_maj_scale_8", "key": "F Major", "melody": [65, 67, 69, 70, 72, 74, 76, 77]},
        {"name": "F_maj_arch_11", "key": "F Major", "melody": [65, 67, 69, 70, 72, 74, 72, 70, 69, 67, 65]},
        {"name": "G_maj_phrase_10", "key": "G Major", "melody": [67, 69, 71, 72, 74, 76, 74, 72, 69, 67]},
    ]

    for item in melodies_to_check:
        res = harmonizer.harmonize(item["melody"], key=item["key"])
        assert res.is_success, f"Failed for {item['name']}: {res.message}"
        chords = [c.function for c in res.best_solution.chords]

        # Check that T, S6, T, S6 and S6, T, S6, T nowhere appear as contiguous sub-slices
        for i in range(len(chords) - 3):
            slice_4 = tuple(chords[i:i + 4])
            assert slice_4 != ("T", "S6", "T", "S6"), (
                f"{item['name']}: found forbidden oscillation T, S6, T, S6 at index {i}: {chords}"
            )
            assert slice_4 != ("S6", "T", "S6", "T"), (
                f"{item['name']}: found forbidden oscillation S6, T, S6, T at index {i}: {chords}"
            )


def test_final_cadence_stepwise_vs_repeated(harmonizer):
    """
    (4) Финал: нет T,T при ступенчатом движении последних двух нот;
        при повторной тонике в мелодии T,T допустим.
    """
    # 4a. Stepwise soprano at final two notes: [..., D4, C4] in C Major -> MUST NOT end in T, T
    stepwise_melodies = [
        {"name": "C_stepwise_5", "key": "C Major", "melody": [64, 65, 67, 62, 60]},  # 62 -> 60 (step -2)
        {"name": "C_stepwise_8", "key": "C Major", "melody": [67, 65, 64, 65, 67, 64, 62, 60]},  # 62 -> 60
        {"name": "G_stepwise_7", "key": "G Major", "melody": [67, 69, 71, 72, 71, 69, 67]},  # 69 -> 67
        {"name": "F_stepwise_5", "key": "F Major", "melody": [69, 70, 72, 67, 65]},  # 67 -> 65
    ]

    allowed_dominant_penult = {"K64", "D", "D7", "D6", "D65", "D43", "D2"}

    for item in stepwise_melodies:
        res = harmonizer.harmonize(item["melody"], key=item["key"])
        assert res.is_success, f"Failed for {item['name']}: {res.message}"
        chords = [c.function for c in res.best_solution.chords]

        # Must not end in T, T
        assert chords[-2:] != ["T", "T"], (
            f"{item['name']}: final chords {chords[-2:]} are T, T on stepwise melody motion: {chords}"
        )
        assert chords[-1] in ("T", "t"), f"{item['name']}: final chord {chords[-1]} != T"
        assert chords[-2] in allowed_dominant_penult, (
            f"{item['name']}: penultimate chord {chords[-2]} not in dominant group: {chords}"
        )

    # 4b. Repeated tonic at final two notes: [..., C4, C4] -> T, T is acceptable
    repeated_tonic_melodies = [
        {"name": "C_repeated_tonic_6", "key": "C Major", "melody": [64, 65, 67, 62, 60, 60]},  # 60 -> 60
        {"name": "F_repeated_tonic_6", "key": "F Major", "melody": [69, 70, 72, 67, 65, 65]},  # 65 -> 65
        {"name": "C_scale_16_repeated", "key": "C Major", "melody": [60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60, 60]},
    ]

    for item in repeated_tonic_melodies:
        res = harmonizer.harmonize(item["melody"], key=item["key"])
        assert res.is_success, f"Failed for {item['name']}: {res.message}"
        chords = [c.function for c in res.best_solution.chords]
        # Final chord must be T; T, T is valid when melody repeats tonic note
        assert chords[-1] in ("T", "t")
        assert chords[-2:] == ["T", "T"] or chords[-2] in allowed_dominant_penult, (
            f"{item['name']}: unexpected final cadence {chords[-2:]}"
        )
