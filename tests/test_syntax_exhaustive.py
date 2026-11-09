"""
Exhaustive test suite for Classical Macro Harmonic Syntax and Functional Sequences.
Audits every single transition between chord functions in ALL_FUNCTIONS,
verifies all classical harmony prohibitions, tests pitch compatibility,
and asserts syntax invariants across diverse melodic contours in generate_plans.
"""

import pytest
from src.harmony.core.types import Key
from src.harmony.syntax.grammar import (
    HarmonicGrammar,
    ALL_FUNCTIONS,
    DOMINANT_GROUP,
    SUBDOMINANT_GROUP,
    SECONDARY_DOMINANT_GROUP,
)


# ---------------------------------------------------------------------------
# Section 1: Exhaustive Pairwise Transition Tests (ALL 256 Transitions)
# ---------------------------------------------------------------------------

class TestExhaustivePairwiseTransitions:
    """Verifies every pair of chord transitions against classical harmony theory."""

    @pytest.fixture
    def grammar(self):
        return HarmonicGrammar(Key(tonic="C", mode="Major"))

    # 1. Classical Prohibitions: Dominant -> Subdominant (Syntactic Regression)
    @pytest.mark.parametrize("d_chord", sorted(DOMINANT_GROUP))
    @pytest.mark.parametrize("s_chord", ["S", "S6", "II", "II6"])
    def test_prohibition_dominant_to_subdominant_regression(self, grammar, d_chord, s_chord):
        """All dominant chords moving to any subdominant chord are strictly forbidden."""
        assert not grammar.is_valid_syntax_transition(d_chord, s_chord), (
            f"Regression {d_chord} -> {s_chord} should be forbidden"
        )

    # 2. Classical Prohibitions: Dominant -> K64
    @pytest.mark.parametrize("d_chord", sorted(DOMINANT_GROUP))
    def test_prohibition_dominant_to_k64(self, grammar, d_chord):
        """K64 resolves TO dominant; dominant moving into K64 is strictly forbidden."""
        assert not grammar.is_valid_syntax_transition(d_chord, "K64"), (
            f"Dominant {d_chord} -> K64 should be forbidden"
        )

    # 3. Classical Prohibitions: Dominant -> Secondary Dominant
    @pytest.mark.parametrize("d_chord", sorted(DOMINANT_GROUP))
    @pytest.mark.parametrize("dd_chord", sorted(SECONDARY_DOMINANT_GROUP))
    def test_prohibition_dominant_to_secondary_dominant(self, grammar, d_chord, dd_chord):
        """Dominant cannot regress to secondary dominant (D -> DD)."""
        assert not grammar.is_valid_syntax_transition(d_chord, dd_chord), (
            f"Regression {d_chord} -> {dd_chord} should be forbidden"
        )

    # 4. Classical Prohibitions: Dominant 7th unresolving into Dominant Triad
    @pytest.mark.parametrize("d7_inv", ["D7", "D65", "D43", "D2"])
    @pytest.mark.parametrize("d_triad", ["D", "D6"])
    def test_prohibition_d7_unresolving_into_dominant_triad(self, grammar, d7_inv, d_triad):
        """Dominant 7th chords cannot unresolve back into dominant triad."""
        assert not grammar.is_valid_syntax_transition(d7_inv, d_triad), (
            f"Un-resolution {d7_inv} -> {d_triad} should be forbidden"
        )

    # 5. Classical Prohibitions: K64 resolution restrictions
    def test_k64_resolutions_allowed(self, grammar):
        """K64 must resolve to D or D7."""
        assert grammar.is_valid_syntax_transition("K64", "D")
        assert grammar.is_valid_syntax_transition("K64", "D7")

    @pytest.mark.parametrize("illegal_target", [
        "T", "T6", "S", "S6", "II", "II6", "VI", "K64",
        "D6", "D65", "D43", "D2", "DD", "DD7",
    ])
    def test_prohibition_k64_to_non_dominant(self, grammar, illegal_target):
        """K64 cannot resolve to any chord other than D or D7."""
        assert not grammar.is_valid_syntax_transition("K64", illegal_target), (
            f"K64 -> {illegal_target} must be forbidden"
        )

    # 6. Classical Prohibitions: Secondary Dominant (DD) regressions
    @pytest.mark.parametrize("dd_chord", ["DD", "DD7"])
    @pytest.mark.parametrize("target", ["S", "S6", "II", "II6", "T", "T6", "VI"])
    def test_prohibition_dd_regressions(self, grammar, dd_chord, target):
        """Secondary dominant cannot move to subdominant, tonic, or VI."""
        assert not grammar.is_valid_syntax_transition(dd_chord, target), (
            f"Secondary dominant {dd_chord} -> {target} must be forbidden"
        )

    @pytest.mark.parametrize("dd_chord", ["DD", "DD7"])
    @pytest.mark.parametrize("valid_target", ["D", "D7", "D6", "D65", "D43", "D2", "K64", "DD", "DD7"])
    def test_allowed_dd_progressions(self, grammar, dd_chord, valid_target):
        """Secondary dominant resolves to Dominant group, K64, or secondary dominant prolongation."""
        assert grammar.is_valid_syntax_transition(dd_chord, valid_target), (
            f"Secondary dominant {dd_chord} -> {valid_target} should be allowed"
        )

    # 7. Classical Prohibitions: D43 resolution
    def test_d43_allowed_resolutions(self, grammar):
        """D43 resolves to T6 or T."""
        assert grammar.is_valid_syntax_transition("D43", "T6")
        assert grammar.is_valid_syntax_transition("D43", "T")

    @pytest.mark.parametrize("invalid_target", [
        "S", "S6", "D", "D6", "D7", "D65", "D43", "D2", "K64", "VI", "II6", "II", "DD", "DD7",
    ])
    def test_prohibition_d43_invalid_targets(self, grammar, invalid_target):
        """D43 moving to anything other than T6 or T is strictly forbidden."""
        assert not grammar.is_valid_syntax_transition("D43", invalid_target), (
            f"D43 -> {invalid_target} must be forbidden"
        )

    # 8. Classical Prohibitions: D2 resolution
    def test_d2_allowed_resolution(self, grammar):
        """D2 must resolve strictly to T6."""
        assert grammar.is_valid_syntax_transition("D2", "T6")

    @pytest.mark.parametrize("invalid_target", [
        "T", "S", "S6", "D", "D6", "D7", "D65", "D43", "D2", "K64", "VI", "II6", "II", "DD", "DD7",
    ])
    def test_prohibition_d2_invalid_targets(self, grammar, invalid_target):
        """D2 moving to anything other than T6 is strictly forbidden."""
        assert not grammar.is_valid_syntax_transition("D2", invalid_target), (
            f"D2 -> {invalid_target} must be forbidden"
        )

    # 9. Classical Prohibitions: Bass leading tone leaps (D6, D65)
    @pytest.mark.parametrize("inv", ["D6", "D65"])
    def test_prohibition_leading_tone_bass_leaps(self, grammar, inv):
        """In D6 and D65, bass has leading tone and must resolve to 1 (T), not leap to T6 or VI."""
        assert grammar.is_valid_syntax_transition(inv, "T")
        assert not grammar.is_valid_syntax_transition(inv, "T6")
        assert not grammar.is_valid_syntax_transition(inv, "VI")

    # 10. Classical Prohibitions: Root D7 to T6
    def test_prohibition_d7_to_t6(self, grammar):
        """Root position D7 cannot resolve to first inversion T6 in classical harmony."""
        assert grammar.is_valid_syntax_transition("D7", "T")
        assert grammar.is_valid_syntax_transition("D7", "VI")  # Deceptive cadence
        assert not grammar.is_valid_syntax_transition("D7", "T6")

    # 11. Comprehensive Allowed Transitions Checklist
    @pytest.mark.parametrize("prev_fn, curr_fn", [
        # Tonic departures
        ("T", "S"), ("T", "S6"), ("T", "II"), ("T", "II6"),
        ("T", "D"), ("T", "D6"), ("T", "D7"), ("T", "D65"), ("T", "D43"), ("T", "D2"),
        ("T", "VI"), ("T", "DD"), ("T", "DD7"), ("T", "T"), ("T", "T6"),
        ("T6", "S"), ("T6", "S6"), ("T6", "II"), ("T6", "II6"),
        ("T6", "D"), ("T6", "D7"), ("T6", "VI"), ("T6", "T"),
        # Subdominant progressions
        ("S", "D"), ("S", "D7"), ("S", "K64"), ("S", "T"), ("S", "S6"), ("S", "II"), ("S", "II6"), ("S", "DD"),
        ("S6", "D"), ("S6", "D7"), ("S6", "K64"), ("S6", "T"),
        ("II6", "K64"), ("II6", "D"), ("II6", "D7"), ("II6", "DD"),
        ("II", "D"), ("II", "D7"), ("II", "K64"), ("II", "DD"),
        # Dominant resolutions & prolongations
        ("D", "T"), ("D", "T6"), ("D", "VI"), ("D", "D"), ("D", "D6"), ("D", "D7"),
        ("D6", "T"), ("D6", "D"), ("D6", "D7"),
        ("D7", "T"), ("D7", "VI"),
        ("D65", "T"),
        ("D43", "T6"), ("D43", "T"),
        ("D2", "T6"),
        ("K64", "D"), ("K64", "D7"),
        # Submediant progressions
        ("VI", "S"), ("VI", "II6"), ("VI", "II"), ("VI", "D"), ("VI", "K64"),
    ])
    def test_standard_allowed_transitions(self, grammar, prev_fn, curr_fn):
        """Standard functional cycles must be recognized as valid."""
        assert grammar.is_valid_syntax_transition(prev_fn, curr_fn), (
            f"Expected {prev_fn} -> {curr_fn} to be valid syntax"
        )


