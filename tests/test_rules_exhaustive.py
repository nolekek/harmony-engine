"""
Exhaustive adversarial and verification test suite for classical harmony rules (Brigade textbook).
Tests every voice leading, doubling, resolution, and syntax rule in `src/harmony/rules/`:
- Parallel 5ths and 8ves (both direct and contrary) across all voice pairs
- Voice crossing, voice overlapping, unisons (direct vs oblique/contrary)
- Texture spacing limits and soprano/bass range bounds
- Doubling in root-position triads (T, S, D), sextaccords (T6, S6, D6), K64, deceptive VI, DD
- Resolutions: 7th down, leading tone up, D43 -> T6, D2 -> T6, VII7 -> T, DD -> K64/D/D7
- Syntax: CADENCE_K64_STRONG_BEAT, SYNTAX_NO_D_TO_S, SYNTAX_NO_D_TO_K64, SYNTAX_K64_MUST_RESOLVE_TO_D
- Corner cases: false relation (переченье), deceptive resolutions in major/minor, unisons
- Benchmark verification: clean textbook examples pass with zero hard violations.
"""

import pytest
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.rules.engine import RuleEngine
from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
    check_voice_overlapping,
    check_unisons,
    check_melodic_intervals,
)
from src.harmony.rules.spacing import (
    check_voice_ranges,
    check_voice_crossing,
    check_texture_spacing,
)
from src.harmony.rules.doubling import (
    check_main_triad_doubling,
    check_sextaccord_doubling,
    check_k64_doubling,
    check_deceptive_vi_doubling,
    check_secondary_dominant_doubling,
)
from src.harmony.rules.resolutions import (
    check_seventh_resolution,
    check_d43_resolution,
    check_d2_resolution,
    check_leading_tone_resolution,
    check_vii7_resolution,
    check_secondary_dominant_resolution,
)
from src.harmony.rules.chromatic import check_false_relation
from tests.corpus.benchmark_tasks import BENCHMARK_TASKS


@pytest.fixture
def engine():
    return RuleEngine()


# ==============================================================================
# 1. VOICE LEADING & SPACING EXHAUSTIVE TESTS
# ==============================================================================

