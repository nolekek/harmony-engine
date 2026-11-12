"""
Comprehensive verification suite for final VI cadence constraints and chromatic false-relation rules.

Covers Scope P1 Revisions:
1. Repro check: pseudo-deceptive cadence T -> VI after tonic in [60,62,64,65,67,69]
   is replaced with legal cadence (III -> VI / D -> VI), never T -> VI.
2. Hard-gate CADENCE_FINAL_VI_REQUIRES_DOMINANT strictly rejects final VI preceded by T, T6, S, II.
3. Legal deceptive cadence (D -> VI, VII7 -> VI, III -> VI) is permitted at the final step.
4. Chromatic false relation (cross-voice C <-> C# and F <-> F#) triggers hard FALSE_RELATION_PERECHENIE.
5. Mode-aware false relation logic permits diatonic semitones in Neapolitan (I <-> bII)
   and harmonic submediant (V <-> bVI).
6. Grader localization: grade_satb_solution reports CADENCE_FINAL_VI_REQUIRES_DOMINANT
   with pedagogical Russian message and fails student work (grade '2 (Не зачтено)').
7. No monkey-patching: doubling module does not alter chromatic module at runtime.
8. Replanning regression: [72, 71, 69] resolves via ['T', 'III', 'VI'].
"""

import pytest

from src.harmony.pipeline import Harmonizer
from src.harmony.rules.engine import RuleEngine
from src.harmony.rules.chromatic import check_false_relation
import src.harmony.rules.doubling as doubling_mod
import src.harmony.rules.chromatic as chromatic_mod
from src.harmony.core.types import Voicing, Key, Chord
from backend.grader import grade_satb_solution


def test_repro_cadence_c_major():
    """
    (1) Melody [60,62,64,65,67,69] (C4, D4, E4, F4, G4, A4) in C Major:
    Must NOT end in T -> VI (pseudo-deceptive cadence).
    Must yield a legal harmonization ending in III -> VI (or D -> VI).
    """
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([60, 62, 64, 65, 67, 69], key="C Major")
    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None

    chords = [c.function for c in res.best_solution.chords]
    assert chords[-1] in ("VI", "vi"), f"Final chord should be VI, got: {chords}"
    assert chords[-2] not in ("T", "t", "T6", "t6", "T53", "t53"), (
        f"Final VI cannot be preceded by Tonic: {chords}"
    )
    assert chords[-2] in ("III", "iii", "D", "D7", "VII7"), (
        f"Final VI must be preceded by legal dominant/mediant, got {chords[-2]} in {chords}"
    )
    assert chords == ["T", "II6", "T", "S6", "III", "VI"], f"Unexpected chord sequence: {chords}"


def test_hard_gate_final_t_to_vi():
    """
    (2) RuleEngine hard-gate CADENCE_FINAL_VI_REQUIRES_DOMINANT:
    Final VI after T or T6 must be strictly rejected with severity 'hard_gate'.
    """
    engine = RuleEngine()
    key = Key.parse("C Major")

    v_t = Voicing(soprano=64, alto=60, tenor=55, bass=48)     # T (E-C-G-C)
    v_t6 = Voicing(soprano=64, alto=60, tenor=55, bass=52)    # T6 (E-C-G-E)
    v_vi = Voicing(soprano=69, alto=60, tenor=48, bass=45)    # VI (A-C-C-A)

    # 1. Final VI after root-position T
    res_t = engine.validate(v_t, v_vi, prev_chord=Chord("T"), curr_chord=Chord("VI"), key=key, is_final_chord=True)
    viols_t = [v for v in res_t.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols_t) >= 1, "Expected CADENCE_FINAL_VI_REQUIRES_DOMINANT for T -> VI (final)"
    assert viols_t[0].is_hard is True, "Violation must be a hard gate"
    assert viols_t[0].penalty >= 10000.0

    # 2. Final VI after T6
    res_t6 = engine.validate(v_t6, v_vi, prev_chord=Chord("T6"), curr_chord=Chord("VI"), key=key, is_final_chord=True)
    viols_t6 = [v for v in res_t6.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols_t6) >= 1, "Expected CADENCE_FINAL_VI_REQUIRES_DOMINANT for T6 -> VI (final)"
    assert viols_t6[0].is_hard is True

    # 3. Non-final VI after T should NOT trigger CADENCE_FINAL_VI_REQUIRES_DOMINANT
    res_non_final = engine.validate(v_t, v_vi, prev_chord=Chord("T"), curr_chord=Chord("VI"), key=key, is_final_chord=False)
    viols_non_final = [v for v in res_non_final.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols_non_final) == 0, "Non-final VI should not trigger cadential rule"