# ---------------------------------------------------------------------------
# Section 2: Pitch Compatibility & Cadence Restrictions Audit
# ---------------------------------------------------------------------------

class TestPitchCompatibilityAndCadence:
    """Audits get_compatible_chords_for_pitch rules."""

    @pytest.fixture
    def grammar(self):
        return HarmonicGrammar(Key(tonic="C", mode="Major"))

    def test_pitch_matching_c_major_scale_degrees(self, grammar):
        """Each scale degree should match chords containing that pitch class."""
        # Degree 1: C (60)
        cands_1 = grammar.get_compatible_chords_for_pitch(60, is_downbeat=True)
        for fn in ("T", "T6", "S", "S6", "K64", "VI", "DD7"):
            assert fn in cands_1, f"Degree 1 should match {fn}"

        # Degree 2: D (62)
        cands_2 = grammar.get_compatible_chords_for_pitch(62, is_downbeat=True)
        for fn in ("D", "D6", "D7", "D65", "D43", "D2", "II", "II6", "DD", "DD7"):
            assert fn in cands_2, f"Degree 2 should match {fn}"

        # Degree 3: E (64)
        cands_3 = grammar.get_compatible_chords_for_pitch(64, is_downbeat=True)
        for fn in ("T", "T6", "K64", "VI"):
            assert fn in cands_3, f"Degree 3 should match {fn}"

        # Degree 4: F (65)
        cands_4 = grammar.get_compatible_chords_for_pitch(65, is_downbeat=True)
        for fn in ("S", "S6", "D7", "D65", "II", "II6"):
            assert fn in cands_4, f"Degree 4 should match {fn}"

        # Degree 5: G (67)
        cands_5 = grammar.get_compatible_chords_for_pitch(67, is_downbeat=True)
        for fn in ("T", "T6", "D", "D6", "D7", "D65", "D43", "D2", "K64"):
            assert fn in cands_5, f"Degree 5 should match {fn}"

        # Degree 6: A (69)
        cands_6 = grammar.get_compatible_chords_for_pitch(69, is_downbeat=True)
        for fn in ("S", "S6", "VI", "II", "II6", "DD", "DD7"):
            assert fn in cands_6, f"Degree 6 should match {fn}"

        # Degree 7: B (71)
        cands_7 = grammar.get_compatible_chords_for_pitch(71, is_downbeat=True)
        for fn in ("D", "D7", "D43", "D2"):
            assert fn in cands_7, f"Degree 7 should match {fn}"

    def test_inversion_doubling_leading_tone_soprano_prohibition(self, grammar):
        """In D6 and D65, leading tone (B) is in bass; doubling it in soprano is forbidden."""
        cands = grammar.get_compatible_chords_for_pitch(71, is_downbeat=True)
        assert "D6" not in cands, "D6 cannot have leading tone in soprano"
        assert "D65" not in cands, "D65 cannot have leading tone in soprano"

    def test_inversion_doubling_seventh_soprano_prohibition_in_d2(self, grammar):
        """In D2, the 7th (F) is in bass; soprano doubling the 7th is forbidden."""
        cands = grammar.get_compatible_chords_for_pitch(65, is_downbeat=True)
        assert "D2" not in cands, "D2 cannot have the 7th in soprano"

    def test_k64_downbeat_metric_restriction(self, grammar):
        """K64 is allowed on downbeat, forbidden on upbeat/weak beat."""
        cands_downbeat = grammar.get_compatible_chords_for_pitch(67, is_downbeat=True)
        cands_upbeat = grammar.get_compatible_chords_for_pitch(67, is_downbeat=False)
        assert "K64" in cands_downbeat
        assert "K64" not in cands_upbeat

    def test_final_cadence_restrictions(self, grammar):
        """
        Final cadence:
        - When melody note is in Tonic (1, 3, 5): must end on authentic cadence T.
        - When melody note is not in Tonic (e.g. 2, 7): must end on half cadence D.
        """
        # Ending on degree 1 (60): authentic cadence T
        cands_1 = grammar.get_compatible_chords_for_pitch(60, is_final_cadence=True)
        assert cands_1 == ["T"]

        # Ending on degree 3 (64): authentic cadence T
        cands_3 = grammar.get_compatible_chords_for_pitch(64, is_final_cadence=True)
        assert cands_3 == ["T"]

        # Ending on degree 5 (67): authentic cadence T
        cands_5 = grammar.get_compatible_chords_for_pitch(67, is_final_cadence=True)
        assert cands_5 == ["T"]

        # Ending on degree 2 (62): half cadence D
        cands_2 = grammar.get_compatible_chords_for_pitch(62, is_final_cadence=True)
        assert cands_2 == ["D"]

        # Ending on degree 7 (71): half cadence D
        cands_7 = grammar.get_compatible_chords_for_pitch(71, is_final_cadence=True)
        assert cands_7 == ["D"]

    def test_penultimate_cadence_restrictions(self, grammar):
        """Penultimate chord before final T cannot be K64 or D2."""
        # Next pitch is C4 (60), which resolves to final T
        cands = grammar.get_compatible_chords_for_pitch(
            pitch=67,  # G4
            is_penultimate=True,
            is_downbeat=True,
            next_pitch=60,
        )
        assert "K64" not in cands, "K64 cannot precede final T directly"
        assert "D2" not in cands, "D2 cannot precede final T directly"


