"""
Dissonance and tendency tone resolution rules according to Brigade Harmony textbook.
Enforces 7th resolution downward by step, mandatory D43 -> T6 progression,
and leading tone resolution upward to the tonic in outer voices.
"""

from typing import Any
from src.harmony.core.types import (
    RuleViolation,
    to_satb,
    parse_key,
    parse_chord_symbol,
)

VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")
DOMINANT_SEVENTH_CHORDS = {"D7", "D65", "D43", "D2"}
DOMINANT_GROUP = {"D", "D7", "D6", "D65", "D43", "D2"}
TONIC_GROUP = {"T", "T6", "T64", "t", "t6", "VI", "vi"}


def check_seventh_resolution(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any = None,
    key: Any = None,
) -> list[RuleViolation]:
    """
    In dominant seventh chords (D7, D65, D43, D2), the seventh (scale degree IV)
    must resolve down by step (1 or 2 semitones down).
    If curr_chord is in DOMINANT_GROUP (intra-dominant repositioning or inversion change, e.g. D7 -> D65),
    the seventh may be sustained on the same pitch (delta == 0) or transferred to another voice.
    """
    if prev_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord)
    if prev_sym not in DOMINANT_SEVENTH_CHORDS:
        return []

    curr_sym = parse_chord_symbol(curr_chord) if curr_chord is not None else ""
    is_curr_dominant = curr_sym in DOMINANT_GROUP

    tonic_pc, _ = parse_key(key) if key is not None else (0, "MAJOR")
    seventh_pc = (tonic_pc + 5) % 12  # Scale degree IV is the 7th of the dominant

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)

    seventh_present_in_curr = any(curr_satb[v] % 12 == seventh_pc for v in range(4))

    violations: list[RuleViolation] = []
    for idx in range(4):
        if prev_satb[idx] % 12 == seventh_pc:
            delta = curr_satb[idx] - prev_satb[idx]
            # If transitioning within DOMINANT_GROUP: allow sustained 7th (delta 0) or transfer
            if is_curr_dominant and (delta == 0 or seventh_present_in_curr or delta in (-1, -2)):
                continue

            # Standard authentic resolution: must step down (-1 or -2 semitones)
            if delta not in (-1, -2):
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_SEVENTH_DOWN",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Seventh (scale degree IV, PC {seventh_pc}) of {prev_sym} in "
                            f"{VOICE_NAMES[idx]} must resolve down by step, moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

    return violations