class TestVoiceLeadingExhaustive:
    """Verifies all horizontal voice-leading and vertical spacing rules."""

    @pytest.mark.parametrize(
        "v1_pair,v2_pair,v1_idx,v2_idx",
        [
            ((67, 60), (69, 62), 0, 1),  # S - A
            ((67, 60), (69, 62), 0, 2),  # S - T
            ((67, 48), (69, 50), 0, 3),  # S - B
            ((60, 53), (62, 55), 1, 2),  # A - T
            ((60, 41), (62, 43), 1, 3),  # A - B
            ((55, 48), (57, 50), 2, 3),  # T - B
        ],
    )
    def test_parallel_fifths_all_pairs(self, v1_pair, v2_pair, v1_idx, v2_idx):
        """Direct parallel fifths across each of the 6 voice pairs must trigger PARALLEL_FIFTHS."""
        satb1 = [64, 60, 55, 48]
        satb2 = [64, 60, 55, 48]
        satb1[v1_idx], satb1[v2_idx] = v1_pair
        satb2[v1_idx], satb2[v2_idx] = v2_pair

        v1 = Voicing(*satb1)
        v2 = Voicing(*satb2)

        violations = check_parallel_fifths_and_octaves(v1, v2)
        assert any(
            v.rule_id == "PARALLEL_FIFTHS" and v.voices == (v1_idx, v2_idx)
            for v in violations
        )

    @pytest.mark.parametrize(
        "v1_pair,v2_pair,v1_idx,v2_idx",
        [
            ((72, 60), (74, 62), 0, 1),  # S - A octave
            ((72, 48), (74, 50), 0, 3),  # S - B octave
            ((60, 60), (62, 62), 1, 2),  # A - T unison
            ((55, 43), (57, 45), 2, 3),  # T - B octave
        ],
    )
    def test_parallel_octaves_and_unisons(self, v1_pair, v2_pair, v1_idx, v2_idx):
        """Parallel pure octaves and parallel unisons must trigger PARALLEL_OCTAVES."""
        satb1 = [72, 60, 55, 48]
        satb2 = [72, 60, 55, 48]
        satb1[v1_idx], satb1[v2_idx] = v1_pair
        satb2[v1_idx], satb2[v2_idx] = v2_pair

        v1 = Voicing(*satb1)
        v2 = Voicing(*satb2)

        violations = check_parallel_fifths_and_octaves(v1, v2)
        assert any(
            v.rule_id == "PARALLEL_OCTAVES" and v.voices == (v1_idx, v2_idx)
            for v in violations
        )

    def test_contrary_fifths(self):
        """Contrary motion arriving into pure fifth must trigger CONTRARY_FIFTHS."""
        # S moves down: 67 -> 62 (-5), B moves up: 48 -> 55 (+7), int: 67-48=19(7), 62-55=7
        v1 = Voicing(soprano=67, alto=60, tenor=55, bass=48)
        v2 = Voicing(soprano=62, alto=60, tenor=55, bass=55)

        violations = check_contrary_fifths_and_octaves(v1, v2)
        assert any(v.rule_id == "CONTRARY_FIFTHS" for v in violations)

    def test_contrary_octaves(self):
        """Contrary motion arriving into pure octave must trigger CONTRARY_OCTAVES."""
        # S moves down: 72 -> 64 (-8), B moves up: 48 -> 52 (+4), int: 72-48=24(0), 64-52=12(0)
        v1 = Voicing(soprano=72, alto=60, tenor=55, bass=48)
        v2 = Voicing(soprano=64, alto=60, tenor=55, bass=52)

        violations = check_contrary_fifths_and_octaves(v1, v2)
        assert any(v.rule_id == "CONTRARY_OCTAVES" for v in violations)

    def test_hidden_fifths_and_octaves(self):
        """Hidden fifth/octave in outer voices with soprano leap > 2 semitones is blocked."""
        # S: 64 -> 69 (+5 leap!), B: 43 -> 45 (+2), both move up into 69 - 45 = 24 (octave)
        v1 = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        v2 = Voicing(soprano=69, alto=60, tenor=55, bass=45)

        violations = check_hidden_fifths_and_octaves(v1, v2)
        assert any(v.rule_id == "HIDDEN_FIFTHS_OCTAVES" for v in violations)

        # But if Soprano steps (<= 2 semitones), direct motion into octave/fifth is permitted
        v_step = Voicing(soprano=65, alto=60, tenor=55, bass=41)  # S: 64 -> 65 (+1), B: 48 -> 41
        assert len(check_hidden_fifths_and_octaves(v1, v_step)) == 0

    @pytest.mark.parametrize(
        "v1_satb,v2_satb,pair",
        [
            ((64, 60, 52, 48), (67, 65, 52, 48), (1, 0)),  # A (65) rose above prev S (64)
            ((64, 60, 52, 48), (64, 60, 62, 48), (2, 1)),  # T (62) rose above prev A (60)
            ((64, 60, 52, 48), (64, 60, 52, 53), (3, 2)),  # B (53) rose above prev T (52)
            ((64, 60, 52, 48), (59, 57, 52, 48), (0, 1)),  # S (59) fell below prev A (60)
            ((64, 60, 52, 48), (64, 51, 48, 40), (1, 2)),  # A (51) fell below prev T (52)
            ((64, 60, 52, 48), (64, 60, 47, 43), (2, 3)),  # T (47) fell below prev B (48)
        ],
    )
    def test_voice_overlapping_all_boundaries(self, v1_satb, v2_satb, pair):
        """Voice overlapping across any adjacent boundary must trigger VOICE_OVERLAPPING."""
        v1 = Voicing(*v1_satb)
        v2 = Voicing(*v2_satb)
        violations = check_voice_overlapping(v1, v2)
        assert any(
            v.rule_id == "VOICE_OVERLAPPING" and v.voices == pair
            for v in violations
        )

    def test_voice_crossing(self):
        """Voice crossing (S < A, A < T, or T < B) triggers VOICE_CROSSING."""
        assert any(v.rule_id == "VOICE_CROSSING" for v in check_voice_crossing(Voicing(59, 60, 52, 48)))
        assert any(v.rule_id == "VOICE_CROSSING" for v in check_voice_crossing(Voicing(64, 50, 52, 48)))
        assert any(v.rule_id == "VOICE_CROSSING" for v in check_voice_crossing(Voicing(64, 60, 45, 48)))

    def test_unisons_direct_motion_forbidden(self):
        """Taking or leaving a unison in direct motion is strictly forbidden."""
        # 1. Direct motion INTO unison: Alto (64) and Tenor (62) both move DOWN to 60
        v1 = Voicing(soprano=72, alto=64, tenor=62, bass=48)
        v2 = Voicing(soprano=72, alto=60, tenor=60, bass=48)
        viol = check_unisons(v1, v2)
        assert any(v.rule_id == "DIRECT_UNISON" and v.voices == (1, 2) for v in viol)

        # 2. Direct motion OUT OF unison: Alto (60) and Tenor (60) both move UP to 64 and 62
        viol_out = check_unisons(v2, v1)
        assert any(v.rule_id == "DIRECT_UNISON" and v.voices == (1, 2) for v in viol_out)

        # 3. Contrary motion INTO unison is PERMITTED:
        # Alto (62) moves DOWN to 60 (-2), Tenor (59) moves UP to 60 (+1)
        v_contrary_prev = Voicing(soprano=72, alto=62, tenor=59, bass=48)
        v_contrary_curr = Voicing(soprano=72, alto=60, tenor=60, bass=48)
        assert len(check_unisons(v_contrary_prev, v_contrary_curr)) == 0

        # 4. Oblique motion INTO unison is PERMITTED:
        # Alto stays on 60 (0), Tenor moves from 55 to 60 (+5)
        v_oblique_prev = Voicing(soprano=72, alto=60, tenor=55, bass=48)
        v_oblique_curr = Voicing(soprano=72, alto=60, tenor=60, bass=48)
        assert len(check_unisons(v_oblique_prev, v_oblique_curr)) == 0

    def test_melodic_intervals(self):
        """Tests forbidden leaps: 7ths, > 12 semitones, tritone, and aug2 in minor."""
        key_c = Key(tonic="C", mode="Major")
        key_a_minor = Key(tonic="A", mode="MinorHarmonic")

        # 7th leap (10 semitones) in Soprano: 60 -> 70
        v1 = Voicing(soprano=60, alto=60, tenor=55, bass=48)
        v2 = Voicing(soprano=70, alto=60, tenor=55, bass=48)
        assert any(v.rule_id == "MELODIC_SEVENTH_LEAP" for v in check_melodic_intervals(v1, v2, key=key_c))

        # Leap > 12 (14 semitones) in Bass: 40 -> 54
        v3 = Voicing(soprano=60, alto=60, tenor=55, bass=40)
        v4 = Voicing(soprano=60, alto=60, tenor=55, bass=54)
        assert any(v.rule_id == "MELODIC_SEVENTH_LEAP" for v in check_melodic_intervals(v3, v4, key=key_c))

        # Tritone leap (6 semitones) in Alto: 60 -> 66
        v5 = Voicing(soprano=72, alto=60, tenor=55, bass=48)
        v6 = Voicing(soprano=72, alto=66, tenor=55, bass=48)
        assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in check_melodic_intervals(v5, v6, key=key_c))

        # Augmented 2nd leap (F4=65 to G#4=68) in A minor
        v7 = Voicing(soprano=69, alto=65, tenor=57, bass=45)
        v8 = Voicing(soprano=69, alto=68, tenor=57, bass=40)
        assert any(v.rule_id == "MELODIC_AUGMENTED_INTERVAL" for v in check_melodic_intervals(v7, v8, key=key_a_minor))

    def test_texture_spacing_and_ranges(self):
        """Spacing limits between upper voices (<=12) and bass-tenor (<=24), plus range limits."""
        # S - A gap = 14 > 12 semitones
        v_gap_sa = Voicing(soprano=76, alto=62, tenor=55, bass=48)
        assert any(v.rule_id == "UPPER_VOICE_SPACING_LIMIT" for v in check_texture_spacing(v_gap_sa))

        # A - T gap = 15 > 12 semitones
        v_gap_at = Voicing(soprano=72, alto=70, tenor=55, bass=48)
        assert any(v.rule_id == "UPPER_VOICE_SPACING_LIMIT" for v in check_texture_spacing(v_gap_at))

        # T - B gap = 26 > 24 semitones
        v_gap_tb = Voicing(soprano=72, alto=67, tenor=66, bass=40)
        assert any(v.rule_id == "BASS_TENOR_SPACING_LIMIT" for v in check_texture_spacing(v_gap_tb))

        # Standard range violations:
        assert any(v.rule_id == "VOICE_RANGE_BOUNDS" for v in check_voice_ranges(Voicing(83, 60, 52, 48)))  # S > 81
        assert any(v.rule_id == "VOICE_RANGE_BOUNDS" for v in check_voice_ranges(Voicing(64, 52, 52, 48)))  # A < 55
        assert any(v.rule_id == "VOICE_RANGE_BOUNDS" for v in check_voice_ranges(Voicing(64, 60, 46, 40)))  # T < 48
        assert any(v.rule_id == "VOICE_RANGE_BOUNDS" for v in check_voice_ranges(Voicing(64, 60, 52, 38)))  # B < 40


