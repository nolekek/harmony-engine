"""
Regression fixture (G3): external reviewer's 8-chord C Major score (4/4, half notes).

chords:   T    II6   T    T6   II6   II    D43   T
The score is a pile of textbook errors (unisons, incomplete chords, parallel
octaves/fifths, a bass contradicting the figured inversion II6, foreign
tones B4 over II and C4 over D43). Pins:

1. grade_satb_solution rejects it ("2") and the emitted rule-id set includes
   the six expected hard gates (four pre-existing + the two new G1/G2 gates).
2. Harmonizer strict pass on the same melody succeeds and its best solution,
   re-validated through RuleEngine pair by pair, is clean of the vertical
   hard gates (VOICE_UNISON / CHORD_THIRD_MISSING / CHORD_FIFTH_MISSING /
   BASS_INVERSION_MISMATCH / FOREIGN_TONE).
"""

from src.harmony.core.types import Chord, Voicing
from src.harmony.pipeline import Harmonizer
from src.harmony.rules.engine import RuleEngine
from backend.grader import grade_satb_solution

EXTERNAL_CHORDS = ["T", "II6", "T", "T6", "II6", "II", "D43", "T"]

EXTERNAL_VOICINGS = [
    (60, 55, 55, 48),
    (62, 57, 57, 38),
    (64, 60, 60, 48),
    (67, 60, 60, 52),
    (69, 65, 62, 53),
    (71, 69, 62, 50),
    (74, 71, 60, 50),
    (76, 72, 60, 48),
]

MELODY = [60, 62, 64, 67, 69, 71, 74, 76]

EXPECTED_HARD_IDS = {
    "VOICE_UNISON",
    "CHORD_THIRD_MISSING",
    "PARALLEL_OCTAVES",
    "PARALLEL_FIFTHS",
    "BASS_INVERSION_MISMATCH",
    "FOREIGN_TONE",
}

FORBIDDEN_IN_SOLVER_OUTPUT = {
    "VOICE_UNISON",
    "CHORD_THIRD_MISSING",
    "CHORD_FIFTH_MISSING",
    "BASS_INVERSION_MISMATCH",
    "FOREIGN_TONE",
}


def test_external_score_rejected_with_expected_hard_rule_ids():
    report = grade_satb_solution(
        voicings=[Voicing(*v) for v in EXTERNAL_VOICINGS],
        key="C Major",
        chords=[Chord(function=c) for c in EXTERNAL_CHORDS],
        time_signature="4/4",
        durations=["half"] * len(EXTERNAL_VOICINGS),
    )
    assert report.is_valid is False
    assert report.grade.startswith("2"), f"expected a failing grade, got {report.grade}"
    found_ids = {v["rule_id"] for v in report.violations}
    missing = EXPECTED_HARD_IDS - found_ids
    assert not missing, f"expected hard rule ids missing from report: {sorted(missing)}"


def test_harmonizer_strict_solution_is_clean_of_vertical_gates():
    result = Harmonizer().harmonize(MELODY, key="C Major")
    assert result.is_success is True, f"strict harmonization failed: {result.message}"
    best = result.best_solution
    assert best is not None

    engine = RuleEngine()
    found_ids: set = set()
    n = len(best.voicings)
    for i in range(n):
        prev_v = best.voicings[i - 1] if i > 0 else None
        prev_c = best.chords[i - 1] if i > 0 else None
        next_v = best.voicings[i + 1] if i + 1 < n else None
        res = engine.validate(
            prev_voicing=prev_v,
            curr_voicing=best.voicings[i],
            prev_chord=prev_c,
            curr_chord=best.chords[i],
            key="C Major",
            is_final_chord=(i == n - 1),
            next_voicing=next_v,
        )
        found_ids.update(v.rule_id for v in res.violations)

    overlap = FORBIDDEN_IN_SOLVER_OUTPUT & found_ids
    assert not overlap, f"strict solver output violates vertical gates: {sorted(overlap)}"