def check_d43_resolution(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    D43 has the fifth of dominant in the bass (scale degree II).
    It resolves canonically to T/T53 (bass steps down II -> I by 1 or 2 semitones)
    or to T6 (bass steps up II -> III by 1 or 2 semitones).
    The seventh (scale degree IV) in upper voices must resolve down by step.
    """
    if prev_chord is None or curr_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord).strip().upper().replace("/", "")
    if prev_sym != "D43":
        return []

    curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "")
    violations: list[RuleViolation] = []

    # Target chord must be T, T53, T6 (or minor t, t53, t6)
    if curr_sym not in ("T", "T53", "T6", "T-6", "t", "t53", "t6", "t-6"):
        violations.append(
            RuleViolation(
                rule_id="RESOLUTION_D43_TO_T6",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"D43 must resolve to T, T53, or T6 (or minor t/t6), but got '{curr_sym}'"
                ),
                voices=(3,),
            )
        )

    # Bass motion check:
    # If resolving to T / T53: bass must step down 1 or 2 semitones (II -> I)
    # If resolving to T6: bass must step up 1 or 2 semitones (II -> III)
    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    delta_b = curr_satb[3] - prev_satb[3]

    if curr_sym in ("T", "T53", "t", "t53"):
        if delta_b not in (-1, -2):
            violations.append(
                RuleViolation(
                    rule_id="RESOLUTION_D43_TO_T6",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Bass of D43 resolving to {curr_sym} must step down by second into root (degree I), "
                        f"moved {delta_b:+d}"
                    ),
                    voices=(3,),
                )
            )
    elif curr_sym in ("T6", "T-6", "t6", "t-6"):
        if delta_b not in (1, 2):
            violations.append(
                RuleViolation(
                    rule_id="RESOLUTION_D43_TO_T6",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"Bass of D43 resolving to {curr_sym} must step up by second into third (degree III), "
                        f"moved {delta_b:+d}"
                    ),
                    voices=(3,),
                )
            )

    # Seventh resolution in upper voices (scale degree IV)
    tonic_pc, _ = parse_key(key) if key is not None else (0, "MAJOR")
    seventh_pc = (tonic_pc + 5) % 12  # Scale degree IV
    for idx in range(3):  # S, A, T
        if prev_satb[idx] % 12 == seventh_pc:
            delta = curr_satb[idx] - prev_satb[idx]
            if delta not in (-1, -2):
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_SEVENTH_DOWN",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Seventh (degree IV, PC {seventh_pc}) of D43 in {VOICE_NAMES[idx]} "
                            f"must resolve down by step, moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

    return violations


def check_d2_resolution(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    D2 has the seventh in the bass (scale degree IV).
    It MUST resolve strictly to T6 (or t6), with the bass stepping down
    by 1 or 2 semitones into the third of the tonic.
    """
    if prev_chord is None or curr_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord).strip().upper().replace("/", "")
    if prev_sym not in ("D2", "DD2"):
        return []

    curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "")
    violations: list[RuleViolation] = []

    if curr_sym not in ("T6", "T-6", "t6", "t-6"):
        violations.append(
            RuleViolation(
                rule_id="RESOLUTION_D2_TO_T6",
                severity="hard_gate",
                penalty=100000.0,
                description=f"D2 must resolve strictly to T6 (or t6), but got '{curr_sym}'",
                voices=(3,),
            )
        )

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    delta_b = curr_satb[3] - prev_satb[3]

    if delta_b not in (-1, -2):
        violations.append(
            RuleViolation(
                rule_id="RESOLUTION_D2_TO_T6",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Bass of D2 must step down by second into third of T6, moved {delta_b:+d}",
                voices=(3,),
            )
        )

    return violations


