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
    prev_chord: Any = None,
    is_final_chord: bool = False,
) -> list[Voicing]:
    """
    Generates all statically valid SATB voicings for a given soprano pitch and chord.

    Constraints enforced during generation:
    1. Pitch ranges:
       - S: 60..81 (extended 59..83)
       - A: 55..74 (extended 53..75)
       - T: 48..67 (extended 46..69)
       - B: 40..60 (extended 36..60)
    2. Voice ordering (no voice crossing):
       S >= A >= T >= B
    3. Textural spacing limits:
       S - A <= 12
       A - T <= 12
       T - B <= 24
    4. Chord tone membership:
       Every voice pitch must be one of the permitted pitch classes for the chord.
    5. Doubling and distribution rules:
       - Main triads (T, S, D in 5/3): root doubled, third doubling strictly forbidden.
       - K64: bass (fifth of chord) strictly doubled.
       - VI (in deceptive cadence): third strictly doubled.
       - Seventh chords: complete (1-3-5-7) or incomplete (doubled root, 3, 7).
       - Inversions: bass note strictly matches required factor (5/3: root; 6: 3rd; 6/4: 5th; 6/5: 3rd; 4/3 & 2: 7th).
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

    sym_clean = chord_sym.strip().upper().replace("/", "")
    is_seventh = (
        (hasattr(chord, "is_seventh") and chord.is_seventh)
        or any(k in sym_clean for k in ("7", "65", "43"))
        or sym_clean.endswith("2")
        or sym_clean in ("D2", "DD2", "II2", "VII2")
    )
    if is_seventh and not (sym_clean.startswith("K") or "64" in sym_clean):
        if sym_clean.startswith("DD") or sym_clean.startswith("DV"):
            seventh_pc = tonic_pc % 12
            allowed_pcs.add(seventh_pc)
        elif sym_clean.startswith("VII"):
            # diminished 7th in minor/harmonic major (deg 6 = +8), or natural major (+9)
            allowed_pcs.add((tonic_pc + 8) % 12)
            allowed_pcs.add((tonic_pc + 9) % 12)
        elif sym_clean.startswith("II"):
            seventh_pc = tonic_pc % 12
            allowed_pcs.add(seventh_pc)
        elif sym_clean.startswith("VI"):
            seventh_pc = (tonic_pc + 7) % 12
            allowed_pcs.add(seventh_pc)
        elif sym_clean.startswith("IV") or sym_clean.startswith("S"):
            seventh_pc = (tonic_pc + 3 if ("MINOR" in mode or sym_clean.islower()) else tonic_pc + 4) % 12
            allowed_pcs.add(seventh_pc)
        else:
            seventh_pc = (tonic_pc + 5) % 12
            allowed_pcs.add(seventh_pc)

    # Check that soprano belongs to chord
    if soprano_pitch % 12 not in allowed_pcs:
        return []

    # Inversion bass pitch class requirement
    # 5/3: root; 6: third; 6/4: fifth; 7: root; 6/5: third; 4/3: fifth/seventh; 2: seventh
    required_bass_pc = None
    if hasattr(chord, "bass_pitch_class") and chord.bass_pitch_class is not None:
        b_val = chord.bass_pitch_class
        required_bass_pc = int(b_val.value if hasattr(b_val, "value") else b_val) % 12
    elif "64" in sym_clean or sym_clean.startswith("K"):
        required_bass_pc = fifth_pc
    elif "65" in sym_clean:
        required_bass_pc = third_pc
    elif "43" in sym_clean:
        required_bass_pc = fifth_pc
    elif sym_clean.endswith("2") or sym_clean in ("D2", "DD2", "II2", "VII2"):
        required_bass_pc = seventh_pc
    elif "6" in sym_clean:
        required_bass_pc = third_pc
    else:
        # Root position (5/3, 7): bass MUST be the root of the chord
        required_bass_pc = root_pc

    candidates: list[Voicing] = []

    # Find valid Alto pitches (strict order S > A):
    alto_low = max(a_min, soprano_pitch - 12)
    alto_high = min(a_max, soprano_pitch - 1)

    for a in range(alto_low, alto_high + 1):
        if a % 12 not in allowed_pcs:
            continue

        # Find valid Tenor pitches (strict order A > T):
        tenor_low = max(t_min, a - 12)
        tenor_high = min(t_max, a - 1)

        for t in range(tenor_low, tenor_high + 1):
            if t % 12 not in allowed_pcs:
                continue

            # Find valid Bass pitches (strict order T > B):
            bass_low = max(b_min, t - 24)
            bass_high = min(b_max, t - 1)

            for b in range(bass_low, bass_high + 1):
                if required_bass_pc is not None and (b % 12 != required_bass_pc):
                    continue
                if b % 12 not in allowed_pcs:
                    continue

                v = Voicing(soprano=soprano_pitch, alto=a, tenor=t, bass=b)

                # Check doublings via doubling validator
                doubling_violations = check_doubling(
                    v,
                    chord=chord,
                    key=key,
                    prev_chord=prev_chord,
                    is_final_chord=is_final_chord,
                )
                if any(viol.is_hard for viol in doubling_violations):
                    continue

                candidates.append(v)

    return candidates
