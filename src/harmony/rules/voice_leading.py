"""
Horizontal voice leading rules according to Brigade Harmony textbook.
Detects parallel/contrary 5ths and 8ves, hidden 5ths/8ves, overlapping, and forbidden melodic leaps.
"""

from typing import Any
from src.harmony.core.types import RuleViolation, to_satb, parse_key, parse_chord_symbol
# Намеренный реэкспорт spacing-проверок: историческая публичная поверхность модуля
# (redundant alias — явный re-export, F401 не применяется).
from src.harmony.rules.spacing import (
    check_voice_crossing as check_voice_crossing,
    check_texture_spacing as check_texture_spacing,
    check_voice_ranges as check_voice_ranges,
)

VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
VOICE_PAIRS = (
    (0, 1),  # S - A
    (0, 2),  # S - T
    (0, 3),  # S - B
    (1, 2),  # A - T
    (1, 3),  # A - B
    (2, 3),  # T - B
)


def check_parallel_fifths_and_octaves(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any = None,
    curr_chord: Any = None,
) -> list[RuleViolation]:
    """
    Checks for parallel pure fifths and pure octaves/unisons across all 6 voice pairs.
    Direct motion into the same pure interval between the same pair of voices is strictly forbidden.
    Catches diminished 5th -> perfect 5th in similar motion (PARALLEL_DIM5_P5).
    Does not apply to pure octave shifts within the same chord (prev_chord == curr_chord).
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    is_same_chord = False
    if prev_chord is not None and curr_chord is not None:
        p_sym = parse_chord_symbol(prev_chord)
        c_sym = parse_chord_symbol(curr_chord)
        if p_sym and p_sym == c_sym:
            is_same_chord = True

    for v1, v2 in VOICE_PAIRS:
        p1, p2 = prev_satb[v1], prev_satb[v2]
        c1, c2 = curr_satb[v1], curr_satb[v2]

        d1 = c1 - p1
        d2 = c2 - p2

        # Motion must be in the same direction and non-zero
        if d1 * d2 > 0:
            raw_prev = abs(p1 - p2)
            raw_curr = abs(c1 - c2)
            int_prev = raw_prev % 12
            int_curr = raw_curr % 12

            # Catch dim 5th -> perfect 5th in similar motion
            if int_prev == 6 and int_curr == 7:
                violations.append(
                    RuleViolation(
                        rule_id="PARALLEL_DIM5_P5",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Forbidden motion from diminished 5th to perfect 5th in similar motion between "
                            f"{VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: {p1}-{p2} (int {raw_prev}) -> {c1}-{c2} (int {raw_curr})"
                        ),
                        voices=(v1, v2),
                    )
                )

            # Skip parallel checks on pure octave repositioning within the same chord
            if is_same_chord and (abs(d1) % 12 == 0 or abs(d2) % 12 == 0):
                continue

            if int_prev == 7 and int_curr == 7:
                violations.append(
                    RuleViolation(
                        rule_id="PARALLEL_FIFTHS",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Parallel fifths between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} (int {raw_prev}) -> {c1}-{c2} (int {raw_curr})"
                        ),
                        voices=(v1, v2),
                    )
                )
            elif int_prev == 0 and int_curr == 0:
                violations.append(
                    RuleViolation(
                        rule_id="PARALLEL_OCTAVES",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Parallel octaves/unisons between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} (int {raw_prev}) -> {c1}-{c2} (int {raw_curr})"
                        ),
                        voices=(v1, v2),
                    )
                )

    return violations


def check_contrary_fifths_and_octaves(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any = None,
    curr_chord: Any = None,
) -> list[RuleViolation]:
    """
    Checks for contrary fifths and octaves: voices moving in opposite directions
    retaining or arriving from a pure 5th/8ve into another pure 5th/8ve.
    Checks exact pure intervals (5th: 7, 19; 8ve: 12, 24, 36).
    Does not apply to voice exchanges or repositioning within the same chord (prev_chord == curr_chord).
    """
    if prev_chord is not None and curr_chord is not None:
        p_sym = parse_chord_symbol(prev_chord)
        c_sym = parse_chord_symbol(curr_chord)
        if p_sym and p_sym == c_sym:
            return []

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    for v1, v2 in VOICE_PAIRS:
        p1, p2 = prev_satb[v1], prev_satb[v2]
        c1, c2 = curr_satb[v1], curr_satb[v2]

        d1 = c1 - p1
        d2 = c2 - p2

        # Contrary motion: opposite directions
        if d1 * d2 < 0:
            raw_prev = abs(p1 - p2)
            raw_curr = abs(c1 - c2)

            # Pure fifths: 7 or 19 or 31 semitones (modulo 12 == 7)
            if raw_prev % 12 == 7 and raw_curr % 12 == 7:
                violations.append(
                    RuleViolation(
                        rule_id="CONTRARY_FIFTHS",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Contrary fifths between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} (int {raw_prev}) -> {c1}-{c2} (int {raw_curr})"
                        ),
                        voices=(v1, v2),
                    )
                )
            # Pure octaves / unison: modulo 12 == 0
            elif raw_prev % 12 == 0 and raw_prev > 0 and raw_curr % 12 == 0:
                if raw_curr == 0:
                    description = (
                        f"Contrary motion octave to unison between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                        f"{p1}-{p2} (int {raw_prev}) -> {c1}-{c2} (int {raw_curr})"
                    )
                else:
                    description = (
                        f"Contrary octaves between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                        f"{p1}-{p2} (int {raw_prev}) -> {c1}-{c2} (int {raw_curr})"
                    )
                violations.append(
                    RuleViolation(
                        rule_id="CONTRARY_OCTAVES",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=description,
                        voices=(v1, v2),
                    )
                )

    return violations


def check_hidden_fifths_and_octaves(
    prev_voicing: Any,
    curr_voicing: Any,
    existing_violations: list[RuleViolation] | None = None,
) -> list[RuleViolation]:
    """
    Checks for hidden (direct) fifths and octaves between outer voices (Soprano and Bass).
    If Soprano and Bass move in the same direction into a pure 5th or 8ve,
    Soprano MUST move by step (|dS| <= 2). A leap in soprano (|dS| > 2) is forbidden.
    Does not duplicate violation if parallel violation is already recorded for outer voices.
    """
    if existing_violations is not None:
        if any(v.voices == (0, 3) and "PARALLEL" in v.rule_id for v in existing_violations):
            return []

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    ds = curr_satb[0] - prev_satb[0]
    db = curr_satb[3] - prev_satb[3]

    # Direct motion between outer voices
    if ds * db > 0:
        raw_curr = abs(curr_satb[0] - curr_satb[3])
        int_curr = raw_curr % 12
        if int_curr in (0, 7):
            # If soprano leaps by more than a step (> 2 semitones)
            if abs(ds) > 2:
                if int_curr == 7:
                    interval_type = "fifth"
                elif raw_curr == 0:
                    interval_type = "unison"
                else:
                    interval_type = "octave"
                violations.append(
                    RuleViolation(
                        rule_id="HIDDEN_FIFTHS_OCTAVES",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Hidden {interval_type} in outer voices: S and B move in direct motion "
                            f"into {curr_satb[0] - curr_satb[3]} semitones with soprano leap "
                            f"|dS|={abs(ds)} > 2"
                        ),
                        voices=(0, 3),
                    )
                )

    return violations


def check_voice_overlapping(
    prev_voicing: Any,
    curr_voicing: Any,
) -> list[RuleViolation]:
    """
    Checks for voice overlapping (перекрывание голосов):
    A voice must not move higher than the previous pitch of its upper neighbor,
    or lower than the previous pitch of its lower neighbor.
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    # Upper movements crossing previous upper neighbor
    if curr_satb[1] > prev_satb[0]:
        violations.append(
            RuleViolation(
                rule_id="VOICE_OVERLAPPING",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Voice overlapping: Alto ({curr_satb[1]}) rose above previous Soprano ({prev_satb[0]})"
                ),
                voices=(1, 0),
            )
        )
    if curr_satb[2] > prev_satb[1]:
        violations.append(
            RuleViolation(
                rule_id="VOICE_OVERLAPPING",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Voice overlapping: Tenor ({curr_satb[2]}) rose above previous Alto ({prev_satb[1]})"
                ),
                voices=(2, 1),
            )
        )
    if curr_satb[3] > prev_satb[2]:
        violations.append(
            RuleViolation(
                rule_id="VOICE_OVERLAPPING",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Voice overlapping: Bass ({curr_satb[3]}) rose above previous Tenor ({prev_satb[2]})"
                ),
                voices=(3, 2),
            )
        )

    # Downward movements crossing previous lower neighbor
    if curr_satb[0] < prev_satb[1]:
        violations.append(
            RuleViolation(
                rule_id="VOICE_OVERLAPPING",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Voice overlapping: Soprano ({curr_satb[0]}) fell below previous Alto ({prev_satb[1]})"
                ),
                voices=(0, 1),
            )
        )
    if curr_satb[1] < prev_satb[2]:
        violations.append(
            RuleViolation(
                rule_id="VOICE_OVERLAPPING",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Voice overlapping: Alto ({curr_satb[1]}) fell below previous Tenor ({prev_satb[2]})"
                ),
                voices=(1, 2),
            )
        )
    if curr_satb[2] < prev_satb[3]:
        violations.append(
            RuleViolation(
                rule_id="VOICE_OVERLAPPING",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Voice overlapping: Tenor ({curr_satb[2]}) fell below previous Bass ({prev_satb[3]})"
                ),
                voices=(2, 3),
            )
        )

    return violations


