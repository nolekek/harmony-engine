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
    is_minor = "MINOR" in mode.upper() or symbol.islower()
    sym_upper = symbol.strip().upper()

    if sym_upper.startswith("DD") or sym_upper in ("D7V", "DV", "D7/V", "D/V"):
        # Double Dominant (D of V): Root = II degree, Third = raised IV (secondary leading tone), Fifth = VI degree
        root = (tonic_pc + 2) % 12
        third = (tonic_pc + 6) % 12
        fifth = (tonic_pc + 9) % 12
        return root, third, fifth

    if "D7II" in sym_upper or "D/II" in sym_upper or "D7/II" in sym_upper:
        # Dominant to II: Root = VI degree, Third = raised I degree, Fifth = III degree
        root = (tonic_pc + 9) % 12
        third = (tonic_pc + 1) % 12
        fifth = (tonic_pc + 4) % 12
        return root, third, fifth

    if "D7VI" in sym_upper or "D/VI" in sym_upper or "D7/VI" in sym_upper:
        # Dominant to VI: Root = III degree in major, Third = raised V degree, Fifth = VII degree
        root = (tonic_pc + 4) % 12
        third = (tonic_pc + 8) % 12
        fifth = (tonic_pc + 11) % 12
        return root, third, fifth

    if "D7IV" in sym_upper or "D/IV" in sym_upper or "D7/IV" in sym_upper:
        # Dominant to IV: Root = I degree, Third = III degree, Fifth = V degree
        root = tonic_pc
        third = (tonic_pc + 4) % 12
        fifth = (tonic_pc + 7) % 12
        return root, third, fifth

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

    if sym_upper.startswith("III"):
        root = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
        third = (tonic_pc + 7) % 12
        fifth = (tonic_pc + 10 if is_minor else tonic_pc + 11) % 12
        return root, third, fifth

    if sym_upper.startswith("II"):
        root = (tonic_pc + 2) % 12
        third = (tonic_pc + 5) % 12
        fifth = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
        return root, third, fifth

    if sym_upper.startswith("VII"):
        root = (tonic_pc + 11) % 12
        third = (tonic_pc + 2) % 12
        fifth = (tonic_pc + 5) % 12
        return root, third, fifth

    if sym_upper.startswith("VI"):
        root = (tonic_pc + 8 if is_minor else tonic_pc + 9) % 12
        third = tonic_pc  # Third of VI is always the tonic!
        fifth = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
        return root, third, fifth

    # Fallback to tonic
    return tonic_pc, (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12, (tonic_pc + 7) % 12


TRIAD_SYMBOLS = {
    "T", "S", "D", "VI", "II", "III",
    "t", "s", "d", "vi", "ii", "iii",
    "T53", "S53", "D53", "VI53", "II53", "III53",
    "t53", "s53", "d53", "vi53", "ii53", "iii53",
}


def check_triad_completeness(
    voicing: Any,
    chord: Any,
    key: Any = None,
    is_final_chord: bool = False,
) -> list[RuleViolation]:
    """
    Checks triad completeness for root-position triads (T/S/D/VI/II/III and minor variants):
    - Third is strictly required in ALL positions, including final chord (CHORD_THIRD_MISSING).
    - Fifth is required in non-final chords (CHORD_FIFTH_MISSING).
    - Incomplete triad (tripled root with third, omitting fifth) is permissible ONLY if is_final_chord=True.
    """
    sym = parse_chord_symbol(chord).strip().replace("/", "")
    if sym not in TRIAD_SYMBOLS:
        return []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)

    satb = to_satb(voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    violations: list[RuleViolation] = []

    # 1. Third is mandatory in ALL triads (including final chord!)
    if counts[third] == 0:
        violations.append(
            RuleViolation(
                rule_id="CHORD_THIRD_MISSING",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Triad '{sym}' is missing mandatory third (PC {third})",
            )
        )

    # 2. Fifth requirement
    if counts[fifth] == 0:
        # Incomplete triad allowed ONLY on final chord with tripled root and present third
        if is_final_chord and counts[root] == 3 and counts[third] == 1 and sym in ("T", "t", "T53", "t53"):
            pass  # Allowed canonical incomplete final tonic triad
        else:
            violations.append(
                RuleViolation(
                    rule_id="CHORD_FIFTH_MISSING",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=f"Triad '{sym}' is missing fifth (PC {fifth})",
                )
            )

    return violations


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

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)

    satb = to_satb(voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    # Check if coming from VII7 resolution: in VII7 -> T, doubling the third of T is mandatory!
    prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""
    if sym in ("T", "t") and prev_sym.startswith("VII"):
        if counts[third] < 2:
            return [
                RuleViolation(
                    rule_id="DOUBLING_MAIN_TRIAD_ROOT",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In resolution of {prev_sym} to {sym}, the third of the tonic triad "
                        f"(PC {third}) must strictly be doubled (found {counts[third]} times)"
                    ),
                )
            ]
        return []

    violations: list[RuleViolation] = []

    # Hard prohibition: never double the third in main root-position triads
    if counts[third] >= 2:
        v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == third)
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_MAIN_TRIAD_ROOT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Forbidden doubling of third in main triad '{sym}' "
                    f"(third PC {third} doubled {counts[third]} times)"
                ),
                voices=v_idx,
            )
        )

    # If soprano is a non-chord tone (NCT), the lower 3 voices form a complete triad
    # (1 root, 1 third, 1 fifth), so doubling of the root in 4 voices is not possible.
    soprano_pc = satb[0] % 12
    if soprano_pc not in (root, third, fifth):
        return violations

    # Standard requirement: root must be doubled (multiplicity >= 2)
    if counts[root] < 2:
        v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == root)
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_MAIN_TRIAD_ROOT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Root not doubled in main triad '{sym}' "
                    f"(root PC {root} present {counts[root]} times)"
                ),
                voices=v_idx,
            )
        )

    return violations


