"""
Macro Harmonic Syntax Engine and Period Grammar.
Generates structurally sound functional chord progressions (T, S, D, K64, etc.)
for a given soprano melody according to classical period form and Brigade syntax rules.
"""

from typing import Any, Sequence
from dataclasses import dataclass
from src.harmony.core.types import Key, Chord, parse_key
from src.harmony.rules.doubling import get_triad_tones
from src.harmony.rules.engine import check_syntax_rules

# All standard classical functions considered by the grammar
ALL_FUNCTIONS = [
    "T", "T6",
    "S", "S6",
    "D", "D6", "D7", "D65", "D43", "D2",
    "K64",
    "VI",
    "II", "II6", "II7", "II65",
    "VII", "VII6", "VII7",
    "III", "III6",
    "DD", "DD7",
]

DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2", "VII", "VII6", "VII7"}
PRIMARY_DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
LEADING_TONE_GROUP = {"VII", "VII6", "VII7"}
SUBDOMINANT_GROUP = {"S", "S6", "S64", "II", "II6", "II65", "II7"}
SECONDARY_DOMINANT_GROUP = {"DD", "DD7", "DD65", "DD43", "DD2"}


@dataclass
class MelodyNote:
    pitch: int
    duration: int = 4
    is_downbeat: bool = False
    is_cadence_point: bool = False
    phrase_boundary: bool = False


