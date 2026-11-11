"""
Exhaustive test suite for Brigade Harmony rules and RuleEngine.
Verifies all hard gates (parallelisms, crossings, doublings, resolutions, syntax)
and tests against human-solved benchmark tasks from the Brigade textbook.
"""

import pytest
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.rules.engine import RuleEngine
from tests.corpus.benchmark_tasks import BENCHMARK_TASKS


@pytest.fixture
def engine():
    return RuleEngine()


class TestSpacingRules:
    """Verifies vertical texture and range constraints."""

    def test_voice_range_bounds(self, engine):
        # Bass out of bounds (35 < 40)
        v_bad = Voicing(soprano=64, alto=60, tenor=52, bass=35)
        res = engine.validate_voicing(v_bad)
        assert not res.is_valid
        assert any(v.rule_id == "VOICE_RANGE_BOUNDS" for v in res.hard_violations)

        # Valid voicing within bounds
        v_good = Voicing(soprano=64, alto=60, tenor=52, bass=48)
        res_good = engine.validate_voicing(v_good)
        assert not any(v.rule_id == "VOICE_RANGE_BOUNDS" for v in res_good.hard_violations)

    def test_voice_crossing(self, engine):
        # Bass (55) higher than Tenor (52)
        v_crossed = Voicing(soprano=64, alto=60, tenor=52, bass=55)
        res = engine.validate_voicing(v_crossed)
        assert not res.is_valid
        assert any(v.rule_id == "VOICE_CROSSING" for v in res.hard_violations)

    def test_texture_spacing_upper_limit(self, engine):
        # S (76) - A (60) = 16 > 12 semitones (gap > octave between upper voices)
        v_gap = Voicing(soprano=76, alto=60, tenor=52, bass=48)
        res = engine.validate_voicing(v_gap)
        assert not res.is_valid
        assert any(v.rule_id == "UPPER_VOICE_SPACING_LIMIT" for v in res.hard_violations)

    def test_texture_spacing_bass_tenor_limit(self, engine):
        # T (67) - B (40) = 27 > 24 semitones
        v_gap = Voicing(soprano=72, alto=67, tenor=67, bass=40)
        res = engine.validate_voicing(v_gap)
        assert not res.is_valid
        assert any(v.rule_id == "BASS_TENOR_SPACING_LIMIT" for v in res.hard_violations)


class TestVoiceLeadingRules:
    """Verifies horizontal motion rules (5ths, 8ves, hidden intervals, leaps)."""

    def test_parallel_fifths(self, engine):
        # S and B move up together by 2 semitones:
        # Prev: S 67, B 48 (int 19 % 12 == 7)
        # Curr: S 69, B 50 (int 19 % 12 == 7)
        v1 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
        v2 = Voicing(soprano=69, alto=60, tenor=57, bass=50)
        res = engine.validate(v1, v2)
        assert not res.is_valid
        assert any(v.rule_id == "PARALLEL_FIFTHS" for v in res.hard_violations)

    def test_parallel_octaves(self, engine):
        # S and B move up together into octave:
        # Prev: S 67, B 43 (int 24 % 12 == 0)
        # Curr: S 69, B 45 (int 24 % 12 == 0)
        v1 = Voicing(soprano=67, alto=62, tenor=55, bass=43)
        v2 = Voicing(soprano=69, alto=64, tenor=57, bass=45)
        res = engine.validate(v1, v2)
        assert not res.is_valid
        assert any(v.rule_id == "PARALLEL_OCTAVES" for v in res.hard_violations)

    def test_contrary_octaves(self, engine):
        # S moves down (67 -> 65), B moves up (43 -> 45) landing on 65 - 45 = 20...
        # S 64, B 52 (int 12) -> S 67 (+3), B 43 (-9) -> int 24
        v1 = Voicing(soprano=64, alto=60, tenor=55, bass=52)
        v2 = Voicing(soprano=67, alto=60, tenor=55, bass=43)
        res = engine.validate(v1, v2)
        assert not res.is_valid
        assert any(v.rule_id == "CONTRARY_OCTAVES" for v in res.hard_violations)

    def test_hidden_fifths_and_octaves(self, engine):
        # Outer voices move in same direction: S leaps up by 5 semitones (64 -> 69),
        # B moves up by 2 semitones (43 -> 45), landing on 69 - 45 = 24 (pure octave)
        v1 = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        v2 = Voicing(soprano=69, alto=60, tenor=57, bass=45)
        res = engine.validate(v1, v2)
        assert not res.is_valid
        assert any(v.rule_id == "HIDDEN_FIFTHS_OCTAVES" for v in res.hard_violations)

    def test_parallel_dim5_to_p5(self, engine):
        # Tenor F3(53), Bass B2(47) (dim 5th) -> Tenor G3(55), Bass C3(48) (P5) in similar motion
        v1 = Voicing(soprano=72, alto=60, tenor=53, bass=47)
        v2 = Voicing(soprano=72, alto=60, tenor=55, bass=48)
        res = engine.validate(v1, v2)
        assert not res.is_valid
        assert any(v.rule_id == "PARALLEL_DIM5_P5" for v in res.hard_violations)

    def test_voice_overlapping(self, engine):
        # Alto in v2 (65) rises above Soprano in v1 (64)
        v1 = Voicing(soprano=64, alto=60, tenor=52, bass=48)
        v2 = Voicing(soprano=67, alto=65, tenor=55, bass=48)
        res = engine.validate(v1, v2)
        assert not res.is_valid
        assert any(v.rule_id == "VOICE_OVERLAPPING" for v in res.hard_violations)

    def test_forbidden_melodic_intervals(self, engine):
        # Alto leaps on augmented second (+3 semitones between F and G# in a-moll)
        key_a_minor = Key(tonic="A", mode="MinorHarmonic")
        v1 = Voicing(soprano=69, alto=65, tenor=57, bass=45)  # Alto F4 (65)
        v2 = Voicing(soprano=69, alto=68, tenor=56, bass=40)  # Alto G#4 (68) -> leap +3 on aug2!
        res = engine.validate(v1, v2, key=key_a_minor)
        assert not res.is_valid
        assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in res.hard_violations)