def check_k64_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    In cadential six-four chord (K64):
    - The bass must strictly be scale degree V (fifth of the key / dominant pitch class).
    - The bass note (scale degree V) must strictly be doubled.
    - Other tones (root I, third III) may not be doubled.
    """
    sym = parse_chord_symbol(chord)
    if sym != "K64":
        return []

    satb = to_satb(voicing)
    bass_pc = satb[3] % 12
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    degree_v_pc = (tonic_pc + 7) % 12

    violations: list[RuleViolation] = []

    # 1. Bass MUST be scale degree V (PC 7 in C-dur)
    if bass_pc != degree_v_pc:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_K64_BASS_ONLY",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In cadential six-four chord (K64), bass must be scale degree V "
                    f"(PC {degree_v_pc}), got PC {bass_pc}"
                ),
                voices=(3,),
            )
        )

    # 2. Bass (scale degree V) MUST be doubled
    if counts[degree_v_pc] < 2:
        v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == degree_v_pc)
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_K64_BASS_ONLY",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In cadential six-four chord (K64), bass note (scale degree V, PC {degree_v_pc}) "
                    f"must be strictly doubled (found {counts[degree_v_pc]} times)"
                ),
                voices=v_idx,
            )
        )

    # 3. Third of tonic (scale degree III) must NOT be doubled
    is_minor = "MINOR" in mode
    third_pc = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
    if counts[third_pc] > 1:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_K64_BASS_ONLY",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In cadential six-four chord (K64), third (scale degree III, PC {third_pc}) "
                    f"cannot be doubled (found {counts[third_pc]} times)"
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
        v_idx = tuple(i for i, p in enumerate(satb) if p % 12 == tonic_pc)
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
                voices=v_idx,
            )
        )

    return violations


def check_secondary_dominant_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    In Secondary Dominant triads (e.g. DD 5/3):
    The root (prima) must be doubled.
    Doubling the third (secondary leading tone) is strictly forbidden!
    """
    sym = parse_chord_symbol(chord).strip().upper().replace("/", "")
    if not (sym == "DD" or sym == "DV"):
        return []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)

    satb = to_satb(voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    violations: list[RuleViolation] = []

    # Third (secondary leading tone) NEVER doubled
    if counts[third] > 1:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_SECONDARY_DOMINANT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In DD triad, the third (secondary leading tone, PC {third}) "
                    f"must NEVER be doubled (found {counts[third]} times)"
                ),
            )
        )

    # Root must be doubled
    if counts[root] < 2:
        violations.append(
            RuleViolation(
                rule_id="DOUBLING_SECONDARY_DOMINANT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In DD triad, the root (PC {root}) must strictly be doubled "
                    f"(found {counts[root]} times)"
                ),
            )
        )

    return violations


