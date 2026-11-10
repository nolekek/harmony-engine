"""
Macro Harmonic Syntax Engine and Period Grammar.
Generates structurally sound functional chord progressions (T, S, D, K64, etc.)
for a given soprano melody according to classical period form and Brigade syntax rules.
"""

from typing import Any, Sequence
from dataclasses import dataclass
from src.harmony.core.types import Key, Chord, parse_key
from src.harmony.rules.doubling import get_triad_tones

# All standard classical functions considered by the grammar
ALL_FUNCTIONS = [
    "T", "T6",
    "S", "S6",
    "D", "D6", "D7", "D65", "D43", "D2",
    "K64",
    "VI",
    "II6", "II",
    "DD", "DD7",
]

DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
SUBDOMINANT_GROUP = {"S", "S6", "S64", "II", "II6", "II65"}
SECONDARY_DOMINANT_GROUP = {"DD", "DD7", "DD65", "DD43", "DD2"}


@dataclass
class MelodyNote:
    pitch: int
    duration: int = 4
    is_downbeat: bool = False
    is_cadence_point: bool = False


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

            # Add 7th for dominant seventh chords
            if fn in ("D7", "D65", "D43", "D2"):
                seventh = (tonic_pc + 5) % 12
                allowed_pcs.add(seventh)
            elif fn in ("DD7", "DD65", "DD43", "DD2"):
                seventh = tonic_pc % 12
                allowed_pcs.add(seventh)

            if pc in allowed_pcs:
                compatible.append(fn)

        return compatible

    def is_valid_syntax_transition(
        self,
        prev_fn: str,
        curr_fn: str,
        is_downbeat: bool = False,
    ) -> bool:
        """
        Validates syntactic progression rules:
        - No D -> S or D -> II regression
        - D43 must go to T6 or T
        - D2 must go to T6
        - K64 must be followed by D or D7
        - Dominants cannot move to K64
        - Dominants cannot move to secondary dominants (D -> DD)
        - Secondary dominant (DD) must resolve to Dominant or K64, not S, II, T, or VI
        - D6 and D65 have leading tone in bass; cannot leap to T6 or VI
        - D7 cannot resolve to T6
        """
        prev_upper = prev_fn.strip().upper()
        curr_upper = curr_fn.strip().upper()

        # D -> S and D -> II regression forbidden
        if prev_upper in DOMINANT_GROUP and curr_upper in SUBDOMINANT_GROUP:
            return False

        # Dominants cannot move to K64 (D -> K64, D6 -> K64 is strictly forbidden; K64 resolves TO dominant)
        if prev_upper in DOMINANT_GROUP and curr_upper == "K64":
            return False

        # Dominant 7th chords cannot un-resolve back into dominant triad (D or D6)
        if prev_upper in ("D7", "D65", "D43", "D2") and curr_upper in ("D", "D6"):
            return False

        # Secondary dominant (DD) cannot resolve to subdominant, tonic, or VI
        if prev_upper in SECONDARY_DOMINANT_GROUP:
            if curr_upper in SUBDOMINANT_GROUP or curr_upper in ("T", "T6", "VI"):
                return False

        # Dominant cannot regress to secondary dominant (D -> DD)
        if prev_upper in DOMINANT_GROUP and curr_upper in SECONDARY_DOMINANT_GROUP:
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
            else:
                p = int(m)
                db = (i % 2 == 0)
            is_final = (i == n - 1)
            notes.append(MelodyNote(pitch=p, is_downbeat=db, is_cadence_point=is_final))

        is_minor = "MINOR" in mode.upper()
        tonic_tones = {tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12}

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
                    and (not is_final or (fn in ("T", "t") if (note.pitch % 12) in tonic_tones else fn in ("D", "d")))
                ]
            step_candidates.append(cands)

        # Beam search for top functional progressions
        # State: (score, [chord_symbols])
        beams: list[tuple[float, list[str]]] = [(0.0, [])]

        for i, cands in enumerate(step_candidates):
            new_beams: list[tuple[float, list[str]]] = []
            is_downbeat = notes[i].is_downbeat

            for score, path in beams:
                for cand in cands:
                    if path:
                        prev_fn = path[-1]
                        if not self.is_valid_syntax_transition(prev_fn, cand, is_downbeat):
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
                        root_triads = {"T", "S", "D", "II", "VI", "t", "s", "d"}
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
                        # Moving between root position and sextachord of the same function (T->T6, T6->T, S->S6, S6->S, D->D6, D6->D):
                        # Bass moves between root and third. If soprano also moves between root and third,
                        # outer voices start and end in octaves/unisons, mathematically guaranteeing parallel or contrary octaves.
                        same_triad_inversion = (
                            (prev_fn in ("T", "t") and cand in ("T6", "t6"))
                            or (prev_fn in ("T6", "t6") and cand in ("T", "t"))
                            or (prev_fn in ("S", "s") and cand in ("S6", "s6"))
                            or (prev_fn in ("S6", "s6") and cand in ("S", "s"))
                            or (prev_fn in ("D", "d") and cand in ("D6", "d6"))
                            or (prev_fn in ("D6", "d6") and cand in ("D", "d"))
                        )
                        if same_triad_inversion:
                            p_root, p_third, _ = get_triad_tones(prev_fn, tonic_pc, mode)
                            p_mel = notes[i - 1].pitch % 12
                            c_mel = notes[i].pitch % 12
                            if (p_mel in (p_root, p_third)) and (c_mel in (p_root, p_third)) and (p_mel != c_mel):
                                continue

                        # Heuristic transitions
                        trans_score = 0.0

                        # Stepwise soprano motion: prioritize sextachords (S6, D6, II6) (T13, BK-02)
                        soprano_step = abs(notes[i].pitch - notes[i - 1].pitch) in (1, 2)
                        if soprano_step and cand in ("S6", "s6", "D6", "d6", "II6"):
                            trans_score += 2.5

                        # Reward standard cycles: T -> S (+1), S -> D (+2), D -> T (+2), K64 -> D7 (+3)
                        is_chromatic_note = (notes[i].pitch % 12) == (tonic_pc + 6) % 12
                        if prev_fn == "K64" and cand in ("D", "D7"):
                            trans_score += 3.0
                        elif prev_fn in SUBDOMINANT_GROUP and cand in DOMINANT_GROUP:
                            trans_score += 2.0
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
                        elif prev_fn in DOMINANT_GROUP and cand in ("T", "T6"):
                            trans_score += 2.0
                        elif prev_fn in ("T", "T6") and cand in SUBDOMINANT_GROUP:
                            trans_score += 1.5
                        elif prev_fn in ("T", "T6") and cand in DOMINANT_GROUP:
                            # Tonic opening into dominant (T -> D, T -> D7, etc.)
                            trans_score += 1.5
                        # Penalize rapid repetitions, UNLESS soprano pitch is sustained/repeated
                        elif prev_fn == cand:
                            if notes[i].pitch == notes[i - 1].pitch:
                                trans_score += 1.0  # Harmonic sustenance on repeated melody note
                            else:
                                trans_score -= 1.0
                    else:
                        # Starting chord preference: T
                        trans_score = 3.0 if cand in ("T", "t") else 0.0

                    new_beams.append((score + trans_score, path + [cand]))

            # Fallback 1: Relax voice leading heuristics with penalty, but strictly enforce is_valid_syntax_transition
            if not new_beams:
                for score, path in beams:
                    for cand in cands:
                        if path:
                            prev_fn = path[-1]
                            if not self.is_valid_syntax_transition(prev_fn, cand, is_downbeat):
                                continue
                            new_beams.append((score - 10.0, path + [cand]))
                        else:
                            new_beams.append((score - 10.0, [cand]))

            # Fallback 2: Check all functions containing the pitch that are valid transitions
            if not new_beams:
                for score, path in beams:
                    if path:
                        prev_fn = path[-1]
                        for fn in ALL_FUNCTIONS:
                            if (notes[i].pitch % 12) in self.get_chord_pitch_classes(fn, k):
                                if self.is_valid_syntax_transition(prev_fn, fn, is_downbeat):
                                    new_beams.append((score - 20.0, path + [fn]))
                    else:
                        for fn in ALL_FUNCTIONS:
                            if (notes[i].pitch % 12) in self.get_chord_pitch_classes(fn, k):
                                new_beams.append((score - 20.0, [fn]))

            # Fallback 3: Sustain previous harmony across passing tone if valid
            if not new_beams:
                for score, path in beams:
                    if path:
                        prev_fn = path[-1]
                        if self.is_valid_syntax_transition(prev_fn, prev_fn, is_downbeat):
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

        return results