class TestDoublingRules:
    """Verifies chord doubling rules according to Brigade textbook."""

    def test_main_triad_root_doubling(self, engine):
        key = Key(tonic="C", mode="Major")
        chord_t = Chord(function="T")

        # Doubling root C: S=64(E), A=60(C), T=52(E), B=48(C) -> doubled E (third!)
        v_double_third = Voicing(soprano=64, alto=60, tenor=52, bass=48)
        # Here pitches are: E4(4), C4(0), E3(4), C3(0). Root C is doubled, but Third E is also doubled!
        # In a triad with 4 voices, either root is doubled (C C E G) or third or fifth.
        # Let's create a triad with NO G (fifth) and doubled third E: C E E E or C C E E.
        v_third_doubled = Voicing(soprano=64, alto=64, tenor=60, bass=48)  # E4, E4, C4, C3 (no G, doubled E)
        res = engine.validate_voicing(v_third_doubled, chord=chord_t, key=key)
        assert not res.is_valid
        assert any(v.rule_id == "DOUBLING_MAIN_TRIAD_ROOT" for v in res.hard_violations)

    def test_k64_bass_doubling(self, engine):
        key = Key(tonic="C", mode="Major")
        chord_k64 = Chord(function="K64")
        # In C-dur, K64 has tones C, E, G. Bass is G (V degree). Bass G MUST be doubled!
        # If bass G is NOT doubled (e.g. G, C, C, E):
        v_bad_k64 = Voicing(soprano=64, alto=60, tenor=48, bass=43)  # E4, C4, C3, G2 (root C doubled, not G!)
        res = engine.validate_voicing(v_bad_k64, chord=chord_k64, key=key)
        assert not res.is_valid
        assert any(v.rule_id == "DOUBLING_K64_BASS_ONLY" for v in res.hard_violations)

        # Correct K64: Bass G is doubled: G2 (43), G3 (55), C4 (60), E4 (64)
        v_good_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        res_good = engine.validate_voicing(v_good_k64, chord=chord_k64, key=key)
        assert not any(v.rule_id == "DOUBLING_K64_BASS_ONLY" for v in res_good.hard_violations)

    def test_deceptive_cadence_vi_doubling(self, engine):
        key = Key(tonic="A", mode="MinorHarmonic")
        prev_chord = Chord(function="D7")
        curr_chord = Chord(function="VI")
        # VI in a-moll is F-dur (F, A, C). In D -> VI, third A MUST be doubled!
        # If root F is doubled instead:
        v_prev = Voicing(soprano=68, alto=62, tenor=56, bass=40)  # D7 (G#, D, G#, E)
        v_bad_vi = Voicing(soprano=65, alto=60, tenor=53, bass=41)  # F4, C4, F3, F2 (tripled root F, third A missing!)
        res = engine.validate(v_prev, v_bad_vi, prev_chord=prev_chord, curr_chord=curr_chord, key=key)
        assert not res.is_valid
        assert any(v.rule_id == "DOUBLING_DECEPTIVE_VI_THIRD" for v in res.hard_violations)