def check_melodic_intervals(
    prev_voicing: Any,
    curr_voicing: Any,
    key: Any = None,
    prev2_voicing: Any = None,
    next_voicing: Any = None,
) -> list[RuleViolation]:
    """
    Checks for forbidden melodic intervals in any single voice:
    - Melodic leaps of a seventh (10 or 11 semitones) or wider than an octave (> 12 semitones)
    - Tritone melodic leaps (augmented 4th / diminished 5th, 6 semitones), with exception:
      diminished 5th DOWN (-6) resolving inwards by step up (+1 or +2) is permitted.
    - Augmented second leaps (3 semitones between scale degrees VI and VII# in harmonic minor)
    - Augmented fifth leaps (8 semitones, e.g. III -> VII# in harmonic minor)
    - Diminished seventh leaps (9 semitones, e.g. VII# -> VI in harmonic minor)
    - Diminished fourth leaps (4 semitones, e.g. VII# -> III in harmonic minor)
    - Two consecutive leaps in the same direction (|d1| > 2 and |d2| > 2, d1*d2 > 0)
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")

    # Check two leaps in same direction if history provided
    if prev2_voicing is not None:
        p2_satb = to_satb(prev2_voicing)
        for idx in range(4):
            d_prev = prev_satb[idx] - p2_satb[idx]
            d_curr = curr_satb[idx] - prev_satb[idx]
            if abs(d_prev) > 4 and abs(d_curr) > 4 and (d_prev * d_curr > 0):
                violations.append(
                    RuleViolation(
                        rule_id="MELODIC_TWO_LEAPS_SAME_DIRECTION",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Forbidden two consecutive leaps in the same direction in {VOICE_NAMES[idx]}: "
                            f"{p2_satb[idx]} -> {prev_satb[idx]} -> {curr_satb[idx]}"
                        ),
                        voices=(idx,),
                    )
                )

    for idx in range(4):
        p = prev_satb[idx]
        c = curr_satb[idx]
        delta = c - p
        step = abs(delta)

        # Seventh leaps or excessive leaps (> 12)
        if step in (10, 11) or step > 12:
            violations.append(
                RuleViolation(
                    rule_id="MELODIC_SEVENTH_LEAP",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Forbidden melodic seventh or excessive leap ({step} semitones) "
                        f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                    ),
                    voices=(idx,),
                )
            )

        # Tritone leap (6 semitones: aug 4th or dim 5th)
        elif step == 6:
            # Diminished 5th DOWN (-6 semitones): permitted if resolving inwards
            if delta == -6:
                is_permitted = False
                if prev2_voicing is not None:
                    d_prev = prev_satb[idx] - to_satb(prev2_voicing)[idx]
                    if d_prev >= 4:
                        is_permitted = True
                elif next_voicing is not None:
                    next_pitch = to_satb(next_voicing)[idx]
                    next_delta = next_pitch - c
                    if next_delta in (1, 2):
                        is_permitted = True
                else:
                    # If prev2 is not provided and next_voicing is None, allow as before
                    is_permitted = True

                if not is_permitted:
                    violations.append(
                        RuleViolation(
                            rule_id="MELODIC_AUGMENTED_INTERVAL",
                            severity="hard_gate",
                            penalty=100000.0,
                            description=(
                                f"Forbidden tritone leap ({step} semitones) "
                                f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                            ),
                            voices=(idx,),
                        )
                    )
            else:
                # Tritone leap (+6) is strictly forbidden
                violations.append(
                    RuleViolation(
                        rule_id="MELODIC_AUGMENTED_INTERVAL",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Forbidden tritone leap ({step} semitones) "
                            f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                        ),
                        voices=(idx,),
                    )
                )

        # Augmented 2nd leap (3 semitones between VI and VII# in harmonic minor/major)
        elif step == 3:
            deg6_pc = (tonic_pc + 8) % 12
            deg7_pc = (tonic_pc + 11) % 12
            pcs = {p % 12, c % 12}
            if pcs == {deg6_pc, deg7_pc}:
                violations.append(
                    RuleViolation(
                        rule_id="MELODIC_AUGMENTED_INTERVAL",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Forbidden augmented 2nd leap between scale degrees VI and VII# "
                            f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                        ),
                        voices=(idx,),
                    )
                )

        # Diminished 7th leap (9 semitones between VII# and VI in minor/harmonic major)
        elif step == 9:
            deg6_pc = (tonic_pc + 8) % 12
            deg7_pc = (tonic_pc + 11) % 12
            pcs = {p % 12, c % 12}
            if pcs == {deg6_pc, deg7_pc}:
                violations.append(
                    RuleViolation(
                        rule_id="MELODIC_DIMINISHED_SEVENTH",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Forbidden diminished 7th leap (9 semitones) "
                            f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                        ),
                        voices=(idx,),
                    )
                )

        # Augmented 5th leap (8 semitones, e.g. III -> VII# in harmonic minor, III -> VIb in harmonic major)
        elif step == 8:
            deg3_min_pc = (tonic_pc + 3) % 12
            deg7_pc = (tonic_pc + 11) % 12
            deg6_pc = (tonic_pc + 8) % 12
            deg3_maj_pc = (tonic_pc + 4) % 12
            pcs = {p % 12, c % 12}
            if pcs == {deg3_min_pc, deg7_pc} or pcs == {deg3_maj_pc, deg6_pc}:
                violations.append(
                    RuleViolation(
                        rule_id="MELODIC_AUGMENTED_INTERVAL",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Forbidden augmented 5th leap (8 semitones) "
                            f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                        ),
                        voices=(idx,),
                    )
                )

        # Diminished 4th leap (4 semitones between VII# and III in harmonic minor/major)
        elif step == 4:
            deg3_min_pc = (tonic_pc + 3) % 12
            deg7_pc = (tonic_pc + 11) % 12
            deg6_pc = (tonic_pc + 8) % 12
            deg3_maj_pc = (tonic_pc + 4) % 12
            pcs = {p % 12, c % 12}
            if pcs == {deg3_min_pc, deg7_pc} or pcs == {deg3_maj_pc, deg6_pc}:
                violations.append(
                    RuleViolation(
                        rule_id="MELODIC_DIMINISHED_FOURTH_SOFT",
                        severity="soft",
                        penalty=5.0,
                        description=(
                            f"Diminished 4th leap (4 semitones) in {VOICE_NAMES[idx]}: {p} -> {c} "
                            f"(soft penalty, permitted if resolving inwards)"
                        ),
                        voices=(idx,),
                    )
                )

    return violations


def check_unisons(
    prev_voicing: Any,
    curr_voicing: Any,
) -> list[RuleViolation]:
    """
    Checks for illegal motion into or out of unisons:
    In classical harmony, a unison between any pair of voices can only be approached
    or left by contrary motion or oblique motion (one voice stationary).
    Approaching or leaving a unison in direct (similar) motion is strictly forbidden.
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    for v1, v2 in VOICE_PAIRS:
        p1, p2 = prev_satb[v1], prev_satb[v2]
        c1, c2 = curr_satb[v1], curr_satb[v2]

        d1 = c1 - p1
        d2 = c2 - p2

        # Direct motion: both voices move in the same non-zero direction
        if d1 * d2 > 0:
            # 1. Direct motion INTO unison
            if c1 == c2 and p1 != p2:
                violations.append(
                    RuleViolation(
                        rule_id="DIRECT_UNISON",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Illegal direct motion into unison between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} -> {c1}-{c2}"
                        ),
                        voices=(v1, v2),
                    )
                )
            # 2. Direct motion OUT OF unison
            elif p1 == p2 and c1 != c2:
                violations.append(
                    RuleViolation(
                        rule_id="DIRECT_UNISON",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Illegal direct motion out of unison between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} -> {c1}-{c2}"
                        ),
                        voices=(v1, v2),
                    )
                )

    return violations


def validate_voice_leading(
    prev_voicing: Any,
    curr_voicing: Any,
    key: Any = None,
    prev_chord: Any = None,
    curr_chord: Any = None,
    prev2_voicing: Any = None,
    next_voicing: Any = None,
) -> list[RuleViolation]:
    """
    Runs full suite of horizontal voice-leading transition checks.
    """
    violations = []
    violations.extend(
        check_parallel_fifths_and_octaves(
            prev_voicing, curr_voicing, prev_chord=prev_chord, curr_chord=curr_chord
        )
    )
    violations.extend(
        check_contrary_fifths_and_octaves(
            prev_voicing, curr_voicing, prev_chord=prev_chord, curr_chord=curr_chord
        )
    )
    violations.extend(
        check_hidden_fifths_and_octaves(
            prev_voicing, curr_voicing, existing_violations=violations
        )
    )
    violations.extend(check_voice_overlapping(prev_voicing, curr_voicing))
    violations.extend(check_unisons(prev_voicing, curr_voicing))
    violations.extend(
        check_melodic_intervals(
            prev_voicing,
            curr_voicing,
            key=key,
            prev2_voicing=prev2_voicing,
            next_voicing=next_voicing,
        )
    )
    return violations