def check_sextaccord_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
    prev_chord: Any = None,
) -> list[RuleViolation]:
    """
    Validates doubling rules for sextaccords (first inversion triads: T6, S6, D6, t6, s6, d6):
    - In T6 and S6 (t6, s6): the root (prima) or fifth must be doubled.
      Doubling the third (bass) is forbidden in standard harmonic texture,
      EXCEPT in specific voice leading situations (e.g. resolution from D43 or D2 into T6,
      or voice exchanges in S6).
    - In D6: the third is the leading tone (scale degree VII).
      Doubling the leading tone in D6 is STRICTLY FORBIDDEN!
      Either the root (V) or fifth (II) must be doubled.
    """
    sym = parse_chord_symbol(chord)
    if sym not in ("T6", "S6", "D6", "t6", "s6", "d6", "VII6", "vii6", "II6", "ii6"):
        return []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)

    satb = to_satb(voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    violations: list[RuleViolation] = []
    prev_sym = parse_chord_symbol(prev_chord) if prev_chord is not None else ""

    # If soprano is a non-chord tone (NCT), skip doubling requirement
    soprano_pc = satb[0] % 12
    if soprano_pc not in (root, third, fifth):
        return violations

    # VII6 / vii6: Leading tone (root) NEVER doubled; double third (bass) or fifth
    if sym in ("VII6", "vii6"):
        if counts[root] >= 2:
            violations.append(
                RuleViolation(
                    rule_id="DOUBLING_VII6_LEADING_TONE",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In leading-tone sextaccord '{sym}', the root (leading tone, PC {root}) "
                        f"must NEVER be doubled (found {counts[root]} times)"
                    ),
                )
            )
        if counts[third] < 2 and counts[fifth] < 2:
            violations.append(
                RuleViolation(
                    rule_id="DOUBLING_SEXTACCORD",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In leading-tone sextaccord '{sym}', either third (PC {third}) "
                        f"or fifth (PC {fifth}) must be doubled"
                    ),
                )
            )
        return violations

    # II6 / ii6: double third (bass, IV degree) or root (II degree)
    if sym in ("II6", "ii6"):
        if counts[third] < 2 and counts[root] < 2:
            violations.append(
                RuleViolation(
                    rule_id="DOUBLING_SEXTACCORD",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In supertonic sextaccord '{sym}', either third (PC {third}) "
                        f"or root (PC {root}) must be doubled"
                    ),
                )
            )
        return violations

    # D6 / d6: Leading tone (third) NEVER doubled
    if sym in ("D6", "d6"):
        if counts[third] >= 2:
            violations.append(
                RuleViolation(
                    rule_id="DOUBLING_D6_LEADING_TONE",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In dominant sextaccord '{sym}', the third (leading tone, PC {third}) "
                        f"must NEVER be doubled (found {counts[third]} times)"
                    ),
                )
            )
        if counts[root] < 2 and counts[fifth] < 2:
            violations.append(
                RuleViolation(
                    rule_id="DOUBLING_SEXTACCORD",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In dominant sextaccord '{sym}', either root (PC {root}) "
                        f"or fifth (PC {fifth}) must be doubled"
                    ),
                )
            )
        return violations

    # T6, S6, t6, s6:
    # Standard rule: root or fifth must be doubled
    if counts[root] < 2 and counts[fifth] < 2:
        # Check exceptions:
        # 1. T6 / t6 resolving from D43, D2, DD43, DD2 where 7th resolves to 3rd in bass
        is_d_inversion_res = (sym in ("T6", "t6") and prev_sym in ("D43", "D2", "DD43", "DD2"))
        # 2. S6 / s6 where smooth voice leading requires doubled third
        is_s6_smooth = (sym in ("S6", "s6") and counts[third] == 2)

        if not (is_d_inversion_res or is_s6_smooth):
            violations.append(
                RuleViolation(
                    rule_id="DOUBLING_SEXTACCORD",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"In sextaccord '{sym}', root (PC {root}) or fifth (PC {fifth}) "
                        f"must be doubled; doubling the third is forbidden"
                    ),
                )
            )

    return violations