# ---------------------------------------------------------------------------
# Section 3: Diverse Melodic Contours in generate_plans
# ---------------------------------------------------------------------------

class TestGeneratePlansDiverseContours:
    """Verifies plan generation on diverse melodic contours and asserts syntax invariants."""

    @pytest.fixture
    def grammar_major(self):
        return HarmonicGrammar(Key(tonic="C", mode="Major"))

    @pytest.fixture
    def grammar_minor(self):
        return HarmonicGrammar(Key(tonic="A", mode="Minor"))

    def _assert_plans_valid(self, grammar, plans, melody_len):
        assert len(plans) > 0, "generate_plans returned empty list"
        for plan_idx, plan in enumerate(plans):
            assert len(plan) == melody_len, f"Plan {plan_idx} length mismatch"
            # Invariant: NO generated plan in any beam ever violates is_valid_syntax_transition
            for i in range(len(plan) - 1):
                p_fn = plan[i].function
                c_fn = plan[i + 1].function
                assert grammar.is_valid_syntax_transition(p_fn, c_fn), (
                    f"Illegal syntax transition in plan {plan_idx} at step {i}: {p_fn} -> {c_fn}"
                )

    # 1. Melodic endings on degrees 1, 2, 3, 5, 7 in Major
    def test_melody_ending_on_degree_1(self, grammar_major):
        """Melody ending on degree 1 (E4 -> D4 -> C4) -> Authentic Cadence ending on T."""
        melody = [64, 62, 60]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        assert plans[0][-1].function in ("T", "t")

    def test_melody_ending_on_degree_2(self, grammar_major):
        """Melody ending on degree 2 (C4 -> E4 -> F4 -> G4 -> D4) -> Half Cadence ending on D."""
        melody = [60, 64, 65, 67, 62]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        assert plans[0][-1].function in ("D", "d")

    def test_melody_ending_on_degree_3(self, grammar_major):
        """Melody ending on degree 3 (C4 -> D4 -> E4) -> Authentic Cadence ending on T."""
        melody = [60, 62, 64]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        assert plans[0][-1].function in ("T", "t")

    def test_melody_ending_on_degree_5(self, grammar_major):
        """Melody ending on degree 5 (C4 -> E4 -> G4) -> Authentic Cadence ending on T."""
        melody = [60, 64, 67]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        assert plans[0][-1].function in ("T", "t")

    def test_melody_ending_on_degree_7(self, grammar_major):
        """Melody ending on degree 7 (C4 -> E4 -> F4 -> B4) -> Half Cadence ending on D."""
        melody = [60, 64, 65, 71]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        assert plans[0][-1].function in ("D", "d")

    # 2. Melodies with wide leaps
    def test_melody_with_wide_octave_and_compound_leaps(self, grammar_major):
        """Melodies with octave leap (C4 -> C5) and compound zig-zag intervals."""
        melody = [60, 72, 67, 64, 72, 67, 60]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))

    def test_melody_with_large_descending_leaps(self, grammar_major):
        """Melody with large descending leap (A4 -> C4)."""
        melody = [64, 69, 60, 62, 60]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))

    # 3. Melodies with repeated notes
    def test_melody_with_repeated_notes_sustains_harmony(self, grammar_major):
        """Repeated melody notes reward harmonic sustain without illegal regressions."""
        melody = [64, 64, 65, 65, 67, 67, 62, 60]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        # Top plan should start with T
        assert plans[0][0].function in ("T", "T6")

    def test_melody_with_plateau_repetitions(self, grammar_major):
        """Sustained 3x note plateau."""
        melody = [67, 67, 67, 65, 64, 62, 60]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))

    # 4. Melodies with chromatic passing notes
    def test_melody_with_secondary_dominant_chromatic_passing(self, grammar_major):
        """Melody with #4 (F#4, pitch 66) chromatic passing note, harmonized via DD / DD7."""
        melody = [64, 65, 66, 67, 62, 60]  # E4 -> F4 -> F#4 -> G4 -> D4 -> C4
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))
        # Assert step 2 (F#4) is DD or DD7
        top_plan = plans[0]
        assert top_plan[2].function in ("DD", "DD7")

    def test_melody_with_chromatic_passing_note_sustains_gracefully(self, grammar_major):
        """Melody with C# (pitch 61) chromatic passing note executes cleanly without syntax collapse."""
        melody = [60, 61, 62, 67, 60]
        plans = grammar_major.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_major, plans, len(melody))

    # 5. Melodies in Minor Keys
    def test_minor_key_contour_complete(self, grammar_minor):
        """A Minor melody with leading tone G#4 (68) and cadence to tonic A3 (57)."""
        melody = [
            {"pitch": 60, "is_downbeat": True},   # C4 (degree 3)
            {"pitch": 62, "is_downbeat": False},  # D4 (degree 4)
            {"pitch": 65, "is_downbeat": True},   # F4 (degree 6)
            {"pitch": 68, "is_downbeat": False},  # G#4 (degree 7, leading tone)
            {"pitch": 57, "is_downbeat": True},   # A3 (degree 1, tonic)
        ]
        plans = grammar_minor.generate_plans(melody, max_plans=5)
        self._assert_plans_valid(grammar_minor, plans, len(melody))
        assert plans[0][-1].function in ("T", "t")

    def test_fallback_cannot_bypass_syntax_rules(self, grammar_major):
        """
        Stress test: Force edge case conditions and verify NO beam or fallback
        can ever produce a prohibited transition like D -> S or K64 -> T.
        """
        difficult_contour = [67, 65, 62, 65, 62, 60]  # G -> F -> D -> F -> D -> C
        plans = grammar_major.generate_plans(difficult_contour, max_plans=10)
        self._assert_plans_valid(grammar_major, plans, len(difficult_contour))
