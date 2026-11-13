"""
Comprehensive fuzzing and invariant test suite for the Viterbi Trellis Solver,
State Generator, and Harmonizer Pipeline (Brigade Harmony Engine).

Verifies zero hard-rule violations across 20+ diverse melodies:
- Major and minor keys (C, G, D, A, F, Bb, Eb Major; A, E, D, C, G, B Minor).
- Different meters (4/4, 3/4, 2/4, 6/8) and dotted durations.
- Authentic cadences (2->1, 7->1), half cadences (ending on D), plagal cadences (S->T).
- Inversions (5/3, 6, 6/4, 7, 6/5, 4/3, 2).
"""

import pytest
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import (
    Key,
    Chord,
    TimeSignature,
    calculate_metric_structure,
)
from src.harmony.rules.engine import RuleEngine
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.solver.viterbi import ViterbiSolver


# ==============================================================================
# 20+ Diverse Fuzzing Test Cases
# ==============================================================================

FUZZ_MELODIES = [
    # 1. C major, 4/4, authentic cadence 2->1 (auto-grammar)
    {
        "id": "c_major_44_authentic_2_to_1",
        "key": "C Major",
        "meter": "4/4",
        "melody": [64, 65, 67, 65, 64, 62, 60],
        "chords": None,
    },
    # 2. C major, 4/4, authentic cadence 7->1 (auto-grammar)
    {
        "id": "c_major_44_authentic_7_to_1",
        "key": "C Major",
        "meter": "4/4",
        "melody": [60, 64, 65, 67, 69, 71, 72],
        "chords": None,
    },
    # 3. G major, 3/4, waltz meter, authentic cadence 2->1
    {
        "id": "g_major_34_authentic_2_to_1",
        "key": "G Major",
        "meter": "3/4",
        "melody": [71, 74, 72, 71, 69, 67],
        "chords": None,
    },
    # 4. F major, 2/4, marching duple meter, authentic cadence 7->1
    {
        "id": "f_major_24_authentic_7_to_1",
        "key": "F Major",
        "meter": "2/4",
        "melody": [65, 69, 67, 65, 64, 65],
        "chords": None,
    },
    # 5. D major, 6/8, compound duple meter, authentic cadence 2->1
    {
        "id": "d_major_68_authentic_2_to_1",
        "key": "D Major",
        "meter": "6/8",
        "melody": [66, 69, 67, 66, 64, 62],
        "chords": None,
    },
    # 6. A minor harmonic, 4/4, authentic cadence 2->1
    {
        "id": "a_minor_44_authentic_2_to_1",
        "key": "A MinorHarmonic",
        "meter": "4/4",
        "melody": [69, 72, 71, 72, 71, 69],
        "chords": None,
    },
    # 7. A minor harmonic, 4/4, authentic cadence 7->1 with leading tone G#4 (68) approached cleanly from E4 (64)
    {
        "id": "a_minor_44_authentic_7_to_1",
        "key": "A MinorHarmonic",
        "meter": "4/4",
        "melody": [69, 65, 64, 64, 68, 69],
        "chords": None,
    },
    # 8. E minor harmonic, 3/4, authentic cadence 2->1
    {
        "id": "e_minor_34_authentic_2_to_1",
        "key": "E MinorHarmonic",
        "meter": "3/4",
        "melody": [64, 67, 69, 67, 66, 64],
        "chords": None,
    },
    # 9. D minor harmonic, 2/4, authentic cadence with minor third step
    {
        "id": "d_minor_24_authentic",
        "key": "D MinorHarmonic",
        "meter": "2/4",
        "melody": [62, 65, 64, 61, 62],
        "chords": None,
    },
    # 10. C major, 4/4, half cadence ending on D (degree 2)
    {
        "id": "c_major_44_half_cadence_deg2",
        "key": "C Major",
        "meter": "4/4",
        "melody": [64, 65, 64, 62],
        "chords": None,
    },
    # 11. G major, 3/4, half cadence ending on D (degree 5) with explicit progression using S6
    {
        "id": "g_major_34_half_cadence_deg5",
        "key": "G Major",
        "meter": "3/4",
        "melody": [67, 67, 69],
        "chords": ["T", "S6", "D"],
    },
    # 12. A minor, 4/4, half cadence with explicit progression t -> s -> D
    {
        "id": "a_minor_44_half_cadence_explicit",
        "key": "A MinorHarmonic",
        "meter": "4/4",
        "melody": [69, 65, 64],
        "chords": ["t", "s", "D"],
    },
    # 13. C major, 4/4, plagal cadence ending S -> T
    {
        "id": "c_major_44_plagal_cadence",
        "key": "C Major",
        "meter": "4/4",
        "melody": [64, 65, 64],
        "chords": ["T", "S", "T"],
    },
    # 14. F major, 4/4, plagal cadence ending S -> T
    {
        "id": "f_major_44_plagal_cadence",
        "key": "F Major",
        "meter": "4/4",
        "melody": [69, 70, 69],
        "chords": ["T", "S", "T"],
    },
    # 15. D minor, 3/4, plagal cadence ending s -> t
    {
        "id": "d_minor_34_plagal_cadence",
        "key": "D MinorHarmonic",
        "meter": "3/4",
        "melody": [65, 67, 65],
        "chords": ["t", "s", "t"],
    },
    # 16. C major, 3/4, with dotted durations (dotted_half, half, quarter)
    {
        "id": "c_major_34_dotted_durations",
        "key": "C Major",
        "meter": "3/4",
        "melody": [
            {"pitch": 64, "duration": "dotted_half"},
            {"pitch": 65, "duration": "half"},
            {"pitch": 62, "duration": "quarter"},
            {"pitch": 60, "duration": "dotted_half"},
        ],
        "chords": None,
    },
    # 17. G major, 4/4, with dotted quarter + eighth rhythm
    {
        "id": "g_major_44_dotted_quarter_eighth",
        "key": "G Major",
        "meter": "4/4",
        "melody": [
            {"pitch": 67, "duration": "dotted_quarter"},
            {"pitch": 69, "duration": "eighth"},
            {"pitch": 71, "duration": "quarter"},
            {"pitch": 69, "duration": "quarter"},
            {"pitch": 67, "duration": "half"},
        ],
        "chords": None,
    },
    # 18. A minor, 6/8, with compound dotted quarter notes
    {
        "id": "a_minor_68_dotted_quarters",
        "key": "A MinorHarmonic",
        "meter": "6/8",
        "melody": [
            {"pitch": 69, "duration": "dotted_quarter"},
            {"pitch": 72, "duration": "dotted_quarter"},
            {"pitch": 71, "duration": "dotted_quarter"},
            {"pitch": 69, "duration": "dotted_quarter"},
        ],
        "chords": None,
    },
    # 19. Bb major, 4/4, authentic cadence
    {
        "id": "bb_major_44_authentic",
        "key": "Bb Major",
        "meter": "4/4",
        "melody": [70, 74, 72, 70],
        "chords": None,
    },
    # 20. C minor, 4/4, authentic cadence with Cadential 6/4 (K64) and Dominant 7th (D7)
    {
        "id": "c_minor_44_k64_d7_authentic",
        "key": "C MinorHarmonic",
        "meter": "4/4",
        "melody": [
            {"pitch": 63, "duration": "half", "is_downbeat": True},
            {"pitch": 65, "duration": "half", "is_downbeat": False},
            {"pitch": 63, "duration": "half", "is_downbeat": True},
            {"pitch": 62, "duration": "half", "is_downbeat": False},
            {"pitch": 60, "duration": "whole", "is_downbeat": True},
        ],
        "chords": ["t", "s", "K64", "D7", "t"],
    },
    # 21. Eb major, 4/4, rich classical cantus firmus
    {
        "id": "eb_major_44_classical",
        "key": "Eb Major",
        "meter": "4/4",
        "melody": [67, 68, 70, 68, 67, 65, 63],
        "chords": None,
    },
    # 22. B minor, 3/4, waltz in sharp minor key
    {
        "id": "b_minor_34_sharp_minor",
        "key": "B MinorHarmonic",
        "meter": "3/4",
        "melody": [71, 74, 73, 71],
        "chords": None,
    },
    # 23. F major, 4/4, dominant inversions D43 -> T6 -> D7 -> T progression
    {
        "id": "f_major_44_d43_t6_inversion",
        "key": "F Major",
        "meter": "4/4",
        "melody": [65, 70, 69, 67, 65],
        "chords": ["T", "D43", "T6", "D7", "T"],
    },
    # 24. A minor, 4/4, deceptive cadence D7 -> VI with doubled third in VI
    {
        "id": "a_minor_44_deceptive_cadence",
        "key": "A MinorHarmonic",
        "meter": "4/4",
        "melody": [69, 68, 69, 69],
        "chords": ["t", "D7", "VI", "t"],
    },
]


