"""
Chromatic Voice Leading, Secondary Dominants, and False Relation (Переченье) Validator.
Strictly implements Brigade textbook rules (Способин, Дубовский et al., Глава 26, 28):
1. Переченье (Cross-relation / False relation):
   Хроматическое видоизменение ступени (например, F -> F# или Bb -> B) должно происходить
   в одном и том же голосе. Появление хроматического полутона в разных голосах
   при одновременном звучании или непосредственном следовании строго запрещено (hard_gate).
   ВАЖНО: Диатонические малые секунды (например, E-F, B-C, или VII-I ступени) НЕ являются переченьем!
"""

from typing import Any, Sequence
from src.harmony.core.types import RuleViolation, Voicing, to_satb, parse_key

VOICE_NAMES = ["Soprano", "Alto", "Tenor", "Bass"]

MAJOR_SCALE_STEPS = {0, 2, 4, 5, 7, 9, 11}
MINOR_HARMONIC_STEPS = {0, 2, 3, 5, 7, 8, 11}


def get_diatonic_pcs(key: Any) -> set[int]:
    """Returns set of diatonic pitch classes for the key."""
    if key is None:
        return MAJOR_SCALE_STEPS
    tonic_pc, mode = parse_key(key)
    steps = MINOR_HARMONIC_STEPS if "minor" in mode.lower() else MAJOR_SCALE_STEPS
    return {(tonic_pc + s) % 12 for s in steps}


def check_false_relation(prev_voicing: Any, curr_voicing: Any, key: Any = None) -> list[RuleViolation]:
    """
    Detects False Relation (Переченье):
    Occurs when a chromatic alteration of a diatonic scale step appears in a DIFFERENT voice
    than the original voice that sounded the diatonic step in the previous chord.
    """
    violations: list[RuleViolation] = []
    p_satb = to_satb(prev_voicing)
    c_satb = to_satb(curr_voicing)

    diatonic_pcs = get_diatonic_pcs(key)

    p_pcs = [(i, p % 12, p) for i, p in enumerate(p_satb)]
    c_pcs = [(j, c % 12, c) for j, c in enumerate(c_satb)]

    for j, c_pc, c_pitch in c_pcs:
        for i, p_pc, p_pitch in p_pcs:
            # If both pitch classes are diatonic in the current key, this is a diatonic interval (e.g. E-F, B-C),
            # NOT a chromatic alteration / false relation!
            if p_pc in diatonic_pcs and c_pc in diatonic_pcs:
                continue

            # Check for chromatic semitone relationship (|p_pc - c_pc| == 1 or 11)
            diff = abs(c_pc - p_pc)
            is_chromatic_semitone = (diff == 1 or diff == 11)

            if is_chromatic_semitone and (i != j):
                # Voice i had the diatonic note, but voice j introduced the chromatic alteration!
                voice_i_moved_to_chromatic = (c_satb[i] % 12 == c_pc)
                voice_j_came_from_diatonic = (p_satb[j] % 12 == p_pc)

                if not voice_i_moved_to_chromatic and not voice_j_came_from_diatonic:
                    violations.append(
                        RuleViolation(
                            rule_id="FALSE_RELATION_PERECHENIE",
                            severity="hard_gate",
                            penalty=100000.0,
                            description=(
                                f"False relation (переченье) between {VOICE_NAMES[i]} "
                                f"(pitch {p_pitch}, pc {p_pc}) and {VOICE_NAMES[j]} "
                                f"(pitch {c_pitch}, pc {c_pc}). "
                                f"Chromatic alteration must occur within the same voice."
                            ),
                        )
                    )

    return violations


def validate_chromatic_rules(prev_voicing: Any, curr_voicing: Any, key: Any = None) -> list[RuleViolation]:
    """Master validator for chromatic voice leading and false relation."""
    violations: list[RuleViolation] = []
    violations.extend(check_false_relation(prev_voicing, curr_voicing, key=key))
    return violations
