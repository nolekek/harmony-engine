"""
Horizontal voice leading rules according to Brigade Harmony textbook.
Detects parallel/contrary 5ths and 8ves, hidden 5ths/8ves, overlapping, and forbidden melodic leaps.
"""

from typing import Any
from src.harmony.core.types import RuleViolation, to_satb, parse_key

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
) -> list[RuleViolation]:
    """
    Checks for parallel pure fifths and pure octaves/unisons across all 6 voice pairs.
    Direct motion into the same pure interval between the same pair of voices is strictly forbidden.
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    for v1, v2 in VOICE_PAIRS:
        p1, p2 = prev_satb[v1], prev_satb[v2]
        c1, c2 = curr_satb[v1], curr_satb[v2]

        d1 = c1 - p1
        d2 = c2 - p2

        # Motion must be in the same direction and non-zero
        if d1 * d2 > 0:
            int_prev = abs(p1 - p2) % 12
            int_curr = abs(c1 - c2) % 12

            if int_prev == 7 and int_curr == 7:
                violations.append(
                    RuleViolation(
                        rule_id="PARALLEL_FIFTHS",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Parallel fifths between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} (int {abs(p1 - p2)}) -> {c1}-{c2} (int {abs(c1 - c2)})"
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
                            f"{p1}-{p2} (int {abs(p1 - p2)}) -> {c1}-{c2} (int {abs(c1 - c2)})"
                        ),
                        voices=(v1, v2),
                    )
                )

    return violations


def check_contrary_fifths_and_octaves(
    prev_voicing: Any,
    curr_voicing: Any,
) -> list[RuleViolation]:
    """
    Checks for contrary fifths and octaves: voices moving in opposite directions
    retaining or arriving from a pure 5th/8ve into another pure 5th/8ve.
    """
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
            int_prev = abs(p1 - p2) % 12
            int_curr = abs(c1 - c2) % 12

            if int_prev == 7 and int_curr == 7:
                violations.append(
                    RuleViolation(
                        rule_id="CONTRARY_FIFTHS",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Contrary fifths between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} -> {c1}-{c2}"
                        ),
                        voices=(v1, v2),
                    )
                )
            elif int_prev == 0 and int_curr == 0:
                violations.append(
                    RuleViolation(
                        rule_id="CONTRARY_OCTAVES",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Contrary octaves between {VOICE_NAMES[v1]} and {VOICE_NAMES[v2]}: "
                            f"{p1}-{p2} -> {c1}-{c2}"
                        ),
                        voices=(v1, v2),
                    )
                )

    return violations


def check_hidden_fifths_and_octaves(
    prev_voicing: Any,
    curr_voicing: Any,
) -> list[RuleViolation]:
    """
    Checks for hidden (direct) fifths and octaves between outer voices (Soprano and Bass).
    If Soprano and Bass move in the same direction into a pure 5th or 8ve,
    Soprano MUST move by step (|dS| <= 2). A leap in soprano (|dS| > 2) is forbidden.
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    ds = curr_satb[0] - prev_satb[0]
    db = curr_satb[3] - prev_satb[3]

    # Direct motion between outer voices
    if ds * db > 0:
        int_curr = abs(curr_satb[0] - curr_satb[3]) % 12
        if int_curr in (0, 7):
            # If soprano leaps by more than a step (> 2 semitones)
            if abs(ds) > 2:
                interval_type = "octave" if int_curr == 0 else "fifth"
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
) -> list[RuleViolation]:
    """
    Checks for forbidden melodic intervals in any single voice:
    - Melodic leaps of a seventh (10 or 11 semitones) or wider than an octave (> 12 semitones)
    - Tritone melodic leaps (augmented 4th / diminished 5th, 6 semitones)
    - Augmented second leaps (3 semitones between scale degrees VI and VII in harmonic minor)
    """
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    tonic_pc, mode = parse_key(key) if key is not None else (0, "MAJOR")
    is_minor = "MINOR" in mode

    for idx in range(4):
        p = prev_satb[idx]
        c = curr_satb[idx]
        step = abs(c - p)

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

        # Tritone leap (augmented 4th / diminished 5th)
        elif step == 6:
            violations.append(
                RuleViolation(
                    rule_id="MELODIC_AUGMENTED_INTERVAL",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Forbidden tritone leap (augmented 4th / dim 5th, 6 semitones) "
                        f"in {VOICE_NAMES[idx]}: {p} -> {c}"
                    ),
                    voices=(idx,),
                )
            )

        # Augmented 2nd leap (3 semitones between VI and VII# in harmonic minor)
        elif step == 3 and is_minor:
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

    return violations


def validate_voice_leading(
    prev_voicing: Any,
    curr_voicing: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    Runs full suite of horizontal voice-leading transition checks.
    """
    violations = []
    violations.extend(check_parallel_fifths_and_octaves(prev_voicing, curr_voicing))
    violations.extend(check_contrary_fifths_and_octaves(prev_voicing, curr_voicing))
    violations.extend(check_hidden_fifths_and_octaves(prev_voicing, curr_voicing))
    violations.extend(check_voice_overlapping(prev_voicing, curr_voicing))
    violations.extend(check_melodic_intervals(prev_voicing, curr_voicing, key=key))
    return violations
