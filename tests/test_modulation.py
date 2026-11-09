"""
Unit tests for harmony.core.modulation.

Verifies First-Degree Relations, Pivot Chords, Modulation Plans, and Secondary Dominants
strictly adhering to the Brigade harmony textbook (Дубовский et al., chapters 26-28, 29, 30, 31).
"""

import pytest
from harmony.core.key import Key, Mode
from harmony.core.pitch import PitchClass
from harmony.core.types import Voicing, Chord
from harmony.rules.doubling import check_secondary_dominant_doubling
from harmony.rules.resolutions import check_secondary_dominant_resolution
from harmony.rules.engine import RuleEngine
from harmony.syntax.grammar import HarmonicGrammar
from harmony.core.modulation import (
    FirstDegreeRelations,
    RelatedKeyInfo,
    get_related_keys_first_degree,
    PivotChord,
    find_pivot_chords,
    build_modulation_plan,
    SecondaryDominant,
    get_secondary_dominants,
)


class TestFirstDegreeRelations:
    """Tests for First-Degree Related Keys (Бригадный учебник, гл. 29)."""

    def test_c_major_six_related_keys(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        relations = get_related_keys_first_degree(c_dur)

        assert len(relations) == 6
        assert isinstance(relations, FirstDegreeRelations)

        # 1. V (Dominant): G Major
        assert relations[0].key == Key(PitchClass.G, Mode.MAJOR)
        assert relations[0].symbol == "V"
        assert relations[0].degree_in_source == 5
        assert not relations[0].is_subdominant_group

        # 2. VI (Submediant / Parallel minor): A MinorHarmonic
        assert relations[1].key == Key(PitchClass.A, Mode.MINOR_HARMONIC)
        assert relations[1].symbol == "VI"
        assert relations[1].degree_in_source == 6
        assert relations[1].is_subdominant_group

        # 3. IV (Subdominant): F Major
        assert relations[2].key == Key(PitchClass.F, Mode.MAJOR)
        assert relations[2].symbol == "IV"
        assert relations[2].degree_in_source == 4
        assert relations[2].is_subdominant_group

        # 4. II (Supertonic): D MinorHarmonic
        assert relations[3].key == Key(PitchClass.D, Mode.MINOR_HARMONIC)
        assert relations[3].symbol == "II"
        assert relations[3].degree_in_source == 2
        assert relations[3].is_subdominant_group

        # 5. III (Mediant): E MinorHarmonic
        assert relations[4].key == Key(PitchClass.E, Mode.MINOR_HARMONIC)
        assert relations[4].symbol == "III"
        assert relations[4].degree_in_source == 3
        assert not relations[4].is_subdominant_group

        # 6. iv (Minor subdominant / гармоническая субдоминанта): F MinorHarmonic
        assert relations[5].key == Key(PitchClass.F, Mode.MINOR_HARMONIC)
        assert relations[5].symbol == "iv"
        assert relations[5].degree_in_source == 4
        assert relations[5].is_subdominant_group

    def test_a_minor_six_related_keys(self):
        a_moll = Key(PitchClass.A, Mode.MINOR_HARMONIC)
        relations = get_related_keys_first_degree(a_moll)

        assert len(relations) == 6

        # 1. III (Parallel major): C Major
        assert relations[0].key == Key(PitchClass.C, Mode.MAJOR)
        assert relations[0].symbol == "III"
        assert relations[0].degree_in_source == 3
        assert not relations[0].is_subdominant_group

        # 2. iv (Subdominant): D MinorHarmonic
        assert relations[1].key == Key(PitchClass.D, Mode.MINOR_HARMONIC)
        assert relations[1].symbol == "iv"
        assert relations[1].degree_in_source == 4
        assert relations[1].is_subdominant_group

        # 3. VI (Submediant major): F Major
        assert relations[2].key == Key(PitchClass.F, Mode.MAJOR)
        assert relations[2].symbol == "VI"
        assert relations[2].degree_in_source == 6
        assert relations[2].is_subdominant_group

        # 4. v (Natural minor dominant): E MinorNatural (or E MinorHarmonic)
        assert relations[3].key == Key(PitchClass.E, Mode.MINOR_NATURAL)
        assert relations[3].symbol == "v"
        assert relations[3].degree_in_source == 5
        assert not relations[3].is_subdominant_group

        # 5. VII (Natural subtonic major): G Major
        assert relations[4].key == Key(PitchClass.G, Mode.MAJOR)
        assert relations[4].symbol == "VII"
        assert relations[4].degree_in_source == 7
        assert not relations[4].is_subdominant_group

        # 6. V (Harmonic major dominant): E Major
        assert relations[5].key == Key(PitchClass.E, Mode.MAJOR)
        assert relations[5].symbol == "V"
        assert relations[5].degree_in_source == 5
        assert not relations[5].is_subdominant_group

    def test_query_helpers(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        relations = get_related_keys_first_degree(c_dur)

        # Lookup by symbol
        assert relations["V"].key == Key(PitchClass.G, Mode.MAJOR)
        assert relations["VI"].key == Key(PitchClass.A, Mode.MINOR_HARMONIC)
        assert relations["iv"].key == Key(PitchClass.F, Mode.MINOR_HARMONIC)

        # Lookup by relation name
        assert relations.by_relation_name("dominant").key == Key(PitchClass.G, Mode.MAJOR)

        # Subdominant vs dominant groupings
        s_group = relations.subdominant_group
        assert len(s_group) == 4  # VI, IV, II, iv
        assert all(r.is_subdominant_group for r in s_group)

        d_group = relations.dominant_group
        assert len(d_group) == 2  # V, III
        assert all(not r.is_subdominant_group for r in d_group)

        # Membership test
        assert relations.contains_key(Key(PitchClass.G, Mode.MAJOR))
        assert relations.contains_key("F MinorHarmonic")
        assert not relations.contains_key("Bb Major")


class TestPivotChords:
    """Tests for Pivot Chords (Бригадный учебник, гл. 30)."""

    def test_pivot_chords_c_major_to_g_major(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        g_dur = Key(PitchClass.G, Mode.MAJOR)

        pivots = find_pivot_chords(c_dur, g_dur)
        assert len(pivots) >= 4

        # In C-dur -> G-dur, common triads are:
        # A-C-E: VI in C-dur, II in G-dur (Strongest subdominant in G!)
        # C-E-G: T in C-dur, IV in G-dur (Subdominant in G!)
        # E-G-B: III in C-dur, VI in G-dur (Subdominant group in G!)
        # G-B-D: D in C-dur, T in G-dur (Tonic in G)
        top_pivot = pivots[0]
        # Best pivot chords must be in the subdominant group of target key
        assert top_pivot.is_subdominant_in_target
        assert top_pivot.target_function in ("II", "IV", "VI")

        # Verify weights descending
        weights = [p.weight for p in pivots]
        assert weights == sorted(weights, reverse=True)

        # Specifically check II in target G-dur gets top priority
        ii_pivot = next(p for p in pivots if p.target_function == "II")
        assert ii_pivot.source_function == "VI"
        assert ii_pivot.pitch_classes == (PitchClass.A, PitchClass.C, PitchClass.E)

        # Check tonic pivot has lower weight than subdominant pivots
        t_pivot = next(p for p in pivots if p.target_function == "T")
        assert t_pivot.weight < ii_pivot.weight

    def test_pivot_chords_c_major_to_a_minor(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        a_moll = Key(PitchClass.A, Mode.MINOR_HARMONIC)

        pivots = find_pivot_chords(c_dur, a_moll)
        assert len(pivots) >= 4

        # D-F-A: II in C-dur, iv in A-minor (subdominant!)
        # F-A-C: IV in C-dur, VI in A-minor (subdominant group!)
        subdominant_pivots = [p for p in pivots if p.is_subdominant_in_target]
        assert len(subdominant_pivots) >= 2
        # Best pivot should be subdominant in target
        assert pivots[0].is_subdominant_in_target


class TestModulationPlanBuilder:
    """Tests for Modulation Plan Construction (Бригадный учебник, гл. 30, 31)."""

    def test_canonical_modulation_c_major_to_g_major(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        g_dur = Key(PitchClass.G, Mode.MAJOR)

        plan = build_modulation_plan(c_dur, g_dur)

        # Should start in source key and conclude in target key
        assert plan[0][0] == c_dur
        assert plan[-1][0] == g_dur

        # Target cadence must end with K64 -> D7 -> T (since top pivot is subdominant group)
        last_three = plan[-3:]
        assert last_three == [
            (g_dur, "K64"),
            (g_dur, "D7"),
            (g_dur, "T"),
        ]

    def test_modulation_plan_with_dominant_pivot(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        g_dur = Key(PitchClass.G, Mode.MAJOR)

        # Manually force G-B-D (D in C, V in G) as pivot
        d_pivot = PivotChord(
            source_function="D",
            target_function="V",
            pitch_classes=(PitchClass.G, PitchClass.B, PitchClass.D),
            weight=15.0,
        )
        plan = build_modulation_plan(c_dur, g_dur, pivot_chord=d_pivot)

        # In Brigade harmony, dominant pivot chord cannot take K64 (D -> K64 forbidden)
        # Sequence must go directly to D7 -> T!
        assert not any(symbol == "K64" for _, symbol in plan)
        assert plan[-2:] == [(g_dur, "D7"), (g_dur, "T")]

    def test_modulation_plan_full_initial_cadence(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        g_dur = Key(PitchClass.G, Mode.MAJOR)

        plan = build_modulation_plan(c_dur, g_dur, include_full_cadence=True)
        # Should contain full exposition T, S, D, T in source key
        first_four = plan[:4]
        assert first_four == [
            (c_dur, "T"),
            (c_dur, "S"),
            (c_dur, "D"),
            (c_dur, "T"),
        ]


class TestSecondaryDominants:
    """Tests for Secondary Dominants / Tonicization (Бригадный учебник, гл. 26-28)."""

    def test_dd7_in_c_major_exact_specification(self):
        """
        Requirement specification test:
        DD7 in C-dur: Root=D (2), 3rd=F# (6), 5th=A (9), 7th=C (0).
        """
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        dd7 = SecondaryDominant.create(c_dur, "DD7")

        assert dd7.root == PitchClass.D
        assert dd7.root.value == 2

        assert dd7.third == PitchClass.F_SHARP
        assert dd7.third.value == 6

        assert dd7.fifth == PitchClass.A
        assert dd7.fifth.value == 9

        assert dd7.seventh == PitchClass.C
        assert dd7.seventh.value == 0

        assert dd7.is_seventh
        assert not dd7.is_diminished_seventh
        assert dd7.target_degree == 5

    def test_dd_triad_in_c_major(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        dd = SecondaryDominant.create(c_dur, "DD")

        assert dd.root == PitchClass.D
        assert dd.third == PitchClass.F_SHARP
        assert dd.fifth == PitchClass.A
        assert dd.seventh is None
        assert not dd.is_seventh
        assert dd.pitch_classes == (PitchClass.D, PitchClass.F_SHARP, PitchClass.A)

    def test_secondary_dominants_to_other_degrees_in_c_major(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)

        # D7/II: dominant seventh to II degree (D) -> A7 (A, C#, E, G)
        d7_ii = SecondaryDominant.create(c_dur, "D7/II")
        assert d7_ii.target_degree == 2
        assert d7_ii.root == PitchClass.A
        assert d7_ii.third == PitchClass.C_SHARP
        assert d7_ii.fifth == PitchClass.E
        assert d7_ii.seventh == PitchClass.G

        # D7/VI: dominant seventh to VI degree (A) -> E7 (E, G#, B, D)
        d7_vi = SecondaryDominant.create(c_dur, "D7/VI")
        assert d7_vi.target_degree == 6
        assert d7_vi.root == PitchClass.E
        assert d7_vi.third == PitchClass.G_SHARP
        assert d7_vi.fifth == PitchClass.B
        assert d7_vi.seventh == PitchClass.D

        # D7/IV: dominant seventh to IV degree (F) -> C7 (C, E, G, Bb)
        d7_iv = SecondaryDominant.create(c_dur, "D7/IV")
        assert d7_iv.target_degree == 4
        assert d7_iv.root == PitchClass.C
        assert d7_iv.third == PitchClass.E
        assert d7_iv.fifth == PitchClass.G
        assert d7_iv.seventh == PitchClass.BB

        # VII7/V: diminished leading-tone seventh to V degree (G) -> F#°7 (F#, A, C, Eb)
        vii7_v = SecondaryDominant.create(c_dur, "VII7/V")
        assert vii7_v.target_degree == 5
        assert vii7_v.root == PitchClass.F_SHARP
        assert vii7_v.third == PitchClass.A
        assert vii7_v.fifth == PitchClass.C
        assert vii7_v.seventh == PitchClass.EB
        assert vii7_v.is_diminished_seventh

    def test_secondary_dominants_in_minor(self):
        a_moll = Key(PitchClass.A, Mode.MINOR_HARMONIC)

        # DD7 in A minor: dominant seventh to V degree (E) -> B7 (B, D#, F#, A)
        dd7_a = SecondaryDominant.create(a_moll, "DD7")
        assert dd7_a.root == PitchClass.B
        assert dd7_a.third == PitchClass.D_SHARP
        assert dd7_a.fifth == PitchClass.F_SHARP
        assert dd7_a.seventh == PitchClass.A

        # D7/IV in A minor: dominant seventh to IV degree (D) -> A7 (A, C#, E, G)
        d7_iv = SecondaryDominant.create(a_moll, "D7/IV")
        assert d7_iv.root == PitchClass.A
        assert d7_iv.third == PitchClass.C_SHARP
        assert d7_iv.fifth == PitchClass.E
        assert d7_iv.seventh == PitchClass.G

    def test_get_secondary_dominants_enumeration(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        doms = get_secondary_dominants(c_dur)

        # 5 eligible degrees (II, III, IV, V, VI) * 3 chord variants (D, D7, VII7) = 15 chords
        assert len(doms) == 15
        assert all(isinstance(d, SecondaryDominant) for d in doms)

    def test_forbidden_secondary_dominant_targets(self):
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        a_moll = Key(PitchClass.A, Mode.MINOR_HARMONIC)

        # In major, VII degree is a diminished triad -> secondary dominant cannot tonicize it
        with pytest.raises(ValueError, match="cannot tonicize VII degree"):
            SecondaryDominant.create(c_dur, "D7/VII")

        # In minor, II degree is a diminished triad -> secondary dominant cannot tonicize it
        with pytest.raises(ValueError, match="cannot tonicize II degree"):
            SecondaryDominant.create(a_moll, "D7/II")


class TestSecondaryDominantResolutionsAndRules:
    """Verifies secondary dominant doubling and voice-leading resolution rules."""

    def test_dd_triad_doubling_rules(self):
        k = Key(PitchClass.C, Mode.MAJOR)
        chord_dd = Chord(function="DD")

        # In DD triad (D - F# - A in C major): Root D must be doubled, Third F# NEVER doubled!
        # Valid: Root doubled: Soprano D4 (62), Alto A3 (57), Tenor F#3 (54), Bass D3 (50)
        v_good = Voicing(soprano=62, alto=57, tenor=54, bass=50)
        viol_good = check_secondary_dominant_doubling(v_good, chord_dd, key=k)
        assert len(viol_good) == 0

        # Invalid: Third (F#) doubled! Soprano F#4 (66), Alto A3 (57), Tenor F#3 (54), Bass D3 (50)
        v_bad_third = Voicing(soprano=66, alto=57, tenor=54, bass=50)
        viol_bad = check_secondary_dominant_doubling(v_bad_third, chord_dd, key=k)
        assert len(viol_bad) > 0
        assert any(v.rule_id == "DOUBLING_SECONDARY_DOMINANT" for v in viol_bad)

        # Invalid: Root not doubled! (e.g. F#, A, A, D)
        v_bad_root = Voicing(soprano=69, alto=57, tenor=54, bass=50)  # A4, A3, F#3, D3 -> doubled fifth
        viol_bad_root = check_secondary_dominant_doubling(v_bad_root, chord_dd, key=k)
        assert len(viol_bad_root) > 0

    def test_dd7_resolution_to_k64(self):
        k = Key(PitchClass.C, Mode.MAJOR)
        c_dd7 = Chord(function="DD7")
        c_k64 = Chord(function="K64")

        # In C major:
        # DD7: D, F#, A, C
        # Soprano: C5 (72) -> 7th of DD7
        # Alto:    F#4 (66) -> secondary leading tone
        # Tenor:   A3 (57) -> 5th
        # Bass:    D3 (50) -> root
        v_dd7 = Voicing(soprano=72, alto=66, tenor=57, bass=50)

        # Resolution to K64 (G in bass, doubled G, C, E):
        # Soprano: C5 (72) -> B4 (71) (7th resolves down by step -1!)
        # Alto:    F#4 (66) -> G4 (67) (secondary leading tone resolves up by semitone +1!)
        # Tenor:   A3 (57) -> G3 (55)
        # Bass:    D3 (50) -> G2 (43) (or G3)
        v_k64 = Voicing(soprano=71, alto=67, tenor=55, bass=43)

        viol = check_secondary_dominant_resolution(v_dd7, v_k64, c_dd7, c_k64, key=k)
        assert len(viol) == 0

    def test_dd7_resolution_violations(self):
        k = Key(PitchClass.C, Mode.MAJOR)
        c_dd7 = Chord(function="DD7")
        c_k64 = Chord(function="K64")

        v_dd7 = Voicing(soprano=72, alto=66, tenor=57, bass=50)

        # 1. Secondary leading tone leaps away instead of stepping up to G or down to F:
        # Alto leaps F#4 (66) -> E4 (64) (-2 semitones!)
        v_bad_lt = Voicing(soprano=71, alto=64, tenor=55, bass=43)
        viol_lt = check_secondary_dominant_resolution(v_dd7, v_bad_lt, c_dd7, c_k64, key=k)
        assert len(viol_lt) > 0
        assert any(v.rule_id == "RESOLUTION_SECONDARY_DOMINANT" for v in viol_lt)

        # 2. Secondary seventh moves UP instead of resolving down by step:
        # Soprano C5 (72) -> D5 (74) (+2 UP!)
        v_bad_7th = Voicing(soprano=74, alto=67, tenor=55, bass=43)
        viol_7th = check_secondary_dominant_resolution(v_dd7, v_bad_7th, c_dd7, c_k64, key=k)
        assert len(viol_7th) > 0
        assert any(v.rule_id == "RESOLUTION_SECONDARY_DOMINANT" for v in viol_7th)

    def test_grammar_with_secondary_dominants(self):
        grammar = HarmonicGrammar(Key(PitchClass.C, Mode.MAJOR))

        # F#4 (66) must match DD and DD7 in C major!
        cands = grammar.get_compatible_chords_for_pitch(66)
        assert "DD" in cands or "DD7" in cands

        # Syntax transitions:
        # Valid: T -> DD, S -> DD, DD -> K64, DD -> D
        assert grammar.is_valid_syntax_transition("T", "DD")
        assert grammar.is_valid_syntax_transition("S", "DD")
        assert grammar.is_valid_syntax_transition("DD", "K64")
        assert grammar.is_valid_syntax_transition("DD7", "D")

        # Invalid regressions:
        # DD -> S forbidden!
        assert not grammar.is_valid_syntax_transition("DD", "S")
        assert not grammar.is_valid_syntax_transition("DD7", "II")
        # D -> DD regression forbidden!
        assert not grammar.is_valid_syntax_transition("D", "DD")
        assert not grammar.is_valid_syntax_transition("D7", "DD7")

    def test_complete_classical_modulation_end_to_end(self):
        """Verifies full classical modulation C-dur -> G-dur passes RuleEngine with zero hard violations."""
        engine = RuleEngine()
        c_dur = Key(PitchClass.C, Mode.MAJOR)
        g_dur = Key(PitchClass.G, Mode.MAJOR)

        pivots = find_pivot_chords(c_dur, g_dur)
        assert len(pivots) > 0
        assert pivots[0].source_function == "VI"
        assert pivots[0].target_function == "II"

        plan = build_modulation_plan(c_dur, g_dur, pivots[0])
        assert len(plan) == 6

        # Standard 4-part classical realization of C -> G modulation:
        voicings = [
            Voicing(72, 67, 64, 48),  # T (C-dur)
            Voicing(72, 69, 64, 45),  # VI (C-dur) = II (G-dur)
            Voicing(71, 67, 62, 50),  # K64 (G-dur)
            Voicing(69, 66, 60, 50),  # D7 (G-dur) - F# in alto
            Voicing(67, 67, 59, 43),  # T (G-dur)
        ]
        chords = [Chord("T"), Chord("VI"), Chord("K64"), Chord("D7"), Chord("T")]
        keys = [c_dur, c_dur, g_dur, g_dur, g_dur]

        prev_v = None
        for idx, (v, c, k) in enumerate(zip(voicings, chords, keys)):
            res = engine.validate(
                prev_voicing=prev_v,
                curr_voicing=v,
                prev_chord=chords[idx - 1] if idx > 0 else None,
                curr_chord=c,
                key=k,
                is_downbeat=(idx in (0, 2, 4)),
            )
            assert res.is_valid, f"Failed at modulation chord {idx} ({c.function}): {res.hard_violations}"
            assert not res.has_hard_violations
            prev_v = v