def test_legal_d_to_vi_and_vii7_to_vi():
    """
    (3) Final VI preceded by D, VII7, or III must NOT trigger CADENCE_FINAL_VI_REQUIRES_DOMINANT.
    """
    engine = RuleEngine()
    key = Key.parse("C Major")

    v_d = Voicing(soprano=71, alto=62, tenor=55, bass=43)       # D (B-D-G-G)
    v_vii7 = Voicing(soprano=71, alto=65, tenor=59, bass=47)    # VII7 (B-F-B-B)
    v_iii = Voicing(soprano=67, alto=59, tenor=55, bass=40)     # III (G-B-G-E)
    v_vi = Voicing(soprano=69, alto=60, tenor=48, bass=45)      # VI (A-C-C-A)

    for prev_name, v_prev in [("D", v_d), ("VII7", v_vii7), ("III", v_iii)]:
        res = engine.validate(
            v_prev,
            v_vi,
            prev_chord=Chord(prev_name),
            curr_chord=Chord("VI"),
            key=key,
            is_final_chord=True,
        )
        viols = [v for v in res.violations if v.rule_id == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
        assert len(viols) == 0, f"Unexpected cadential hard-gate for {prev_name} -> VI: {viols}"


def test_cross_voice_c_csharp_and_f_fsharp_flagged():
    """
    (4) Cross-voice chromatic semitones (C <-> C# and F <-> F#) must trigger
    hard FALSE_RELATION_PERECHENIE when not in recognized diatonic/modal context.
    """
    key = Key.parse("C Major")

    # Cross-voice C (alto 60) -> C# (tenor 61) in secondary dominant
    v1 = Voicing(soprano=64, alto=60, tenor=55, bass=48)  # Alto has C (60)
    v2 = Voicing(soprano=64, alto=57, tenor=61, bass=45)  # Tenor has C# (61)
    viols_c = check_false_relation(v1, v2, key=key, prev_chord=Chord("T"), curr_chord=Chord("A7"))
    p_c = [v for v in viols_c if v.rule_id == "FALSE_RELATION_PERECHENIE"]
    assert len(p_c) >= 1, "Cross-voice C <-> C# must trigger FALSE_RELATION_PERECHENIE"
    assert any(v.is_hard for v in p_c)

    # Cross-voice F (soprano 65) -> F# (alto 66) in DD
    v3 = Voicing(soprano=65, alto=60, tenor=53, bass=41)  # Soprano has F (65)
    v4 = Voicing(soprano=62, alto=66, tenor=57, bass=50)  # Alto has F# (66)
    viols_f = check_false_relation(v3, v4, key=key, prev_chord=Chord("S"), curr_chord=Chord("DD"))
    p_f = [v for v in viols_f if v.rule_id == "FALSE_RELATION_PERECHENIE"]
    assert len(p_f) >= 1, "Cross-voice F <-> F# must trigger FALSE_RELATION_PERECHENIE"
    assert any(v.is_hard for v in p_f)


def test_diatonic_neapolitan_and_bvi_not_flagged():
    """
    (5) Diatonic semitones in Neapolitan (I <-> bII: C <-> Db) and harmonic
    submediant (V <-> bVI: G <-> Ab) must NOT trigger FALSE_RELATION_PERECHENIE.
    """
    key = Key.parse("C Major")

    # 1. Neapolitan N6: T -> N6 where Alto has C (60) and Soprano has Db (61)
    v_t = Voicing(soprano=64, alto=60, tenor=52, bass=48)   # Alto has C
    v_n6 = Voicing(soprano=61, alto=53, tenor=53, bass=41)  # Soprano has Db (61), Bass has F
    viols_n = check_false_relation(v_t, v_n6, key=key, prev_chord=Chord("T"), curr_chord=Chord("N6"))
    p_n = [v for v in viols_n if v.rule_id == "FALSE_RELATION_PERECHENIE"]
    assert len(p_n) == 0, f"Diatonic C <-> Db in Neapolitan must not trigger false relation: {p_n}"

    # 2. Harmonic submediant bVI: D -> bVI where Alto has G (55) and Tenor has Ab (56)
    v_d = Voicing(soprano=71, alto=55, tenor=62, bass=43)    # Alto has G (55)
    v_bvi = Voicing(soprano=68, alto=60, tenor=56, bass=44)  # Tenor has Ab (56)
    viols_bvi = check_false_relation(v_d, v_bvi, key=key, prev_chord=Chord("D"), curr_chord=Chord("bVI"))
    p_bvi = [v for v in viols_bvi if v.rule_id == "FALSE_RELATION_PERECHENIE"]
    assert len(p_bvi) == 0, f"Diatonic G <-> Ab in bVI must not trigger false relation: {p_bvi}"


def test_grader_flags_t_to_vi_final():
    """
    (6) Student homework grader: grade_satb_solution reports CADENCE_FINAL_VI_REQUIRES_DOMINANT
    with pedagogical Russian critique and rejects submission.
    """
    v_t = Voicing(soprano=64, alto=60, tenor=55, bass=48)
    v_vi = Voicing(soprano=69, alto=60, tenor=48, bass=45)

    report = grade_satb_solution(
        voicings=[v_t, v_vi],
        key="C Major",
        chords=["T", "VI"],
    )

    assert report.is_valid is False, "Progression ending in T -> VI must be marked invalid"
    assert report.grade == "2 (Не зачтено)", f"Expected grade 2, got {report.grade}"

    viols = [v for v in report.violations if v["rule_id"] == "CADENCE_FINAL_VI_REQUIRES_DOMINANT"]
    assert len(viols) >= 1, "Grader report must include CADENCE_FINAL_VI_REQUIRES_DOMINANT"
    msg = viols[0]["message_ru"]
    assert "Прерванная каденция (VI) обязана следовать за доминантовой группой" in msg, (
        f"Unexpected Russian message: {msg}"
    )


def test_no_monkey_patch_in_doubling():
    """
    (7) Verify elimination of monkey-patching in doubling module.
    """
    assert not hasattr(doubling_mod, "_chromatic"), (
        "doubling.py should not import chromatic as _chromatic"
    )
    assert not hasattr(doubling_mod, "_refined_check_false_relation"), (
        "doubling.py should not define _refined_check_false_relation"
    )
    assert chromatic_mod.check_false_relation.__module__ == "src.harmony.rules.chromatic", (
        "chromatic.check_false_relation must be native to src.harmony.rules.chromatic"
    )


def test_replanning_rescues_c5_b4_a4_integration():
    """
    (8) Verify [72, 71, 69] resolves via ['T', 'III', 'VI'] without falling into T -> VI.
    """
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([72, 71, 69], key="C Major")
    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    chords = [c.function for c in res.best_solution.chords]
    assert chords == ["T", "III", "VI"], f"Expected ['T', 'III', 'VI'], got: {chords}"


def test_single_note_69_allows_final_vi():
    """
    (9) Single-note melody [69] (A4) in C Major has no predecessor (n=1).
    The cadential predecessor rule must not apply; VI is legal and success must be True.
    """
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([69], key="C Major")
    assert res.is_success is True, f"Single-note harmonization failed: {res.message}"
    assert res.best_solution is not None
    chords = [c.function for c in res.best_solution.chords]
    assert chords == ["VI"], f"Expected ['VI'], got: {chords}"


def test_two_notes_60_69_rejected_by_cadence_ban():
    """
    (10) Two-note melodies ending in A4 ([60, 69], [64, 69], [67, 69]) in C Major
    cannot legally close on VI because T -> VI, T6 -> VI, etc. are forbidden by the
    cadential hard-gate CADENCE_FINAL_VI_REQUIRES_DOMINANT. Must return success=False.
    """
    harmonizer = Harmonizer()
    for melody in ([60, 69], [64, 69], [67, 69]):
        res = harmonizer.harmonize(melody, key="C Major")
        assert res.is_success is False, (
            f"Melody {melody} should fail strict cadence requirements, but succeeded: "
            f"{[c.function for c in res.best_solution.chords] if res.best_solution else None}"
        )


def test_repro_progression_60_to_69_not_after_forbidden():
    """
    (11) Melody [60,62,64,65,67,69] in C Major succeeds and final VI is NOT
    preceded by T, T6, S, or II.
    """
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([60, 62, 64, 65, 67, 69], key="C Major")
    assert res.is_success is True, f"Harmonization failed: {res.message}"
    assert res.best_solution is not None
    chords = [c.function for c in res.best_solution.chords]
    assert chords[-1] in ("VI", "vi")
    forbidden = {"T", "t", "T6", "t6", "T53", "t53", "S", "s", "S6", "s6", "II", "ii", "II6", "ii6"}
    assert chords[-2] not in forbidden, f"Final VI preceded by forbidden chord: {chords}"
    assert chords[-2] in {"D", "d", "D7", "d7", "D6", "d6", "D65", "d65", "VII7", "vii7", "III", "iii"}