class TestResolutionRules:
    """Verifies seventh and tendency tone resolutions."""

    def test_seventh_resolution_down(self, engine):
        key = Key(tonic="C", mode="Major")
        chord_d7 = Chord(function="D7")
        chord_t = Chord(function="T")
        # In D7 (G, B, D, F), the 7th is F. It MUST resolve down by step into E.
        # If F moves UP to G:
        v_d7 = Voicing(soprano=65, alto=59, tenor=55, bass=43)   # S=F4 (7th), A=B3, T=G3, B=G2
        v_bad_res = Voicing(soprano=67, alto=60, tenor=52, bass=48)  # S went F4 -> G4 (+2 UP!)
        res = engine.validate(v_d7, v_bad_res, prev_chord=chord_d7, curr_chord=chord_t, key=key)
        assert not res.is_valid
        assert any(v.rule_id == "RESOLUTION_SEVENTH_DOWN" for v in res.hard_violations)

    def test_d43_resolutions(self, engine):
        key = Key(tonic="F", mode="Major")
        chord_d43 = Chord(function="D43")
        chord_t = Chord(function="T")
        chord_t6 = Chord(function="T6")
        chord_ii = Chord(function="II")
        chord_d2 = Chord(function="D2")

        # In F major: C7 has root C, third E, fifth G, seventh Bb.
        # D43 has fifth G in bass (scale degree II): G2 = 43.
        # Seventh Bb is in soprano: Bb4 = 70.
        v_d43 = Voicing(soprano=70, alto=60, tenor=52, bass=43)

        # Case 1: D43 resolving to II is forbidden
        v_ii = Voicing(soprano=69, alto=62, tenor=53, bass=50)
        res1 = engine.validate(v_d43, v_ii, prev_chord=chord_d43, curr_chord=chord_ii, key=key)
        assert not res1.is_valid
        assert any(v.rule_id == "RESOLUTION_D43_TO_T6" for v in res1.hard_violations)

        # Case 2: D43 -> T (5/3) is valid (bass steps down G2(43) -> F2(41), 7th Bb4(70) -> A4(69))
        v_t53 = Voicing(soprano=69, alto=60, tenor=53, bass=41)
        res2 = engine.validate(v_d43, v_t53, prev_chord=chord_d43, curr_chord=chord_t, key=key)
        assert res2.is_valid, f"D43 -> T53 must be valid, got: {[v.rule_id for v in res2.hard_violations]}"

        # Case 3: D43 -> T6 is valid (bass steps up G2(43) -> A2(45), 7th Bb4(70) -> A4(69))
        v_t6 = Voicing(soprano=69, alto=60, tenor=53, bass=45)
        res3 = engine.validate(v_d43, v_t6, prev_chord=chord_d43, curr_chord=chord_t6, key=key)
        assert res3.is_valid, f"D43 -> T6 must be valid, got: {[v.rule_id for v in res3.hard_violations]}"

        # Case 4: D2 -> T (5/3) is a violation (D2 must resolve strictly to T6)
        v_d2 = Voicing(soprano=67, alto=60, tenor=52, bass=46)  # Bb2 (7th) in bass
        res4 = engine.validate(v_d2, v_t53, prev_chord=chord_d2, curr_chord=chord_t, key=key)
        assert not res4.is_valid
        assert any(v.rule_id == "RESOLUTION_D2_TO_T6" for v in res4.hard_violations)