def check_leading_tone_resolution(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    When progressing from Dominant to Tonic in an authentic cadence,
    the leading tone (scale degree VII) in outer voices (Soprano and Bass)
    must resolve upward to the tonic (scale degree I) by half-step (+1 semitone).
    """
    if prev_chord is None or curr_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord)
    curr_sym = parse_chord_symbol(curr_chord)

    if prev_sym not in DOMINANT_GROUP or curr_sym not in TONIC_GROUP:
        return []

    tonic_pc, _ = parse_key(key) if key is not None else (0, "MAJOR")
    leading_tone_pc = (tonic_pc + 11) % 12  # Scale degree VII

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    # Check outer voices: Soprano (0) and Bass (3)
    for idx in (0, 3):
        if prev_satb[idx] % 12 == leading_tone_pc:
            delta = curr_satb[idx] - prev_satb[idx]
            # Must step up by half-step (+1)
            if delta != 1:
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_LEADING_TONE_UP",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Leading tone (VII, PC {leading_tone_pc}) in {VOICE_NAMES[idx]} "
                            f"must resolve up to tonic by half-step (+1), moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

    return violations


def check_vii7_resolution(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    In leading-tone seventh chords (VII7, VII65, VII43, VII2) resolving to T/t:
    - The seventh (scale degree VI) must resolve down by step into degree V.
    - The fifth (scale degree IV) must resolve down by step into degree III.
    - The leading tone (scale degree VII) must resolve up by half-step into degree I.
    - The resulting tonic triad T strictly requires a doubled third!
    """
    if prev_chord is None or curr_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord)
    curr_sym = parse_chord_symbol(curr_chord)

    vii7_family = {"VII7", "vii7", "VII65", "vii65", "VII43", "vii43", "VII2", "vii2"}
    if prev_sym not in vii7_family or curr_sym not in ("T", "t"):
        return []

    tonic_pc, _ = parse_key(key) if key is not None else (0, "MAJOR")
    leading_pc = (tonic_pc + 11) % 12
    fifth_pc = (tonic_pc + 5) % 12    # Scale degree IV is 5th of VII7
    seventh_pc = (tonic_pc + 9) % 12  # Scale degree VI (or 8 in minor)
    seventh_pc_alt = (tonic_pc + 8) % 12

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    for idx in range(4):
        p = prev_satb[idx] % 12
        delta = curr_satb[idx] - prev_satb[idx]

        # Seventh must resolve down by step (-1 or -2)
        if p in (seventh_pc, seventh_pc_alt):
            if delta not in (-1, -2):
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_VII7_SEVENTH_DOWN",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Seventh of {prev_sym} in {VOICE_NAMES[idx]} must resolve down by step, "
                            f"moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

        # Fifth of VII7 must resolve down by step (-1 or -2) into 3rd of T
        elif p == fifth_pc:
            if delta not in (-1, -2):
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_VII7_FIFTH_DOWN",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Fifth of {prev_sym} in {VOICE_NAMES[idx]} must resolve down into third of T, "
                            f"moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

        # Leading tone of VII7 must resolve up by half-step (+1) into tonic
        elif p == leading_pc:
            if delta != 1:
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_VII7_LEADING_TONE_UP",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Leading tone of {prev_sym} in {VOICE_NAMES[idx]} "
                            f"must resolve up to tonic by half-step (+1), moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

    # Resulting tonic triad must strictly double the third to avoid parallel fifths
    from collections import Counter
    curr_satb = to_satb(curr_voicing)
    curr_counts = Counter([p % 12 for p in curr_satb])
    _, mode = parse_key(key) if key is not None else (0, "MAJOR")
    is_minor = "MINOR" in mode or curr_sym.islower()
    tonic_third_pc = (tonic_pc + 3 if is_minor else tonic_pc + 4) % 12
    if curr_counts[tonic_third_pc] < 2:
        violations.append(
            RuleViolation(
                rule_id="RESOLUTION_VII7_DOUBLED_THIRD",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"In resolution of {prev_sym} to {curr_sym}, the third of the tonic triad "
                    f"(PC {tonic_third_pc}) must strictly be doubled to avoid parallel fifths. "
                    f"Found {curr_counts[tonic_third_pc]} times."
                ),
            )
        )

    return violations