# ==============================================================================
# 2. CHORD DOUBLING EXHAUSTIVE TESTS
# ==============================================================================

class TestDoublingExhaustive:
    """Verifies doubling rules for triads, sextaccords, K64, deceptive VI, and DD."""

    def test_main_triad_root_doubling(self):
        key = Key(tonic="C", mode="Major")
        chord_t = Chord(function="T")

        # Third E doubled (C, E, E, G): forbidden in root-position main triad!
        v_third_doubled = Voicing(soprano=64, alto=64, tenor=55, bass=48)
        viol = check_main_triad_doubling(v_third_doubled, chord_t, key=key)
        assert any(v.rule_id == "DOUBLING_MAIN_TRIAD_ROOT" for v in viol)

        # Standard doubled root (C, E, G, C): valid!
        v_good = Voicing(soprano=64, alto=60, tenor=55, bass=48)
        assert len(check_main_triad_doubling(v_good, chord_t, key=key)) == 0

        # Incomplete triad with tripled root (C, C, C, E) and single third: valid!
        Voicing(soprano=64, alto=60, tenor=48, bass=36)  # allow extended bass or 48/60
        v_tripled = Voicing(soprano=64, alto=60, tenor=48, bass=48)
        assert len(check_main_triad_doubling(v_tripled, chord_t, key=key)) == 0

    def test_sextaccord_doubling(self):
        key = Key(tonic="C", mode="Major")
        chord_t6 = Chord(function="T6")
        chord_d6 = Chord(function="D6")

        # 1. T6 with doubled root C (E, G, C, C): valid!
        Voicing(soprano=64, alto=60, tenor=55, bass=52)  # S=E, A=C, T=G, B=E(52) -> wait, bass of T6 is E (52)
        # T6 in C: bass is E3 (52). Root=C, Fifth=G.
        # Voicing: S=C5(72), A=G4(67), T=C4(60), B=E3(52) -> C doubled, E single, G single!
        v_t6_doubled_root = Voicing(soprano=72, alto=67, tenor=60, bass=52)
        assert len(check_sextaccord_doubling(v_t6_doubled_root, chord_t6, key=key)) == 0

        # 2. T6 with doubled fifth G (G, G, C, E): valid!
        v_t6_doubled_fifth = Voicing(soprano=67, alto=67, tenor=60, bass=52)
        assert len(check_sextaccord_doubling(v_t6_doubled_fifth, chord_t6, key=key)) == 0

        # 3. T6 with doubled third E without D43/D2 resolution: forbidden!
        v_t6_doubled_third = Voicing(soprano=64, alto=64, tenor=60, bass=52)  # E4, E4, C4, E3 -> third E doubled!
        viol = check_sextaccord_doubling(v_t6_doubled_third, chord_t6, key=key)
        assert any(v.rule_id == "DOUBLING_SEXTACCORD" for v in viol)

        # 4. T6 with doubled third coming from D43 resolution: permitted!
        chord_d43 = Chord(function="D43")
        viol_d43 = check_sextaccord_doubling(v_t6_doubled_third, chord_t6, key=key, prev_chord=chord_d43)
        assert len(viol_d43) == 0

        # 5. D6: Leading tone B (third) doubled: STRICTLY FORBIDDEN!
        # D6 in C: bass is B2 (47). Leading tone is B.
        # If B is doubled (e.g. S=B4(71), A=G4(67), T=D4(62), B=B2(47)):
        v_d6_doubled_lt = Voicing(soprano=71, alto=67, tenor=62, bass=47)
        viol_d6 = check_sextaccord_doubling(v_d6_doubled_lt, chord_d6, key=key)
        assert any(v.rule_id == "DOUBLING_D6_LEADING_TONE" for v in viol_d6)

        # 6. D6 with doubled root G: valid!
        v_d6_good = Voicing(soprano=67, alto=67, tenor=62, bass=47)  # G4, G4, D4, B2
        assert len(check_sextaccord_doubling(v_d6_good, chord_d6, key=key)) == 0

    def test_k64_strictly_doubles_bass(self):
        key = Key(tonic="C", mode="Major")
        chord_k64 = Chord(function="K64")

        # In C major, K64 has bass G (43). Bass G must be doubled!
        # Good K64: S=E4(64), A=C4(60), T=G3(55), B=G2(43) -> G doubled
        v_good = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        assert len(check_k64_doubling(v_good, chord_k64, key=key)) == 0

        # Bad K64: doubled root C (E4, C4, C3, G2) -> Bass G is NOT doubled!
        v_bad = Voicing(soprano=64, alto=60, tenor=48, bass=43)
        viol = check_k64_doubling(v_bad, chord_k64, key=key)
        assert any(v.rule_id == "DOUBLING_K64_BASS_ONLY" for v in viol)

    def test_deceptive_cadence_doubles_third(self):
        key = Key(tonic="A", mode="MinorHarmonic")
        chord_d7 = Chord(function="D7")
        chord_vi = Chord(function="VI")

        # VI in A minor is F major (F-A-C). Third is A (tonic degree I).
        # Good deceptive cadence: third A is strictly doubled!
        v_good_vi = Voicing(soprano=69, alto=60, tenor=57, bass=41)  # A4, C4, A3, F2 -> A doubled
        assert len(check_deceptive_vi_doubling(v_good_vi, chord_d7, chord_vi, key=key)) == 0

        # Bad deceptive cadence: root F is doubled instead (F4, C4, F3, F2)
        v_bad_vi = Voicing(soprano=65, alto=60, tenor=53, bass=41)
        viol = check_deceptive_vi_doubling(v_bad_vi, chord_d7, chord_vi, key=key)
        assert any(v.rule_id == "DOUBLING_DECEPTIVE_VI_THIRD" for v in viol)

    def test_secondary_dominant_doubling(self):
        key = Key(tonic="C", mode="Major")
        chord_dd = Chord(function="DD")

        # In C-dur: DD (D-F#-A). Secondary leading tone is F# (third).
        # Good DD: root D doubled, F# single (F#4, D4, A3, D3)
        v_good = Voicing(soprano=66, alto=62, tenor=57, bass=50)
        assert len(check_secondary_dominant_doubling(v_good, chord_dd, key=key)) == 0

        # Bad DD: secondary leading tone F# doubled (F#4, F#4, A3, D3)
        v_bad = Voicing(soprano=66, alto=66, tenor=57, bass=50)
        viol = check_secondary_dominant_doubling(v_bad, chord_dd, key=key)
        assert any(v.rule_id == "DOUBLING_SECONDARY_DOMINANT" for v in viol)