class HarmonicGrammar:
    """
    Formal Grammar and Plan Generator for classical four-part harmony.
    Enforces macro syntax:
    - Period structure (middle cadence -> D, final cadence -> K64 - D7 - T)
    - Functional circle (T -> S -> D -> T)
    - Strict prohibition of D -> S regression
    - Mandatory D43 -> T6 resolution
    - K64 on downbeat only
    """

    def __init__(self, key: Key | None = None):
        self.key = key or Key(tonic="C", mode="Major")

    def get_chord_pitch_classes(self, fn: str, key: Key | None = None) -> set[int]:
        """Returns the set of pitch classes belonging to the chord function."""
        k = key or self.key
        tonic_pc, mode = parse_key(k)
        root, third, fifth = get_triad_tones(fn, tonic_pc, mode)
        pcs = {root, third, fifth}
        fn_upper = fn.strip().upper()
        if fn_upper in ("D7", "D65", "D43", "D2"):
            pcs.add((tonic_pc + 5) % 12)
        elif fn_upper in ("DD7", "DD65", "DD43", "DD2"):
            pcs.add(tonic_pc % 12)
        elif fn_upper in ("II7", "II65"):
            pcs.add(tonic_pc % 12)
        elif fn_upper == "VII7":
            is_minor = "MINOR" in mode.upper() or fn.islower()
            pcs.add((tonic_pc + 8 if is_minor else tonic_pc + 9) % 12)
            if not is_minor:
                pcs.add((tonic_pc + 8) % 12)
        return pcs

    def get_compatible_chords_for_pitch(
        self,
        pitch: int,
        key: Key | None = None,
        is_downbeat: bool = False,
        is_final_cadence: bool = False,
        is_penultimate: bool = False,
        next_pitch: int | None = None,
    ) -> list[str]:
        """
        Returns all chord functions that can harmonically accommodate the soprano pitch.
        If next_pitch is provided, ensures that unstable tendency tones (like 7ths in soprano)
        can actually resolve smoothly without illegal leaps.
        """
        k = key or self.key
        tonic_pc, mode = parse_key(k)
        pc = pitch % 12
        compatible: list[str] = []

        is_minor = "MINOR" in mode.upper()
        tonic_tones = {tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12}
        can_step_down = (next_pitch is not None) and ((next_pitch - pitch) in (-1, -2))

        for fn in ALL_FUNCTIONS:
            # Metric rule: K64 cannot be on weak beat
            if fn == "K64" and not is_downbeat:
                continue

            # Position rule: Final cadence ending chord
            # If pitch matches tonic triad, authentic cadence ending must be T.
            # If pitch does not match tonic (e.g. degrees 2, 7), half cadence ending must be D.
            if is_final_cadence:
                if pc in tonic_tones:
                    if fn not in ("T", "t"):
                        continue
                else:
                    if fn not in ("D", "d"):
                        continue

            # Position rule: Penultimate chord in authentic cadence is typically D, D7, etc.
            # K64 CANNOT be penultimate immediately before final T, because K64 must resolve to D!
            if is_penultimate:
                next_in_tonic = (next_pitch is None) or ((next_pitch % 12) in tonic_tones)
                if next_in_tonic and fn in ("K64", "T64", "S64", "D2"):
                    continue

            # Dissonance resolution rule: If a 7th chord is chosen and the soprano note IS the 7th,
            # the soprano MUST step down (-1 or -2) into the next note. Leaps from the 7th are forbidden!
            if next_pitch is not None and not can_step_down:
                if fn in ("D7", "D65", "D43", "D2") and pc == (tonic_pc + 5) % 12:
                    continue
                if fn in ("DD7", "DD65", "DD43", "DD2") and pc == tonic_pc % 12:
                    continue
                if fn in ("II7", "II65") and pc == tonic_pc % 12:
                    continue
                if fn == "VII7" and pc in ((tonic_pc + 8) % 12, (tonic_pc + 9) % 12):
                    continue

            root, third, fifth = get_triad_tones(fn, tonic_pc, mode)
            allowed_pcs = {root, third, fifth}

            # Inversion doubling rules:
            # In D6 and D65, the bass has the leading tone (third).
            # Doubling the leading tone in the soprano is strictly forbidden!
            if fn in ("D6", "D65") and pc == third:
                continue

            # In D2 and D43, the bass has the 7th.
            # Doubling the 7th in soprano is strictly forbidden!
            if fn in ("D2", "D43") and pc == (tonic_pc + 5) % 12:
                continue
            if fn in ("DD2", "DD43") and pc == tonic_pc % 12:
                continue

            # Add 7th for seventh chords
            if fn in ("D7", "D65", "D43", "D2"):
                seventh = (tonic_pc + 5) % 12
                allowed_pcs.add(seventh)
            elif fn in ("DD7", "DD65", "DD43", "DD2"):
                seventh = tonic_pc % 12
                allowed_pcs.add(seventh)
            elif fn in ("II7", "II65"):
                seventh = tonic_pc % 12
                allowed_pcs.add(seventh)
            elif fn == "VII7":
                allowed_pcs.add((tonic_pc + 8 if is_minor else tonic_pc + 9) % 12)
                if not is_minor:
                    allowed_pcs.add((tonic_pc + 8) % 12)

            if pc in allowed_pcs:
                compatible.append(fn)

        # Cadential preference: before the final tonic the textbook wants a
        # dominant preparation (D/D7/D65/D43/D2/D6), not a plagal S/II.
        if is_penultimate and next_pitch is not None and (next_pitch % 12) in tonic_tones:
            cadential = [
                fn for fn in compatible
                if fn in ("D", "d", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2", "D6", "d6")
            ]
            if cadential:
                compatible = cadential

        return compatible

    def is_valid_syntax_transition(
        self,
        prev_fn: str,
        curr_fn: str,
        is_downbeat: bool = True,
        phrase_boundary: bool = False,
    ) -> bool:
        """
        Validates syntactic progression rules using unified RuleEngine check_syntax_rules:
        - No D -> S or D -> II regression (unless phrase_boundary=True)
        - D43 must go to T6 or T
        - D2 must go to T6
        - K64 must be followed by D or D7
        - Dominants cannot move to K64
        - Dominants cannot move to secondary dominants (D -> DD)
        - Secondary dominant (DD) must resolve to Dominant or K64, not S, II, T, or VI
        - D6 and D65 have leading tone in bass; cannot leap to T6 or VI
        - D7 cannot resolve to T6
        """
        # Unified check with RuleEngine syntax rules
        syntax_violations = check_syntax_rules(
            prev_chord=prev_fn,
            curr_chord=curr_fn,
            is_downbeat=is_downbeat,
            phrase_boundary=phrase_boundary,
        )
        if any(v.is_hard for v in syntax_violations):
            return False

        prev_upper = prev_fn.strip().upper()
        curr_upper = curr_fn.strip().upper()

        # D -> S and D -> II regression forbidden inside phrase (allowed at phrase boundary)
        if not phrase_boundary and (prev_upper in DOMINANT_GROUP and curr_upper in SUBDOMINANT_GROUP):
            return False

        # Dominants cannot move to K64 (D -> K64, D6 -> K64 is strictly forbidden; K64 resolves TO dominant)
        if prev_upper in DOMINANT_GROUP and curr_upper == "K64":
            return False

        # Dominant 7th chords cannot un-resolve back into dominant triad (D or D6)
        if prev_upper in ("D7", "D65", "D43", "D2") and curr_upper in ("D", "D6"):
            return False

        # Secondary dominant (DD) cannot resolve to subdominant, tonic, or VI
        if prev_upper in SECONDARY_DOMINANT_GROUP:
            if curr_upper in SUBDOMINANT_GROUP or curr_upper in ("T", "T6", "VI", "III", "III6"):
                return False

        # Dominant cannot regress to secondary dominant (D -> DD)
        if prev_upper in DOMINANT_GROUP and curr_upper in SECONDARY_DOMINANT_GROUP:
            return False

        # Dominant cannot regress to mediant (D -> III, D -> III6)
        if prev_upper in DOMINANT_GROUP and curr_upper in ("III", "III6"):
            return False

        # Mediant cannot move to K64, DD, or VII
        if prev_upper in ("III", "III6"):
            if curr_upper == "K64" or curr_upper in SECONDARY_DOMINANT_GROUP or curr_upper in ("VII", "VII6", "VII7"):
                return False

        # Root-position diminished VII triad (VII, VII53) is strictly forbidden in classical harmony
        if curr_upper in ("VII", "VII53"):
            return False

        # Supertonic seventh chords (II7, II65) can only resolve to Dominant group, K64, or T64
        if prev_upper in ("II7", "II65"):
            if curr_upper not in ("D", "D7", "D43", "D2", "D65", "D6", "K64", "T64"):
                return False

        # Leading-tone chords (VII6, VII7) can only resolve to Tonic or intra-functionally to Dominant
        if prev_upper in ("VII", "VII6", "VII7"):
            if curr_upper not in ("T", "T6", "T53", "T-6", "t", "t6", "D", "D7", "D65", "d", "d7"):
                return False

        # VII6 is a passing chord between tonic inversions (T-VII6-T6, T6-VII6-T); cannot follow subdominant
        if prev_upper in SUBDOMINANT_GROUP and curr_upper == "VII6":
            return False

        # D43 must resolve to T6 or T (and T53)
        if prev_upper == "D43" and curr_upper not in ("T6", "T", "T53"):
            return False

        # D2 must resolve strictly to T6
        if prev_upper == "D2" and curr_upper not in ("T6", "T-6"):
            return False

        # K64 must resolve to dominant triad or D7
        if prev_upper == "K64" and curr_upper not in ("D", "D7"):
            return False

        # Inversions with leading tone in bass (D6, D65) cannot leap to T6 or VI
        if prev_upper in ("D6", "D65") and curr_upper in ("T6", "VI"):
            return False

        # Root position D7 cannot resolve to T6
        if prev_upper == "D7" and curr_upper == "T6":
            return False

        return True

    def generate_plans(
        self,
        melody: Sequence[int | dict[str, Any]],
        key: Key | None = None,
        max_plans: int = 5,
    ) -> list[list[Chord]]:
        """
        Generates candidate functional plans for the entire melody.
        Backtracks through the compatible function lattice with beam search pruning.
        """
        k = key or self.key
        tonic_pc, mode = parse_key(k)
        n = len(melody)
        if n == 0:
            return []

        # Parse notes
        notes: list[MelodyNote] = []
        for i, m in enumerate(melody):
            if isinstance(m, dict):
                p = int(m["pitch"])
                db = bool(m.get("is_downbeat", False))
                pb = bool(m.get("phrase_boundary", m.get("is_phrase_boundary", False)))
            else:
                p = int(m)
                db = (i % 2 == 0)
                pb = False
            is_final = (i == n - 1)
            notes.append(MelodyNote(pitch=p, is_downbeat=db, is_cadence_point=is_final, phrase_boundary=pb))

        is_minor = "MINOR" in mode.upper()
        tonic_tones = {tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12}
        scale_pcs = set(k.scale_pcs)

        # Build candidate options per step
        step_candidates: list[list[str]] = []
        for i, note in enumerate(notes):
            is_final = (i == n - 1)
            is_penult = (i == n - 2)
            next_p = notes[i + 1].pitch if i < n - 1 else None
            cands = self.get_compatible_chords_for_pitch(
                pitch=note.pitch,
                key=k,
                is_downbeat=note.is_downbeat,
                is_final_cadence=is_final,
                is_penultimate=is_penult,
                next_pitch=next_p,
            )
            if not cands:
                # Fallback to any functions in ALL_FUNCTIONS whose tones contain note pitch
                cands = [
                    fn for fn in ALL_FUNCTIONS
                    if (note.pitch % 12) in self.get_chord_pitch_classes(fn, k)
                    and (fn != "K64" or note.is_downbeat)
                    and (not is_final or (fn in ("T", "t") if (note.pitch % 12) in tonic_tones else fn in ("D", "d")))
                ]
            # VII7 root position forces the bass onto the root (the leading tone);
            # a soprano sitting on the same leading tone would duplicate it, which
            # the canon forbids. VII6 stays available instead.
            lead_pc = (tonic_pc + 11) % 12
            if (note.pitch % 12) == lead_pc:
                cands = [fn for fn in cands if fn != "VII7"]
            step_candidates.append(cands)

        # Beam search for top functional progressions
        # State: (score, [chord_symbols])
        beams: list[tuple[float, list[str]]] = [(0.0, [])]

        for i, cands in enumerate(step_candidates):
            new_beams: list[tuple[float, list[str]]] = []
            is_downbeat = notes[i].is_downbeat
            is_pb = bool(notes[i].phrase_boundary)

            for score, path in beams:
                local_cands = cands
                if path and (notes[i].pitch % 12) not in scale_pcs and not is_downbeat:
                    prev_fn_nct = path[-1]
                    if prev_fn_nct not in cands:
                        # Chromatic passing tone on a weak beat: keeping the current
                        # harmony turns it into an NCT instead of a bogus altered chord.
                        local_cands = cands + [prev_fn_nct]
                for cand in local_cands:
                    if path:
                        prev_fn = path[-1]
                        if not self.is_valid_syntax_transition(prev_fn, cand, is_downbeat, phrase_boundary=is_pb):
                            continue
                        # Deceptive VI after a dominant must double the tonic third;
                        # that is impossible when the soprano already sits on the
                        # root of VI, so such a plan is a dead end.
                        if cand in ("VI", "vi") and prev_fn in (
                            "D", "d", "D7", "D65", "D43", "D2", "D6"
                        ):
                            vi_root_pc = (tonic_pc + (8 if is_minor else 9)) % 12
                            if (notes[i].pitch % 12) == vi_root_pc:
                                continue
                        # Second-relationship voice leading law (REPORT #54):
                        # In root-position S, bass is scale degree 4. Moving to dominant with soprano rising from 4 to 5
                        # (e.g. F4 -> G4 in C-dur) forces both outer voices to move in parallel into the octave/unison,
                        # mathematically guaranteeing parallel octaves (or parallel unisons).
                        if prev_fn in ("S", "s") and cand in DOMINANT_GROUP:
                            if (
                                (notes[i - 1].pitch % 12) == (tonic_pc + 5) % 12
                                and (notes[i].pitch % 12) == (tonic_pc + 7) % 12
                                and notes[i].pitch > notes[i - 1].pitch
                            ):
                                continue

                        # Root-position fifth-to-fifth law:
                        # If both prev_fn and cand are root-position triads (T, S, D, II, VI),
                        # and soprano has the fifth in both chords, outer voices form a pure 5th
                        # in both chords, mathematically forcing either parallel or contrary fifths.
                        root_triads = {"T", "S", "D", "II", "VI", "III", "t", "s", "d"}
                        if prev_fn in root_triads and cand in root_triads:
                            _, _, p_fifth = get_triad_tones(prev_fn, tonic_pc, mode)
                            _, _, c_fifth = get_triad_tones(cand, tonic_pc, mode)
                            if (notes[i - 1].pitch % 12) == p_fifth and (notes[i].pitch % 12) == c_fifth:
                                continue

                        # D6 / D65 has leading tone in bass which must resolve up by step into tonic.
                        # If soprano leaps up into the fifth of the tonic (|dS| > 2), direct motion into a 5th
                        # mathematically guarantees a forbidden hidden fifth (outer voices).
                        if prev_fn in ("D6", "D65") and cand in ("T", "t"):
                            if (notes[i].pitch - notes[i - 1].pitch) > 2 and (notes[i].pitch % 12) == (tonic_pc + 7) % 12:
                                continue

                        # Root-to-third outer voice octave law:
                        # Moving between root position and sextachord of the same function (T->T6, T6->T, S->S6, S6->S, D->D6, D6->D, III->III6, III6->III):
                        # Bass moves between root and third. If soprano also moves between root and third,
                        # outer voices start and end in octaves/unisons, mathematically guaranteeing parallel or contrary octaves.
                        same_triad_inversion = (
                            (prev_fn in ("T", "t") and cand in ("T6", "t6"))
                            or (prev_fn in ("T6", "t6") and cand in ("T", "t"))
                            or (prev_fn in ("S", "s") and cand in ("S6", "s6"))
                            or (prev_fn in ("S6", "s6") and cand in ("S", "s"))
                            or (prev_fn in ("D", "d") and cand in ("D6", "d6"))
                            or (prev_fn in ("D6", "d6") and cand in ("D", "d"))
                            or (prev_fn in ("III", "iii") and cand in ("III6", "iii6"))
                            or (prev_fn in ("III6", "iii6") and cand in ("III", "iii"))
                        )
                        if same_triad_inversion:
                            p_root, p_third, _ = get_triad_tones(prev_fn, tonic_pc, mode)
                            p_mel = notes[i - 1].pitch % 12
                            c_mel = notes[i].pitch % 12
                            if (p_mel in (p_root, p_third)) and (c_mel in (p_root, p_third)) and (p_mel != c_mel):
                                continue

                        # Outer voice parallel/hidden octaves law in D -> T resolution:
                        # If dominant moves to root tonic (T, t), and soprano rises scale degree 5 -> 1 (e.g. G4 -> C5),
                        # soprano moves up 5 -> 1 while bass also moves 5 -> 1 (G -> C).
                        # In root D, this mathematically guarantees parallel octaves (outer voices).
                        # In D6/D65, bass rises 7 -> 1 while soprano leaps 5 -> 1, mathematically guaranteeing hidden octaves.
                        if prev_fn in DOMINANT_GROUP and cand in ("T", "t"):
                            if (
                                (notes[i - 1].pitch % 12) == (tonic_pc + 7) % 12
                                and (notes[i].pitch % 12) == tonic_pc
                                and notes[i].pitch > notes[i - 1].pitch
                            ):
                                continue

                        # Heuristic transitions
                        trans_score = 0.0

                        # Opening wobble: a dominant chord in the second slot
                        # (T -> D6 -> T) reads as a functional hiccup, not an opening.
                        if i == 1 and cand in DOMINANT_GROUP:
                            trans_score -= 2.0

                        # Stepwise soprano motion: prioritize sextachords (S6, D6, II6, VII6, III6) (T13, BK-02)
                        soprano_step = abs(notes[i].pitch - notes[i - 1].pitch) in (1, 2)
                        if soprano_step and cand in ("S6", "s6", "D6", "d6", "II6", "VII6", "III6"):
                            trans_score += 2.5

                        # Descending leading tone (T16): C -> B (1 -> 7) descending into III or VII6
                        is_descending_leading = (
                            (notes[i - 1].pitch % 12 == tonic_pc)
                            and (notes[i].pitch % 12 == (tonic_pc + 11) % 12)
                            and (notes[i].pitch < notes[i - 1].pitch)
                        )
                        if is_descending_leading and cand in ("III", "III6", "VII6"):
                            trans_score += 4.0

                        # III progression reward: III -> S, S6, VI, II, II6, II65
                        if prev_fn in ("III", "iii", "III6", "iii6") and cand in ("S", "S6", "s", "s6", "VI", "vi", "II", "II6", "II65"):
                            trans_score += 3.0

                        # Reward standard cycles: T -> S (+1), S -> D (+2), D -> T (+2), K64 -> D7 (+3)
                        is_chromatic_note = (notes[i].pitch % 12) == (tonic_pc + 6) % 12
                        if prev_fn == "K64" and cand in ("D", "D7"):
                            trans_score += 3.0
                        elif prev_fn in SUBDOMINANT_GROUP and cand in PRIMARY_DOMINANT_GROUP:
                            trans_score += 2.0
                        elif prev_fn in SUBDOMINANT_GROUP and cand in LEADING_TONE_GROUP:
                            if (notes[i].pitch % 12) == (tonic_pc + 11) % 12:
                                trans_score += 4.0
                            else:
                                trans_score += 0.5
                        elif prev_fn in SUBDOMINANT_GROUP and cand in ("T", "T6"):
                            # Plagal return (S -> T)
                            trans_score += 1.5
                        elif cand in SECONDARY_DOMINANT_GROUP:
                            if is_chromatic_note:
                                trans_score += 4.0
                            elif prev_fn in SUBDOMINANT_GROUP:
                                trans_score += 0.5
                            else:
                                trans_score -= 1.0
                        elif prev_fn in SECONDARY_DOMINANT_GROUP and cand in ("K64", "D", "D7"):
                            trans_score += 2.0
                        elif prev_fn in PRIMARY_DOMINANT_GROUP and cand in ("T", "T6"):
                            trans_score += 2.0
                        elif prev_fn in LEADING_TONE_GROUP and cand in ("T", "T6"):
                            trans_score += 1.0
                        elif prev_fn in ("T", "T6", "VI", "vi") and cand in SUBDOMINANT_GROUP:
                            trans_score += 1.5
                        elif prev_fn in ("T", "T6") and cand in PRIMARY_DOMINANT_GROUP:
                            # Tonic opening into dominant (T -> D, T -> D7, etc.)
                            trans_score += 1.5
                        elif prev_fn in ("T", "T6") and cand in LEADING_TONE_GROUP:
                            trans_score += 0.5
                        # Penalize rapid repetitions, UNLESS soprano pitch is sustained/repeated
                        elif prev_fn == cand:
                            if notes[i].pitch == notes[i - 1].pitch:
                                trans_score += 1.0  # Harmonic sustenance on repeated melody note
                            else:
                                trans_score -= 1.0
                        # Chromatic passing tone on a weak beat: sustaining the
                        # previous harmony turns the foreign note into an NCT
                        # instead of forcing a bogus altered chord.
                        if (notes[i].pitch % 12) not in scale_pcs and not is_downbeat and cand == prev_fn:
                            trans_score += 4.0
                    else:
                        # Initial chord rule: Classical exercises cannot start on unstable/transitional chords
                        if cand in ("III", "III6", "VII", "VII6", "VII7", "II7", "II65", "K64", "D2", "DD", "DD7"):
                            continue
                        # Starting chord preference: T, T6, VI
                        if cand in ("T", "t"):
                            trans_score = 3.0
                        elif cand in ("T6", "t6"):
                            trans_score = 2.5
                        elif cand in ("VI", "vi"):
                            trans_score = 2.0
                        else:
                            trans_score = 0.0

                    new_beams.append((score + trans_score, path + [cand]))

            # Fallback 1: Relax voice leading heuristics with penalty, but strictly enforce is_valid_syntax_transition
            if not new_beams:
                is_final_step = (i == n - 1)
                for score, path in beams:
                    for cand in cands:
                        if is_final_step:
                            # The final cadence may only land on T/T6 (tonic pitch)
                            # or on D/VI (half/deceptive cadence).
                            if (notes[i].pitch % 12) in tonic_tones:
                                if cand not in ("T", "t", "T6", "t6"):
                                    continue
                            elif cand in ("VI", "vi"):
                                if not path or path[-1] not in ("D", "d", "D7"):
                                    continue
                            elif cand in ("D", "d", "D7"):
                                pass
                            else:
                                continue
                        if path:
                            prev_fn = path[-1]
                            if not self.is_valid_syntax_transition(prev_fn, cand, is_downbeat, phrase_boundary=is_pb):
                                continue
                            new_beams.append((score - 10.0, path + [cand]))
                        else:
                            if cand in ("III", "III6", "VII", "VII6", "VII7", "II7", "II65", "K64", "D2", "DD", "DD7"):
                                continue
                            new_beams.append((score - 10.0, [cand]))

            # Fallback 2: Check all functions containing the pitch that are valid transitions
            if not new_beams:
                is_final_step = (i == n - 1)
                for score, path in beams:
                    if path:
                        prev_fn = path[-1]
                        for fn in ALL_FUNCTIONS:
                            if fn == "K64" and (not is_downbeat or is_final_step):
                                continue
                            if is_final_step:
                                if (notes[i].pitch % 12) in tonic_tones:
                                    if fn not in ("T", "t", "T6", "t6"):
                                        continue
                                else:
                                    if fn in ("VI", "vi") and prev_fn in ("D", "d", "D7"):
                                        pass
                                    elif fn in ("D", "d", "D7"):
                                        pass
                                    else:
                                        continue
                            if (notes[i].pitch % 12) in self.get_chord_pitch_classes(fn, k):
                                if self.is_valid_syntax_transition(prev_fn, fn, is_downbeat, phrase_boundary=is_pb):
                                    new_beams.append((score - 20.0, path + [fn]))
                    else:
                        for fn in ALL_FUNCTIONS:
                            if fn in ("III", "III6", "VII", "VII6", "VII7", "II7", "II65", "K64", "D2", "DD", "DD7"):
                                continue
                            if (notes[i].pitch % 12) in self.get_chord_pitch_classes(fn, k):
                                new_beams.append((score - 20.0, [fn]))

            # Fallback 3: Sustain previous harmony across passing tone if valid
            if not new_beams:
                is_final_step = (i == n - 1)
                for score, path in beams:
                    if path:
                        prev_fn = path[-1]
                        if is_final_step:
                            # Final cadence must never be bypassed by sustaining a
                            # passing harmony (e.g. DD -> DD on the last note).
                            if (notes[i].pitch % 12) in tonic_tones:
                                if prev_fn not in ("T", "t", "T6", "t6"):
                                    continue
                            elif prev_fn in ("VI", "vi"):
                                if len(path) < 2 or path[-2] not in ("D", "d", "D7"):
                                    continue
                            elif prev_fn not in ("D", "d", "D7"):
                                continue
                        if prev_fn == "K64" and (not is_downbeat or (i == n - 1)):
                            continue
                        if self.is_valid_syntax_transition(prev_fn, prev_fn, is_downbeat, phrase_boundary=is_pb):
                            new_beams.append((score - 30.0, path + [prev_fn]))

            # Keep top beams
            new_beams.sort(key=lambda x: x[0], reverse=True)
            beams = new_beams[:max(max_plans * 4, 16)]

        # Extract top plans with deduplication
        results: list[list[Chord]] = []
        seen_paths: set[tuple[str, ...]] = set()
        for _, path in beams:
            t_path = tuple(path)
            if t_path not in seen_paths:
                seen_paths.add(t_path)
                results.append([Chord(function=fn) for fn in path])
            if len(results) >= max_plans:
                break

        # Inject textbook cadence templates (K64 -> D7 -> T, II6 -> D7 -> T, ...)
        # so the solver can actually choose a proper dominant cadence instead of
        # whatever the heuristic beam happened to leave behind.
        for path in self._cadence_template_plans(notes, k, max_plans):
            t_path = tuple(path)
            if t_path in seen_paths:
                continue
            seen_paths.add(t_path)
            results.append([Chord(function=fn) for fn in path])
            if len(results) >= max_plans:
                break

        return results

    _CADENCE_TEMPLATES: tuple[tuple[str, ...], ...] = (
        ("K64", "D7"),
        ("II6", "D7"),
        ("II65", "D7"),
        ("S6", "D7"),
        ("K64", "D"),
        ("II6", "K64", "D7"),
        ("D7",),
        ("D",),
    )

    def _cadence_template_plans(
        self,
        notes: list[MelodyNote],
        key: Key,
        max_plans: int,
    ) -> list[list[str]]:
        """Builds plans whose final cadence follows a textbook template.

        Template chords occupy positions n-1-Len .. n-2, the final tonic stays at
        n-1. The prefix is beam-searched with the regular compatibility rules, so
        the resulting plan is always syntactically valid end to end.
        """
        n = len(notes)
        if n < 3:
            return []
        tonic_pc, mode = parse_key(key)
        is_minor = "MINOR" in mode.upper()
        tonic_tones = {
            tonic_pc,
            (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12,
            (tonic_pc + 7) % 12,
        }
        if (notes[-1].pitch % 12) not in tonic_tones:
            return []

        plans: list[list[str]] = []
        seen: set[tuple[str, ...]] = set()

        for template in self._CADENCE_TEMPLATES:
            length = len(template)
            if length >= n:
                continue
            prefix_len = n - 1 - length

            compatible = True
            for j, fn in enumerate(template):
                idx = prefix_len + j
                pc = notes[idx].pitch % 12
                if pc not in self.get_chord_pitch_classes(fn, key):
                    compatible = False
                    break
                if fn == "K64" and not notes[idx].is_downbeat:
                    compatible = False
                    break
            if not compatible:
                continue

            beams: list[tuple[float, list[str]]] = [(0.0, [])]
            for i in range(prefix_len):
                nxt = notes[i + 1].pitch if i + 1 < n else None
                cands = self.get_compatible_chords_for_pitch(
                    pitch=notes[i].pitch,
                    key=key,
                    is_downbeat=notes[i].is_downbeat,
                    is_final_cadence=False,
                    is_penultimate=False,
                    next_pitch=nxt,
                )
                step: list[tuple[float, list[str]]] = []
                for score, path in beams:
                    for cand in cands:
                        if not path:
                            if cand in (
                                "III", "III6", "VII", "VII6", "VII7", "II7", "II65",
                                "K64", "D2", "DD", "DD7",
                            ):
                                continue
                        elif not self.is_valid_syntax_transition(
                            path[-1], cand, notes[i].is_downbeat
                        ):
                            continue
                        bonus = 1.0 if cand in ("S", "S6", "II", "II6") else 0.0
                        step.append((score + bonus, path + [cand]))
                if not step:
                    beams = []
                    break
                step.sort(key=lambda item: item[0], reverse=True)
                beams = step[:64]
            if not beams:
                continue

            for _, path in beams:
                full = path + list(template) + ["T"]
                if len(full) != n:
                    continue
                valid = True
                for i in range(1, n):
                    if not self.is_valid_syntax_transition(
                        full[i - 1], full[i], notes[i].is_downbeat
                    ):
                        valid = False
                        break
                if not valid:
                    continue
                signature = tuple(full)
                if signature in seen:
                    continue
                seen.add(signature)
                plans.append(full)
                if len(plans) >= max_plans:
                    return plans
        return plans