def check_seventh_chord_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    Validates factor completeness and doublings for seventh chords (D7, D65, D43, D2, VII7, II7, DD7, etc.):
    - Inversions (65, 43, 2): must be complete (1 root, 1 third, 1 fifth, 1 seventh).
    - Root position (7): complete (1, 1, 1, 1) or incomplete (2 roots, 1 third, 1 seventh, 0 fifths).
    """
    sym = parse_chord_symbol(chord).strip().upper().replace("/", "")
    is_seventh = (
        (hasattr(chord, "is_seventh") and chord.is_seventh)
        or any(k in sym for k in ("7", "65", "43"))
        or sym.endswith("2")
        or sym in ("D2", "DD2", "II2", "VII2")
    )
    if not is_seventh or "64" in sym or sym.startswith("K"):
        return []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    root, third, fifth = get_triad_tones(sym, tonic_pc, mode)

    if sym.startswith("DD") or sym.startswith("DV"):
        seventh = tonic_pc % 12
        seventh_alt = seventh
    elif sym.startswith("VII"):
        seventh = (tonic_pc + 8 if ("MINOR" in mode or sym.islower()) else tonic_pc + 9) % 12
        seventh_alt = (tonic_pc + 8) % 12
    elif sym.startswith("II"):
        seventh = tonic_pc % 12
        seventh_alt = seventh
    elif sym.startswith("VI"):
        seventh = (tonic_pc + 7) % 12
        seventh_alt = seventh
    elif sym.startswith("IV") or sym.startswith("S"):
        seventh = (tonic_pc + 3 if ("MINOR" in mode or sym.islower()) else tonic_pc + 4) % 12
        seventh_alt = seventh
    else:
        seventh = (tonic_pc + 5) % 12
        seventh_alt = seventh

    satb = to_satb(voicing)
    pcs = [p % 12 for p in satb]
    counts = Counter(pcs)

    is_inversion = any(inv in sym for inv in ("65", "43")) or sym.endswith("2") or sym in ("D2", "DD2", "II2", "VII2")
    has_seventh = counts[seventh] >= 1 or counts[seventh_alt] >= 1

    violations: list[RuleViolation] = []
    if is_inversion:
        if not (counts[root] == 1 and counts[third] == 1 and counts[fifth] == 1 and has_seventh):
            violations.append(
                RuleViolation(
                    rule_id="SEVENTH_CHORD_INVERSION_INCOMPLETE",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Seventh chord inversion '{sym}' must be complete (root, third, fifth, seventh all present once). "
                        f"Got factor counts: root={counts[root]}, third={counts[third]}, fifth={counts[fifth]}, seventh={counts[seventh]}"
                    ),
                )
            )
    else:
        is_complete = counts[root] == 1 and counts[third] == 1 and counts[fifth] == 1 and has_seventh
        is_incomplete = counts[root] == 2 and counts[third] == 1 and has_seventh and counts[fifth] == 0
        if not (is_complete or is_incomplete):
            violations.append(
                RuleViolation(
                    rule_id="SEVENTH_CHORD_DISTRIBUTION",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Root-position seventh chord '{sym}' must be complete (1 root, 1 third, 1 fifth, 1 seventh) "
                        f"or incomplete (2 roots, 1 third, 1 seventh, no fifth). Got: root={counts[root]}, "
                        f"third={counts[third]}, fifth={counts[fifth]}, seventh={counts[seventh]}"
                    ),
                )
            )

    return violations


def check_doubling(
    voicing: Any,
    chord: Any,
    key: Any = None,
    prev_chord: Any = None,
    is_final_chord: bool = False,
) -> list[RuleViolation]:
    """
    Runs all doubling validation checks relevant to the given chord and context.
    """
    violations = []
    violations.extend(check_main_triad_doubling(voicing, chord, key=key, prev_chord=prev_chord))
    violations.extend(check_triad_completeness(voicing, chord, key=key, is_final_chord=is_final_chord))
    violations.extend(check_sextaccord_doubling(voicing, chord, key=key, prev_chord=prev_chord))
    violations.extend(check_k64_doubling(voicing, chord, key=key))
    violations.extend(check_secondary_dominant_doubling(voicing, chord, key=key))
    violations.extend(check_seventh_chord_doubling(voicing, chord, key=key))
    if prev_chord is not None:
        violations.extend(check_deceptive_vi_doubling(voicing, prev_chord, chord, key=key))
    return violations