# ==============================================================================
# 3. RESOLUTIONS & TENDENCY TONES EXHAUSTIVE TESTS
# ==============================================================================

class TestResolutionsExhaustive:
    """Verifies 7th resolution, leading tone resolution, D43/D2, VII7, and DD."""

    def test_dominant_seventh_resolution_down(self):
        key = Key(tonic="C", mode="Major")
        c_d7 = Chord(function="D7")
        c_t = Chord(function="T")

        # D7: G4(67), F4(65), D4(62), G2(43) -> 7th is F4 in Alto
        # Good resolution: F4 resolves down by half-step to E4 (64)
        v_d7 = Voicing(soprano=67, alto=65, tenor=62, bass=43)
        v_t_good = Voicing(soprano=67, alto=64, tenor=60, bass=48)
        assert len(check_seventh_resolution(v_d7, v_t_good, c_d7, c_t, key=key)) == 0

        # Bad resolution: F4 leaps up to G4 (67)
        v_t_bad = Voicing(soprano=67, alto=67, tenor=60, bass=48)
        viol = check_seventh_resolution(v_d7, v_t_bad, c_d7, c_t, key=key)
        assert any(v.rule_id == "RESOLUTION_SEVENTH_DOWN" for v in viol)

    def test_outer_leading_tone_resolution_up(self):
        key = Key(tonic="C", mode="Major")
        c_d = Chord(function="D")
        c_t = Chord(function="T")

        # Leading tone B4 (71) in Soprano must resolve UP to C5 (72)
        v_d = Voicing(soprano=71, alto=67, tenor=62, bass=43)
        v_t_good = Voicing(soprano=72, alto=67, tenor=60, bass=48)
        assert len(check_leading_tone_resolution(v_d, v_t_good, c_d, c_t, key=key)) == 0

        # If leading tone in Soprano drops to G4 (67): forbidden!
        v_t_bad = Voicing(soprano=67, alto=67, tenor=60, bass=48)
        viol = check_leading_tone_resolution(v_d, v_t_bad, c_d, c_t, key=key)
        assert any(v.rule_id == "RESOLUTION_LEADING_TONE_UP" for v in viol)

    def test_d43_resolves_to_t_or_t6(self):
        key = Key(tonic="F", mode="Major")
        c_d43 = Chord(function="D43")
        c_t6 = Chord(function="T6")
        c_ii = Chord(function="II")
        c_t = Chord(function="T")

        # Canonical D43 in F-dur: V7 = C-E-G-Bb, 4/3 bass = FIFTH of chord = G.
        # S=G4(67), A=Bb3(58, 7th), T=E3(52, 3rd), B=G2(43).
        v_d43 = Voicing(soprano=67, alto=58, tenor=52, bass=43)

        # Canonical resolution to T53: bass G->F (-2), 7th Bb->A (-1), 3rd E->F (+1).
        v_t = Voicing(soprano=69, alto=57, tenor=53, bass=41)
        assert len(check_d43_resolution(v_d43, v_t, c_d43, c_t, key=key)) == 0

        # Canonical resolution to T6: bass G->A (+2).
        v_t6 = Voicing(soprano=65, alto=57, tenor=53, bass=45)
        assert len(check_d43_resolution(v_d43, v_t6, c_d43, c_t6, key=key)) == 0

        # Forbidden target: D43 -> II
        v_ii = Voicing(soprano=69, alto=62, tenor=55, bass=43)
        viol_ii = check_d43_resolution(v_d43, v_ii, c_d43, c_ii, key=key)
        assert any(v.rule_id == "RESOLUTION_D43_TO_T6" for v in viol_ii)

    def test_d2_must_resolve_to_t6(self):
        key = Key(tonic="C", mode="Major")
        c_d2 = Chord(function="D2")
        c_t6 = Chord(function="T6")
        c_t = Chord(function="T")

        # In C major: D2 has seventh F in bass (F2=41 or F3=53).
        # Bass F2(41) MUST step down by semitone into E2(40, third of T6).
        v_d2 = Voicing(soprano=71, alto=67, tenor=62, bass=41)  # B4, G4, D4, F2
        v_t6 = Voicing(soprano=72, alto=67, tenor=60, bass=40)  # C5, G4, C4, E2
        assert len(check_d2_resolution(v_d2, v_t6, c_d2, c_t6, key=key)) == 0

        # Target not T6: D2 -> T 5/3 (bass jumps to C2=36 or C3=48)
        v_t53 = Voicing(soprano=72, alto=67, tenor=60, bass=48)
        viol_t = check_d2_resolution(v_d2, v_t53, c_d2, c_t, key=key)
        assert any(v.rule_id == "RESOLUTION_D2_TO_T6" for v in viol_t)

    def test_vii7_complete_resolution(self):
        key = Key(tonic="C", mode="Major")
        c_vii7 = Chord(function="VII7")
        c_t = Chord(function="T")

        # VII7 in C: B2(47), D4(62), F4(65), Ab4(68)
        # Resolution to T:
        # S: Ab4(68) -> G4(67) (7th resolves down by step -1)
        # A: F4(65)  -> E4(64) (5th resolves down into 3rd -1)
        # T: D4(62)  -> E4(64) (3rd resolves up into 3rd +2 -> doubled third!)
        # B: B2(47)  -> C3(48) (leading tone resolves up by half-step +1)
        v_vii7 = Voicing(soprano=68, alto=65, tenor=62, bass=47)
        v_t = Voicing(soprano=67, alto=64, tenor=64, bass=48)

        # Valid resolution: zero violations
        assert len(check_vii7_resolution(v_vii7, v_t, c_vii7, c_t, key=key)) == 0

        # 1. Seventh Ab4(68) leaps up to C5(72) -> violation!
        v_bad_7th = Voicing(soprano=72, alto=64, tenor=64, bass=48)
        viol_7 = check_vii7_resolution(v_vii7, v_bad_7th, c_vii7, c_t, key=key)
        assert any(v.rule_id == "RESOLUTION_VII7_SEVENTH_DOWN" for v in viol_7)

        # 2. Fifth F4(65) leaps up to G4(67) -> violation!
        v_bad_5th = Voicing(soprano=67, alto=67, tenor=64, bass=48)
        viol_5 = check_vii7_resolution(v_vii7, v_bad_5th, c_vii7, c_t, key=key)
        assert any(v.rule_id == "RESOLUTION_VII7_FIFTH_DOWN" for v in viol_5)

        # 3. Leading tone B2(47) drops to G2(43) -> violation!
        v_bad_lt = Voicing(soprano=67, alto=64, tenor=64, bass=43)
        viol_lt = check_vii7_resolution(v_vii7, v_bad_lt, c_vii7, c_t, key=key)
        assert any(v.rule_id == "RESOLUTION_VII7_LEADING_TONE_UP" for v in viol_lt)

    def test_secondary_dominant_resolution_targets_and_tendencies(self):
        key = Key(tonic="C", mode="Major")
        Chord(function="DD")
        c_dd7 = Chord(function="DD7")
        c_k64 = Chord(function="K64")
        c_d = Chord(function="D")
        c_s = Chord(function="S")

        # DD7 in C: D3(50), A3(57), F#4(66), C5(72)
        v_dd7 = Voicing(soprano=72, alto=66, tenor=57, bass=50)

        # Valid resolution: DD7 -> K64 (C5 is held common tone 0, F#4 steps up to G4 +1)
        v_k64 = Voicing(soprano=72, alto=67, tenor=55, bass=43)
        assert len(check_secondary_dominant_resolution(v_dd7, v_k64, c_dd7, c_k64, key=key)) == 0

        # Valid resolution: DD7 -> D (C5 steps down to B4 -1, F#4 steps up to G4 +1)
        v_d = Voicing(soprano=71, alto=67, tenor=55, bass=43)
        assert len(check_secondary_dominant_resolution(v_dd7, v_d, c_dd7, c_d, key=key)) == 0

        # Invalid target: DD7 -> S (functional regression!)
        v_s = Voicing(soprano=69, alto=65, tenor=57, bass=41)
        viol_tgt = check_secondary_dominant_resolution(v_dd7, v_s, c_dd7, c_s, key=key)
        assert any(v.rule_id == "RESOLUTION_DD_TARGET" for v in viol_tgt)


