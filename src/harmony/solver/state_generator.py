"""
Fast combinatorial state generator for four-part SATB voicings.
Generates all statically admissible voicings for a given soprano melody note and chord,
pruning forbidden doublings and textural gaps before passing states to the DP graph.
"""

from typing import Any, Sequence
from src.harmony.core.types import Voicing, Key, Chord, to_satb, parse_key
from src.harmony.rules.spacing import STANDARD_VOICE_RANGES, EXTENDED_VOICE_RANGES
from src.harmony.rules.doubling import get_triad_tones, check_doubling


def generate_candidate_voicings(
    soprano_pitch: int,
    chord: Any,
    key: Any = None,
    allow_extended_ranges: bool = False,
) -> list[Voicing]:
    """
    Generates all statically valid SATB voicings for a given soprano pitch and chord.

    Constraints enforced during generation:
    1. Pitch ranges:
       - S: 60..81
       - A: 55..74
       - T: 48..67
       - B: 40..60
    2. Voice ordering (no voice crossing):
       S >= A >= T >= B
    3. Textural spacing limits:
       S - A <= 12
       A - T <= 12
       T - B <= 24
    4. Chord tone membership:
       Every voice pitch must be one of the permitted pitch classes for the chord.
    5. Doubling rules:
       - Main triads (T, S, D in 5/3): root doubled, third doubling strictly forbidden.
       - K64: bass (fifth of chord) strictly doubled.
       - VI (in deceptive cadence): third strictly doubled.
       - Seventh chords: complete (1-3-5-7) or incomplete (doubled root, 3, 7).
    """
    ranges = EXTENDED_VOICE_RANGES if allow_extended_ranges else STANDARD_VOICE_RANGES
    s_min, s_max = ranges[0]
    a_min, a_max = ranges[1]
    t_min, t_max = ranges[2]
    b_min, b_max = ranges[3]

    if not (s_min <= soprano_pitch <= s_max):
        return []

    # Get allowed pitch classes and chord factors
    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    chord_sym = chord.function if hasattr(chord, "function") else str(chord)
    root_pc, third_pc, fifth_pc = get_triad_tones(chord_sym, tonic_pc, mode)
    allowed_pcs = {root_pc, third_pc, fifth_pc}

    is_seventh = hasattr(chord, "is_seventh") and chord.is_seventh
    seventh_pc = None
    if is_seventh or "7" in chord_sym or "65" in chord_sym or "43" in chord_sym or "2" in chord_sym:
        sym_clean = chord_sym.strip().upper().replace("/", "")
        if sym_clean.startswith("DD") or sym_clean.startswith("D7V") or sym_clean.startswith("DV"):
            # For double dominant 7th, 7th is tonic (scale degree I)
            seventh_pc = tonic_pc % 12
        elif "II" in sym_clean:
            seventh_pc = (tonic_pc + 7) % 12
        elif "VI" in sym_clean:
            seventh_pc = (tonic_pc + 2) % 12
        elif "IV" in sym_clean:
            seventh_pc = (tonic_pc + 10) % 12
        else:
            # For dominant 7th, 7th is IV degree (tonic + 5)
            seventh_pc = (tonic_pc + 5) % 12
        allowed_pcs.add(seventh_pc)

    # Check that soprano belongs to chord
    if soprano_pitch % 12 not in allowed_pcs:
        return []

    # Inversion bass pitch class requirement
    # 5/3: root; 6: third; 6/4: fifth; 7: root; 6/5: third; 4/3: fifth/seventh; 2: seventh
    required_bass_pc = None
    if chord_sym in ("K64", "T64", "S64", "D64", "s64", "t64"):
        required_bass_pc = fifth_pc
    elif chord_sym in ("T6", "S6", "D6", "s6", "t6", "II6", "ii6"):
        required_bass_pc = third_pc
    elif chord_sym in ("D43",):
        required_bass_pc = (tonic_pc + 5) % 12  # 7th in bass per Brigade D43 convention
    elif chord_sym in ("D2",):
        required_bass_pc = (tonic_pc + 5) % 12  # 7th in bass
    elif chord_sym in ("D65",):
        required_bass_pc = third_pc

    candidates: list[Voicing] = []

    # Find valid Alto pitches:
    # A in [max(a_min, soprano_pitch - 12), min(a_max, soprano_pitch)]
    alto_low = max(a_min, soprano_pitch - 12)
    alto_high = min(a_max, soprano_pitch)

    for a in range(alto_low, alto_high + 1):
        if a % 12 not in allowed_pcs:
            continue

        # Find valid Tenor pitches:
        # T in [max(t_min, a - 12), min(t_max, a)]
        tenor_low = max(t_min, a - 12)
        tenor_high = min(t_max, a)

        for t in range(tenor_low, tenor_high + 1):
            if t % 12 not in allowed_pcs:
                continue

            # Find valid Bass pitches:
            # B in [max(b_min, t - 24), min(b_max, t)]
            bass_low = max(b_min, t - 24)
            bass_high = min(b_max, t)

            for b in range(bass_low, bass_high + 1):
                if required_bass_pc is not None and (b % 12 != required_bass_pc):
                    continue
                if b % 12 not in allowed_pcs:
                    continue

                v = Voicing(soprano=soprano_pitch, alto=a, tenor=t, bass=b)

                # Check doublings via doubling validator
                doubling_violations = check_doubling(v, chord=chord, key=key)
                if any(viol.is_hard for viol in doubling_violations):
                    continue

                candidates.append(v)

    return candidates