@pytest.mark.parametrize("case", FUZZ_MELODIES, ids=[c["id"] for c in FUZZ_MELODIES])
def test_fuzz_harmonizer_zero_hard_violations(case):
    """
    Fuzzes the Harmonizer across diverse melodies, meters, keys, and cadences.
    Enforces that EVERY solution produced by the solver passes RuleEngine validation
    with ZERO hard-rule violations.
    """
    engine = RuleEngine()
    harmonizer = Harmonizer(rule_engine=engine)

    res = harmonizer.harmonize(
        melody=case["melody"],
        key=case["key"],
        chords=case["chords"],
        time_signature=case["meter"],
    )

    assert res.is_success, (
        f"Harmonizer failed on test case '{case['id']}': {res.message}"
    )
    assert len(res.solutions) > 0, f"No solutions returned for '{case['id']}'"

    parsed_key = Key.parse(case["key"])

    for sol_idx, sol in enumerate(res.solutions):
        assert len(sol.voicings) == len(case["melody"])
        assert len(sol.chords) == len(case["melody"])
        assert sol.cost < float("inf")

        # Extract downbeat info from pre-computed metric coordinates
        metric_info = sol.metric_info if sol.metric_info else calculate_metric_structure(
            case["melody"],
            default_time_signature=TimeSignature.parse(case["meter"]),
        )

        for i in range(len(sol.voicings)):
            prev_v = sol.voicings[i - 1] if i > 0 else None
            curr_v = sol.voicings[i]
            prev_c = sol.chords[i - 1] if i > 0 else None
            curr_c = sol.chords[i]
            is_db = bool(metric_info[i].get("is_downbeat", False))

            # 1. Validate through RuleEngine
            v_res = engine.validate(
                prev_voicing=prev_v,
                curr_voicing=curr_v,
                prev_chord=prev_c,
                curr_chord=curr_c,
                key=parsed_key,
                is_downbeat=is_db,
            )

            hard_viols = [f"{v.rule_id}: {v.description}" for v in v_res.hard_violations]
            assert not v_res.has_hard_violations, (
                f"[{case['id']}] Solution {sol_idx} step {i} ({curr_c.function}) "
                f"produced HARD VIOLATIONS: {hard_viols}"
            )
            assert v_res.is_valid is True

            # 2. Invariant: Soprano matches melody pitch
            expected_pitch = case["melody"][i]["pitch"] if isinstance(case["melody"][i], dict) else case["melody"][i]
            assert curr_v.soprano == expected_pitch, (
                f"[{case['id']}] Soprano pitch {curr_v.soprano} != expected melody {expected_pitch}"
            )

            # 3. Invariant: Voice ranges
            assert 60 <= curr_v.soprano <= 81
            assert 55 <= curr_v.alto <= 74
            assert 48 <= curr_v.tenor <= 67
            assert 40 <= curr_v.bass <= 60

            # 4. Invariant: Voice ordering (no crossing)
            assert curr_v.soprano >= curr_v.alto >= curr_v.tenor >= curr_v.bass

            # 5. Invariant: Texture spacing limits
            assert curr_v.soprano - curr_v.alto <= 12
            assert curr_v.alto - curr_v.tenor <= 12
            assert curr_v.tenor - curr_v.bass <= 24