def check_secondary_dominant_resolution(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    Validates resolution of Secondary Dominant chords (DD, DD7, D7/V, D7/II, D7/VI, D7/IV):
    - Secondary leading tone (e.g. F# in C-dur for DD) must resolve up by semitone (+1)
      into target root (e.g. G in D, D7, or K64), OR step down chromatically (-1).
    - Secondary seventh (e.g. C in DD7) must resolve down by step (-1 or -2)
      into the third of the target chord (e.g. B in G).
    """
    if prev_chord is None or curr_chord is None:
        return []

    prev_sym = parse_chord_symbol(prev_chord).strip().upper().replace("/", "")
    curr_sym = parse_chord_symbol(curr_chord).strip().upper().replace("/", "")
    if not (
        prev_sym.startswith("DD")
        or prev_sym in ("D7V", "DV")
        or "D7II" in prev_sym
        or "DII" in prev_sym
        or "D7VI" in prev_sym
        or "DVI" in prev_sym
        or "D7IV" in prev_sym
        or "DIV" in prev_sym
    ):
        return []

    tonic_pc, _ = parse_key(key) if key is not None else (0, "MAJOR")

    # Determine secondary leading tone and secondary seventh
    sec_leading_pc = None
    sec_seventh_pc = None

    if prev_sym.startswith("DD") or prev_sym in ("D7V", "DV"):
        sec_leading_pc = (tonic_pc + 6) % 12
        if any(x in prev_sym for x in ("7", "65", "43", "2")):
            sec_seventh_pc = tonic_pc % 12
    elif "II" in prev_sym:
        sec_leading_pc = (tonic_pc + 1) % 12
        if any(x in prev_sym for x in ("7", "65", "43", "2")):
            sec_seventh_pc = (tonic_pc + 7) % 12
    elif "VI" in prev_sym:
        sec_leading_pc = (tonic_pc + 8) % 12
        if any(x in prev_sym for x in ("7", "65", "43", "2")):
            sec_seventh_pc = (tonic_pc + 2) % 12
    elif "IV" in prev_sym:
        sec_leading_pc = (tonic_pc + 4) % 12
        if any(x in prev_sym for x in ("7", "65", "43", "2")):
            sec_seventh_pc = (tonic_pc + 10) % 12

    prev_satb = to_satb(prev_voicing)
    curr_satb = to_satb(curr_voicing)
    violations: list[RuleViolation] = []

    # Validate target chord for secondary dominant
    if prev_sym.startswith("DD") or prev_sym in ("D7V", "DV"):
        allowed_targets = {"D", "D7", "D6", "D65", "D43", "D2", "K64", "VII", "VII7", "VII65", "VII43", "VII2"}
        if curr_sym not in allowed_targets:
            violations.append(
                RuleViolation(
                    rule_id="RESOLUTION_DD_TARGET",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=f"Secondary dominant {prev_sym} must resolve to D or K64 group, not {curr_sym}",
                )
            )

    for idx in range(4):
        p = prev_satb[idx] % 12
        delta = curr_satb[idx] - prev_satb[idx]

        # Check secondary leading tone resolution
        if sec_leading_pc is not None and p == sec_leading_pc:
            # Must step up by semitone (+1) or step down chromatically (-1)
            if delta not in (1, -1):
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_SECONDARY_DOMINANT",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Secondary leading tone (PC {sec_leading_pc}) in {VOICE_NAMES[idx]} "
                            f"must resolve up by semitone (+1) or down chromatically (-1), moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

        # Check secondary seventh resolution
        if sec_seventh_pc is not None and p == sec_seventh_pc:
            # Must resolve down by step (-1 or -2), or be held as common tone in K64 (delta == 0)
            is_k64_held = (curr_sym == "K64" and delta == 0)
            if not (delta in (-1, -2) or is_k64_held):
                violations.append(
                    RuleViolation(
                        rule_id="RESOLUTION_SECONDARY_DOMINANT",
                        severity="hard_gate",
                        penalty=100000.0,
                        description=(
                            f"Secondary seventh (PC {sec_seventh_pc}) of {prev_sym} in {VOICE_NAMES[idx]} "
                            f"must resolve down by step (-1 or -2), moved {delta:+d}"
                        ),
                        voices=(idx,),
                    )
                )

    return violations


def validate_resolutions(
    prev_voicing: Any,
    curr_voicing: Any,
    prev_chord: Any,
    curr_chord: Any,
    key: Any = None,
) -> list[RuleViolation]:
    """
    Runs all dissonance and tendency tone resolution checks.
    """
    violations = []
    violations.extend(
        check_seventh_resolution(
            prev_voicing, curr_voicing, prev_chord, curr_chord, key=key
        )
    )
    violations.extend(
        check_d43_resolution(
            prev_voicing, curr_voicing, prev_chord, curr_chord, key=key
        )
    )
    violations.extend(
        check_d2_resolution(
            prev_voicing, curr_voicing, prev_chord, curr_chord, key=key
        )
    )
    violations.extend(
        check_leading_tone_resolution(
            prev_voicing, curr_voicing, prev_chord, curr_chord, key=key
        )
    )
    violations.extend(
        check_vii7_resolution(
            prev_voicing, curr_voicing, prev_chord, curr_chord, key=key
        )
    )
    violations.extend(
        check_secondary_dominant_resolution(
            prev_voicing, curr_voicing, prev_chord, curr_chord, key=key
        )
    )
    return violations
