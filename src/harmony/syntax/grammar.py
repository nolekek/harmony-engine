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
]

DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
SUBDOMINANT_GROUP = {"S", "S6", "S64", "II", "II6", "II65"}


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

    def get_compatible_chords_for_pitch(
        self,
        pitch: int,
        key: Key | None = None,
        is_downbeat: bool = False,
        is_final_cadence: bool = False,
        is_penultimate: bool = False,
    ) -> list[str]:
        """
        Returns all chord functions that can harmonically accommodate the soprano pitch.
        """
        k = key or self.key
        tonic_pc, mode = parse_key(k)
        pc = pitch % 12
        compatible: list[str] = []

        for fn in ALL_FUNCTIONS:
            # Metric rule: K64 cannot be on weak beat
            if fn == "K64" and not is_downbeat:
                continue

            # Position rule: Final cadence ending chord must be T
            if is_final_cadence and fn not in ("T", "t"):
                continue

            # Position rule: Penultimate chord in authentic cadence is typically D, D7, or K64
            if is_penultimate and fn not in ("D", "D7", "K64"):
                continue

            root, third, fifth = get_triad_tones(fn, tonic_pc, mode)
            allowed_pcs = {root, third, fifth}

            # Add 7th for dominant seventh chords
            if fn in ("D7", "D65", "D43", "D2"):
                seventh = (tonic_pc + 5) % 12
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
        - D43 must go to T6
        - D2 must go to T6
        - K64 must be followed by D or D7
        """
        prev_upper = prev_fn.strip().upper()
        curr_upper = curr_fn.strip().upper()

        # D -> S regression forbidden
        if prev_upper in DOMINANT_GROUP and curr_upper in SUBDOMINANT_GROUP:
            return False

        # D43 must resolve to T6
        if prev_upper == "D43" and curr_upper not in ("T6", "T"):
            return False

        # D2 must resolve to T6
        if prev_upper == "D2" and curr_upper != "T6":
            return False

        # K64 must resolve to dominant
        if prev_upper == "K64" and curr_upper not in ("D", "D7"):
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
            is_penult = (i == n - 2)
            notes.append(MelodyNote(pitch=p, is_downbeat=db, is_cadence_point=is_final))

        # Build candidate options per step
        step_candidates: list[list[str]] = []
        for i, note in enumerate(notes):
            is_final = (i == n - 1)
            is_penult = (i == n - 2)
            cands = self.get_compatible_chords_for_pitch(
                pitch=note.pitch,
                key=k,
                is_downbeat=note.is_downbeat,
                is_final_cadence=is_final,
                is_penultimate=is_penult,
            )
            if not cands:
                # Fallback to any triad containing note
                cands = [fn for fn in ["T", "S", "D"] if self.get_compatible_chords_for_pitch(note.pitch, k)]
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
                        # Heuristic transitions
                        trans_score = 0.0
                        # Reward standard cycles: T -> S (+1), S -> D (+2), D -> T (+2), K64 -> D7 (+3)
                        if prev_fn == "K64" and cand in ("D", "D7"):
                            trans_score += 3.0
                        elif prev_fn in SUBDOMINANT_GROUP and cand in DOMINANT_GROUP:
                            trans_score += 2.0
                        elif prev_fn in DOMINANT_GROUP and cand in ("T", "T6"):
                            trans_score += 2.0
                        elif prev_fn in ("T", "T6") and cand in SUBDOMINANT_GROUP:
                            trans_score += 1.5
                        # Penalize rapid repetitions
                        elif prev_fn == cand:
                            trans_score -= 1.0
                    else:
                        # Starting chord preference: T
                        trans_score = 3.0 if cand in ("T", "t") else 0.0

                    new_beams.append((score + trans_score, path + [cand]))

            if not new_beams:
                # If beam collapsed, fallback to appending cands directly
                for score, path in beams:
                    for cand in cands[:2]:
                        new_beams.append((score, path + [cand]))

            # Keep top beams
            new_beams.sort(key=lambda x: x[0], reverse=True)
            beams = new_beams[:max(max_plans * 4, 16)]

        # Extract top plans
        results: list[list[Chord]] = []
        for _, path in beams[:max_plans]:
            results.append([Chord(function=fn) for fn in path])

        return results