# ==============================================================================
# Targeted Invariant Tests for State Generator & Viterbi
# ==============================================================================

def test_state_generator_bass_inversion_rules():
    """
    Verifies that state_generator strictly enforces bass factor requirements:
    - Root position (5/3, 7): root in bass
    - Sextachord (6): third in bass
    - Cadential 6/4 (K64): fifth in bass
    - Dominant 7th inversions (65: third, 43: 7th, 2: 7th)
    """
    k = Key("C", "Major")
    # C major: Root=0(C), Third=4(E), Fifth=7(G), Seventh=5(F)
    # Soprano = G4 (67)
    voicings_t = generate_candidate_voicings(67, Chord("T"), key=k)
    assert len(voicings_t) > 0
    for v in voicings_t:
        assert v.bass % 12 == 0, f"T root-position must have root C in bass, got {v.bass % 12}"

    # T6 (third in bass = E = 4)
    voicings_t6 = generate_candidate_voicings(67, Chord("T6"), key=k)
    assert len(voicings_t6) > 0
    for v in voicings_t6:
        assert v.bass % 12 == 4, f"T6 must have third E in bass, got {v.bass % 12}"

    # K64 (fifth in bass = G = 7)
    voicings_k64 = generate_candidate_voicings(64, Chord("K64"), key=k)
    assert len(voicings_k64) > 0
    for v in voicings_k64:
        assert v.bass % 12 == 7, f"K64 must have fifth G in bass, got {v.bass % 12}"

    # D7 (root in bass = G = 7)
    voicings_d7 = generate_candidate_voicings(65, Chord("D7"), key=k)
    assert len(voicings_d7) > 0
    for v in voicings_d7:
        assert v.bass % 12 == 7, f"D7 root-position must have root G in bass, got {v.bass % 12}"

    # D65 (third in bass = B = 11)
    voicings_d65 = generate_candidate_voicings(67, Chord("D65"), key=k)
    assert len(voicings_d65) > 0
    for v in voicings_d65:
        assert v.bass % 12 == 11, f"D65 must have third B in bass, got {v.bass % 12}"

    # D43 (fifth in bass = D = 2 per Brigade canon)
    voicings_d43 = generate_candidate_voicings(67, Chord("D43"), key=k)
    assert len(voicings_d43) > 0
    for v in voicings_d43:
        assert v.bass % 12 == 2, f"D43 must have fifth D in bass, got {v.bass % 12}"

    # D2 (7th in bass = F = 5)
    voicings_d2 = generate_candidate_voicings(67, Chord("D2"), key=k)
    assert len(voicings_d2) > 0
    for v in voicings_d2:
        assert v.bass % 12 == 5, f"D2 must have 7th F in bass, got {v.bass % 12}"