# ==============================================================================
# 4. SYNTAX RULES EXHAUSTIVE TESTS
# ==============================================================================

class TestSyntaxExhaustive:
    """Verifies macro harmonic syntax constraints in RuleEngine."""

    def test_k64_strong_beat_requirement(self, engine):
        chord_k64 = Chord(function="K64")
        v = Voicing(soprano=72, alto=67, tenor=60, bass=43)

        # Weak beat: forbidden!
        res_weak = engine.validate(None, v, curr_chord=chord_k64, is_downbeat=False)
        assert not res_weak.is_valid
        assert any(v.rule_id == "CADENCE_K64_STRONG_BEAT" for v in res_weak.hard_violations)

        # Downbeat: valid!
        res_strong = engine.validate(None, v, curr_chord=chord_k64, is_downbeat=True)
        assert not any(v.rule_id == "CADENCE_K64_STRONG_BEAT" for v in res_strong.hard_violations)

    @pytest.mark.parametrize("d_func", ["D", "D7", "D6", "D65", "D43", "D2", "DD"])
    @pytest.mark.parametrize("s_func", ["S", "S6", "II", "II6"])
    def test_functional_regression_d_to_s_all_combinations(self, engine, d_func, s_func):
        """Any regression from Dominant group to Subdominant group must be blocked."""
        c_d = Chord(function=d_func)
        c_s = Chord(function=s_func)
        v1 = Voicing(soprano=67, alto=62, tenor=55, bass=43)
        v2 = Voicing(soprano=65, alto=60, tenor=53, bass=41)

        res = engine.validate(v1, v2, prev_chord=c_d, curr_chord=c_s)
        assert not res.is_valid
        assert any(v.rule_id == "SYNTAX_NO_D_TO_S" for v in res.hard_violations)

    def test_regression_d_to_k64(self, engine):
        """D -> K64 regression is strictly blocked."""
        c_d = Chord(function="D")
        c_k64 = Chord(function="K64")
        v_d = Voicing(soprano=67, alto=62, tenor=55, bass=43)
        v_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)

        res = engine.validate(v_d, v_k64, prev_chord=c_d, curr_chord=c_k64, is_downbeat=True)
        assert not res.is_valid
        assert any(v.rule_id == "SYNTAX_NO_D_TO_K64" for v in res.hard_violations)

    def test_k64_must_resolve_to_dominant(self, engine):
        """K64 must resolve to D or D7, never to T or S."""
        c_k64 = Chord(function="K64")
        c_t = Chord(function="T")
        c_d = Chord(function="D")
        v_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)
        v_t = Voicing(soprano=64, alto=60, tenor=52, bass=48)
        v_d = Voicing(soprano=62, alto=59, tenor=55, bass=43)

        # K64 -> T is invalid
        res_t = engine.validate(v_k64, v_t, prev_chord=c_k64, curr_chord=c_t)
        assert not res_t.is_valid
        assert any(v.rule_id == "SYNTAX_K64_MUST_RESOLVE_TO_D" for v in res_t.hard_violations)

        # K64 -> D is valid
        res_d = engine.validate(v_k64, v_d, prev_chord=c_k64, curr_chord=c_d)
        assert not any(v.rule_id == "SYNTAX_K64_MUST_RESOLVE_TO_D" for v in res_d.hard_violations)