class TestSyntaxRules:
    """Verifies macro harmonic progression constraints."""

    def test_k64_metric_placement(self, engine):
        chord_k64 = Chord(function="K64")
        v = Voicing(soprano=71, alto=64, tenor=55, bass=50)

        # On weak beat -> violation
        res_weak = engine.validate(None, v, curr_chord=chord_k64, is_downbeat=False)
        assert not res_weak.is_valid
        assert any(v.rule_id == "CADENCE_K64_STRONG_BEAT" for v in res_weak.hard_violations)

        # On downbeat -> valid
        res_strong = engine.validate(None, v, curr_chord=chord_k64, is_downbeat=True)
        assert not any(v.rule_id == "CADENCE_K64_STRONG_BEAT" for v in res_strong.hard_violations)

    def test_functional_regression_d_to_s(self, engine):
        chord_d = Chord(function="D")
        chord_s = Chord(function="S")
        v1 = Voicing(soprano=62, alto=59, tenor=50, bass=43)
        v2 = Voicing(soprano=65, alto=60, tenor=53, bass=41)
        res = engine.validate(v1, v2, prev_chord=chord_d, curr_chord=chord_s)
        assert not res.is_valid
        assert any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in res.hard_violations)

    def test_functional_regression_d_to_s_phrase_boundary(self, engine):
        chord_d = Chord(function="D")
        chord_s = Chord(function="S")
        v1 = Voicing(soprano=62, alto=59, tenor=50, bass=43)
        v2 = Voicing(soprano=65, alto=60, tenor=53, bass=41)
        res = engine.validate(v1, v2, prev_chord=chord_d, curr_chord=chord_s, phrase_boundary=True)
        assert not any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in res.hard_violations)

    def test_rule_catalog_description_lookup(self, engine):
        assert engine.get_rule_description("VOICE_UNISON") is not None
        assert engine.get_rule_description("PARALLEL_FIFTHS") is not None

    def test_functional_regression_d_to_k64(self, engine):
        chord_d = Chord(function="D")
        chord_k64 = Chord(function="K64")
        v_d = Voicing(soprano=62, alto=59, tenor=50, bass=43)
        v_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        res = engine.validate(v_d, v_k64, prev_chord=chord_d, curr_chord=chord_k64, is_downbeat=True)
        assert not res.is_valid
        assert any(v.rule_id == "SYNTAX_NO_D_TO_K64" for v in res.hard_violations)

    def test_k64_must_resolve_to_dominant(self, engine):
        chord_k64 = Chord(function="K64")
        chord_t = Chord(function="T")
        chord_d = Chord(function="D")
        v_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        v_t = Voicing(soprano=64, alto=60, tenor=52, bass=48)
        v_d = Voicing(soprano=62, alto=59, tenor=55, bass=43)

        # K64 -> T is strictly invalid in classical cadence
        res_bad = engine.validate(v_k64, v_t, prev_chord=chord_k64, curr_chord=chord_t)
        assert not res_bad.is_valid
        assert any(v.rule_id == "SYNTAX_K64_MUST_RESOLVE_TO_D" for v in res_bad.hard_violations)

        # K64 -> D is valid
        res_good = engine.validate(v_k64, v_d, prev_chord=chord_k64, curr_chord=chord_d)
        assert not any(v.rule_id == "SYNTAX_K64_MUST_RESOLVE_TO_D" for v in res_good.hard_violations)


class TestHumanBenchmarkCorpus:
    """
    Verifies that all human reference solutions from the Brigade textbook
    pass the RuleEngine without any hard-gate violations.
    """

    @pytest.mark.parametrize("task", BENCHMARK_TASKS, ids=[t["id"] for t in BENCHMARK_TASKS])
    def test_benchmark_task_validity(self, engine, task):
        key = Key(tonic=task["key"]["tonic"], mode=task["key"]["mode"])
        satb_list = task["ground_truth_satb"]
        functions = task["ground_truth_functions"]
        melody = task["melody"]

        prev_v = None
        prev_chord = None

        for idx, (satb, func, mel) in enumerate(zip(satb_list, functions, melody)):
            curr_v = Voicing(*satb)
            curr_chord = Chord(function=func)
            is_downbeat = mel.get("is_downbeat", False)

            res = engine.validate(
                prev_voicing=prev_v,
                curr_voicing=curr_v,
                prev_chord=prev_chord,
                curr_chord=curr_chord,
                key=key,
                is_downbeat=is_downbeat,
                is_final_chord=(idx == len(satb_list) - 1),
            )

            # Human solution must NEVER have hard violations!
            hard_errors = [f"{v.rule_id}: {v.description}" for v in res.hard_violations]
            assert not res.has_hard_violations, (
                f"Task '{task['id']}' failed at chord {idx} ({func}): {hard_errors}"
            )
            assert res.cost < float("inf")

            prev_v = curr_v
            prev_chord = curr_chord