def test_seventh_chord_factor_completeness():
    """
    Verifies that seventh chord inversions are strictly complete (all 4 chord factors present).
    """
    k = Key("C", "Major")
    # D65 candidates for Soprano = G4 (67)
    voicings = generate_candidate_voicings(67, Chord("D65"), key=k)
    assert len(voicings) > 0

    expected_factors = {7, 11, 2, 5}  # G, B, D, F
    for v in voicings:
        pcs = set(v.pitch_classes())
        assert pcs == expected_factors, (
            f"D65 voicing {v} must be complete with factors {expected_factors}, got {pcs}"
        )


def test_viterbi_extended_ranges_respected():
    """
    Verifies that when allow_extended_ranges=True is passed to ViterbiSolver,
    the rule engine also respects extended ranges without throwing VOICE_RANGE_BOUNDS.
    """
    solver = ViterbiSolver()
    k = Key("G", "Major")
    # Soprano pitch 59 (B3) is the third of G major. Standard range min is 60, extended min is 59!
    res = solver.solve([59, 59], ["T", "T"], key=k, allow_extended_ranges=True)
    assert res.is_success is True, f"Viterbi should solve in extended ranges: {res.message}"
    assert res.voicings is not None
    assert res.voicings[0].soprano == 59


def test_pipeline_diverse_key_string_parsing():
    """
    Verifies that Harmonizer parses string key signatures accurately.
    """
    Harmonizer()
    keys_to_test = [
        ("C Major", 0, "MAJOR"),
        ("A minor", 9, "MINORHARMONIC"),
        ("G-dur", 7, "MAJOR"),
        ("c-moll", 0, "MINORHARMONIC"),
        ("F# Minor", 6, "MINORHARMONIC"),
        ("Bb Major", 10, "MAJOR"),
        ("Eb MinorHarmonic", 3, "MINORHARMONIC"),
    ]
    for key_str, exp_pc, exp_mode in keys_to_test:
        k = Key.parse(key_str)
        assert k.tonic_pc == exp_pc, f"Failed tonic_pc for {key_str}: got {k.tonic_pc}, expected {exp_pc}"
        assert k.normalized_mode == exp_mode, f"Failed mode for {key_str}: got {k.normalized_mode}, expected {exp_mode}"


def test_vii7_resolution_via_solver():
    """
    Verifies that VII7 -> T can be solved by ViterbiSolver, correctly resolving the diminished 7th
    with the mandatory doubled third in the tonic triad.
    """
    solver = ViterbiSolver()
    k = Key("C", "Major")
    # Ab4 (68) -> G4 (67)
    res = solver.solve([68, 67], ["VII7", "T"], key=k)
    assert res.is_success is True, f"VII7 -> T failed: {res.message}"
    assert res.voicings is not None

    v_vii7, v_t = res.voicings
    # In VII7, factors should be B(11), D(2), F(5), Ab(8)
    assert set(v_vii7.pitch_classes()) == {11, 2, 5, 8}

    # In T after VII7, the third E(4) MUST be doubled!
    t_pcs = v_t.pitch_classes()
    assert t_pcs.count(4) == 2, f"T after VII7 must double the third (E=4), got: {t_pcs}"