# ==============================================================================
# 5. CORNER CASES & BENCHMARK VALIDATION
# ==============================================================================

class TestCornerCasesAndBenchmarks:
    """Verifies edge cases (false relation, deceptive cadence) and classical benchmarks."""

    def test_chromatic_false_relation(self):
        key = Key(tonic="C", mode="Major")

        # 1. Diatonic semitone (E-F or B-C) must NOT trigger false relation
        v_diat1 = Voicing(soprano=71, alto=67, tenor=62, bass=50)
        v_diat2 = Voicing(soprano=69, alto=66, tenor=60, bass=50)
        assert len(check_false_relation(v_diat1, v_diat2, key=key)) == 0

        # 2. Chromatic step in SAME voice (Tenor F3(53) -> F#3(54)) is valid
        v_same1 = Voicing(soprano=64, alto=60, tenor=53, bass=48)
        v_same2 = Voicing(soprano=62, alto=60, tenor=54, bass=50)
        assert len(check_false_relation(v_same1, v_same2, key=key)) == 0

        # 3. False relation (Alto has F4=65, Tenor introduces F#3=54) triggers FALSE_RELATION_PERECHENIE
        v_pere1 = Voicing(soprano=67, alto=65, tenor=60, bass=48)
        v_pere2 = Voicing(soprano=67, alto=64, tenor=54, bass=50)
        viol = check_false_relation(v_pere1, v_pere2, key=key)
        assert any(v.rule_id == "FALSE_RELATION_PERECHENIE" for v in viol)

    def test_deceptive_cadence_in_major_and_minor(self, engine):
        """Verifies clean deceptive cadence transitions in both major and minor."""
        # C major: D7 -> VI. Leading tone B in SOPRANO so the doubled tonic
        # lands in different octaves (C5 and C4) instead of an A=T unison.
        key_c = Key(tonic="C", mode="Major")
        c_d7 = Chord(function="D7")
        c_vi = Chord(function="VI")
        # D7: S=B4(71, leading tone), A=F4(65, 7th), T=D4(62, 5th), B=G2(43)
        # VI: S=C5(72, lt up), A=E4(64, 7th down), T=C4(60, 5th down), B=A2(45)
        v_d7 = Voicing(soprano=71, alto=65, tenor=62, bass=43)
        v_vi = Voicing(soprano=72, alto=64, tenor=60, bass=45)

        res_c = engine.validate(v_d7, v_vi, prev_chord=c_d7, curr_chord=c_vi, key=key_c)
        assert res_c.is_valid
        assert not res_c.has_hard_violations

        # A minor: D7 -> VI. D7 (E-G#-B-D): S=B4(71), A=D4(62), T=G#3(56, lt), B=E2(40)
        # VI (F-A-C): S=A4(69, lt up), A=C4(60, 7th down), T=A3(57, 5th), B=F2(41)
        key_a = Key(tonic="A", mode="MinorHarmonic")
        v_d7_m = Voicing(soprano=71, alto=62, tenor=56, bass=40)
        v_vi_m = Voicing(soprano=69, alto=60, tenor=57, bass=41)

        res_a = engine.validate(v_d7_m, v_vi_m, prev_chord=c_d7, curr_chord=c_vi, key=key_a)
        assert res_a.is_valid
        assert not res_a.has_hard_violations

    @pytest.mark.parametrize("task", BENCHMARK_TASKS, ids=[t["id"] for t in BENCHMARK_TASKS])
    def test_all_brigade_benchmark_tasks_pass_cleanly(self, engine, task):
        """All human reference solutions from the Brigade textbook pass with zero hard violations."""
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

            hard_errors = [f"{v.rule_id}: {v.description}" for v in res.hard_violations]
            assert not res.has_hard_violations, (
                f"Task '{task['id']}' failed at chord {idx} ({func}): {hard_errors}"
            )
            assert res.cost < float("inf")

            prev_v = curr_v
            prev_chord = curr_chord
