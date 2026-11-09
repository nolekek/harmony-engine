"""
Chord tone doubling rules according to Brigade Harmony textbook.
Enforces root doubling in main triads (T, S, D), bass doubling in K64,
and third doubling in deceptive cadence (VI after D/D7).
"""

from typing import Any
from collections import Counter
from src.harmony.core.types import (
    RuleViolation,
    to_satb,
    parse_key,
    parse_chord_symbol,
)


def get_triad_tones(symbol: str, tonic_pc: int, mode: str) -> tuple[int, int, int]:
    """
    Returns (root_pc, third_pc, fifth_pc) for the given chord function.
    Supports all standard inversions and extensions (D7, D43, K64, S6, T6, II6, VI, etc.).
    """
    is_minor = "MINOR" in mode or symbol.islower()
    sym_upper = symbol.strip().upper()

    if sym_upper.startswith("K64"):
        # Cadential 6/4 is tonic chord tones over fifth degree (dominant bass)
        root = tonic_pc
        third = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
        fifth = (tonic_pc + 7) % 12
        return root, third, fifth

    if sym_upper.startswith("T"):
        root = tonic_pc
        third = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
        fifth = (tonic_pc + 7) % 12
        return root, third, fifth

    if sym_upper.startswith("S"):
        root = (tonic_pc + 5) % 12
        third = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
        fifth = tonic_pc
        return root, third, fifth

    if sym_upper.startswith("D"):
        root = (tonic_pc + 7) % 12
        # Dominant in both major and harmonic minor has major third (leading tone)
        third = (tonic_pc + 11) % 12
        fifth = (tonic_pc + 2) % 12
        return root, third, fifth

    if sym_upper.startswith("II"):
        root = (tonic_pc + 2) % 12
        third = (tonic_pc + 5) % 12
        fifth = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
        return root, third, fifth

    if sym_upper.startswith("VI"):
        root = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
        third = tonic_pc  # Third of VI is always the tonic!
        fifth = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
        return root, third, fifth

    if sym_upper.startswith("VII"):
        root = (tonic_pc + 11) % 12
        third = (tonic_pc + 2) % 12
        fifth = (tonic_pc + 5) % 12
        return root, third, fifth

    # Fallback to tonic
    return tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12


def check_main_triad_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
    prev_chord: Any = None,
) -> list[RuleViolation]:
    """
    In root-position main triads (T, S, D, t, s), the root (prima) must be doubled.
    Doubling the third is strictly forbidden, EXCEPT when resolving directly from VII7,
    where doubling the third in T is mandatory by Brigade rules to avoid parallel fifths.
    """
    sym = parse_chord_symbol(chord)
    if sym not in ("T", "S", "D", "t", "s"):
        return []

    # Check if coming from VII7 resolution: in VII7 -> T, doubling the third of T is mandatory!
    prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""
    if sym in ("T", "t") and prev_sym.startswith("VII"):
        return []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)

    satb = to_satb(voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    violations: list[RuleViolation] = []

    # Hard prohibition: never double the third in main root-position triads
    if counts[third] >= 2:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_MAIN_TRIAD_ROOT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Forbidden doubling of third in main triad '{sym}' "
                    f"(third PC {third} doubled {counts[third]} times)"
                ),
            )
        )

    # Standard requirement: root must be doubled (multiplicity >= 2)
    if counts[root] < 2:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_MAIN_TRIAD_ROOT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Root not doubled in main triad '{sym}' "
                    f"(root PC {root} present {counts[root]} times)"
                ),
            )
        )

    return violations


def check_k64_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    In cadential six-four chord (K64), the bass note (scale degree 5 / fifth of triad)
    must strictly be doubled.
    """
    sym = parse_chord_symbol(chord)
    if sym != "K64":
        return []

    satb = to_satb(voicing)
    bass_pc = satb[3] % 12
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    violations: list[RuleViolation] = []
    if counts[bass_pc] < 2:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_K64_BASS_ONLY",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In cadential six-four chord (K64), bass note (PC {bass_pc}) "
                    f"must be strictly doubled (found {counts[bass_pc]} times)"
                ),
            )
        )

    return violations


def check_deceptive_vi_doubling(
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    In deceptive cadence (D -> VI or D7 -> VI), the third of the VI triad
    (which is scale degree I / tonic pitch class) must strictly be doubled.
    """
    if prev_chord is None or curr_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord)
    curr_sym = parse_chord_symbol(curr_chord)

    is_dominant = prev_sym in ("D", "D7", "D65", "D43", "D2", "D6")
    is_vi = curr_sym in ("VI", "vi")

    if not (is_dominant and is_vi):
        return []

    tonic_pc, _ = parse_key(key) if key is not None else (0, "MAJOR")
    satb = to_satb(curr_voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    violations: list[RuleViolation] = []
    if counts[tonic_pc] < 2:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_DECEPTIVE_VI_THIRD",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In deceptive cadence ({prev_sym} -> {curr_sym}), the third of VI "
                    f"(tonic degree I, PC {tonic_pc}) must strictly be doubled "
                    f"(found {counts[tonic_pc]} times)"
                ),
            )
        )

    return violations


def check_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
    prev_chord: Any = None,
) -> list[RuleViolation]:
    """
    Runs all doubling validation checks relevant to the given chord and context.
    """
    violations = []
    violations.extend(check_main_triad_doubling(voicing, chord, key=key, prev_chord=prev_chord))
    violations.extend(check_k64_doubling(voicing, chord, key=key))
    if prev_chord is not None:
        violations.extend(check_deceptive_vi_doubling(voicing, prev_chord, chord, key=key))
    return violations
