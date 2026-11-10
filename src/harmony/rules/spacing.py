"""
Voice ranges, crossing, and texture spacing rules according to Brigade Harmony textbook.
"""

from typing import Any, Mapping
from src.harmony.core.types import RuleViolation, to_satb

VOICE_NAMES = ("Soprano", "Alto", "Tenor", "Bass")

# Standard Brigade textbook ranges (MIDI pitch)
STANDARD_VOICE_RANGES: dict[int, tuple[int, int]] = {
    0: (60, 81),  # Soprano: C4 - A5
    1: (55, 74),  # Alto: G3 - D5
    2: (48, 67),  # Tenor: C3 - G4
    3: (40, 60),  # Bass: E2 - C4
}

# Extended ranges permitted in exceptional climaxes / cadences
EXTENDED_VOICE_RANGES: dict[int, tuple[int, int]] = {
    0: (59, 83),  # B3 - B5
    1: (53, 75),  # F3 - Eb5
    2: (46, 69),  # Bb2 - A4
    3: (36, 60),  # C2 - C4 (final cadential bass reaches C2 = 36)
}


def check_voice_ranges(
    voicing: Any,
    ranges: Mapping[int, tuple[int, int]] | None = None,
    allow_extended: bool = False,
) -> list[RuleViolation]:
    """
    Checks whether all four voices fall within their strictly designated vocal compass.
    """
    satb = to_satb(voicing)
    active_ranges = ranges or (EXTENDED_VOICE_RANGES if allow_extended else STANDARD_VOICE_RANGES)

    violations: list[RuleViolation] = []
    for idx, pitch in enumerate(satb):
        min_p, max_p = active_ranges.get(idx, STANDARD_VOICE_RANGES[idx])
        if pitch < min_p or pitch > max_p:
            violations.append(
                RuleViolation(
                    rule_id="VOICE_RANGE_BOUNDS",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=(
                        f"{VOICE_NAMES[idx]} pitch {pitch} out of allowable range "
                        f"[{min_p}, {max_p}]"
                    ),
                    voices=(idx,),
                )
            )
    return violations


def check_voice_crossing(voicing: Any) -> list[RuleViolation]:
    """
    Checks for voice crossing: Soprano >= Alto >= Tenor >= Bass.
    """
    s, a, t, b = to_satb(voicing)
    violations: list[RuleViolation] = []

    if s < a:
        violations.append(
            RuleViolation(
                rule_id="VOICE_CROSSING",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Voice crossing: Soprano ({s}) < Alto ({a})",
                voices=(0, 1),
            )
        )
    if a < t:
        violations.append(
            RuleViolation(
                rule_id="VOICE_CROSSING",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Voice crossing: Alto ({a}) < Tenor ({t})",
                voices=(1, 2),
            )
        )
    if t < b:
        violations.append(
            RuleViolation(
                rule_id="VOICE_CROSSING",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Voice crossing: Tenor ({t}) < Bass ({b})",
                voices=(2, 3),
            )
        )
    return violations


def check_voice_unison(voicing: Any) -> list[RuleViolation]:
    """
    Checks for adjacent voice unisons: strict descending order Soprano > Alto > Tenor > Bass.
    Equality between adjacent voices is strictly prohibited in 4-part classical harmony.
    """
    s, a, t, b = to_satb(voicing)
    violations: list[RuleViolation] = []

    if s == a:
        violations.append(
            RuleViolation(
                rule_id="VOICE_UNISON",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Voice unison: Soprano ({s}) == Alto ({a})",
                voices=(0, 1),
            )
        )
    if a == t:
        violations.append(
            RuleViolation(
                rule_id="VOICE_UNISON",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Voice unison: Alto ({a}) == Tenor ({t})",
                voices=(1, 2),
            )
        )
    if t == b:
        violations.append(
            RuleViolation(
                rule_id="VOICE_UNISON",
                severity="hard_gate",
                penalty=100000.0,
                description=f"Voice unison: Tenor ({t}) == Bass ({b})",
                voices=(2, 3),
            )
        )
    return violations


def check_texture_spacing(voicing: Any) -> list[RuleViolation]:
    """
    Checks for acoustic texture gaps (spacing limits):
    - Soprano - Alto <= 12 semitones (pure octave)
    - Alto - Tenor <= 12 semitones (pure octave)
    - Tenor - Bass <= 24 semitones (two octaves)
    """
    s, a, t, b = to_satb(voicing)
    violations: list[RuleViolation] = []

    if s - a > 12:
        violations.append(
            RuleViolation(
                rule_id="UPPER_VOICE_SPACING_LIMIT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Upper voice spacing limit exceeded: S ({s}) - A ({a}) = "
                    f"{s - a} > 12 semitones"
                ),
                voices=(0, 1),
            )
        )
    if a - t > 12:
        violations.append(
            RuleViolation(
                rule_id="UPPER_VOICE_SPACING_LIMIT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Upper voice spacing limit exceeded: A ({a}) - T ({t}) = "
                    f"{a - t} > 12 semitones"
                ),
                voices=(1, 2),
            )
        )
    if t - b > 24:
        violations.append(
            RuleViolation(
                rule_id="BASS_TENOR_SPACING_LIMIT",
                severity="hard_gate",
                penalty=100000.0,
                description=(
                    f"Bass-Tenor spacing limit exceeded: T ({t}) - B ({b}) = "
                    f"{t - b} > 24 semitones"
                ),
                voices=(2, 3),
            )
        )
    return violations


def validate_spacing(
    voicing: Any,
    ranges: Mapping[int, tuple[int, int]] | None = None,
    allow_extended: bool = False,
) -> list[RuleViolation]:
    """
    Runs full static texture checks on a single voicing vertical slice.
    """
    violations = []
    violations.extend(check_voice_ranges(voicing, ranges=ranges, allow_extended=allow_extended))
    violations.extend(check_voice_crossing(voicing))
    violations.extend(check_voice_unison(voicing))
    violations.extend(check_texture_spacing(voicing))
    return violations
