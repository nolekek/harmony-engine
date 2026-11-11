"""
Non-Chord Tones (Неаккордовые звуки) and Melodic Embellishments Validator.
Implements Brigade Textbook rules for:
- Задержания (Suspensions): приготовление, задержание на сильной доле, разрешение на ступень вниз/вверх.
- Проходящие звуки (Passing tones): поступенное заполнение терций на слабой доле.
- Вспомогательные звуки (Neighbor/Auxiliary tones): шаг на секунду от аккордового тона и возврат обратно.
- Предъёмы (Anticipations): взятие аккордового тона следующей гармонии на слабой доле.
"""

from enum import Enum
from typing import Any, Sequence
from dataclasses import dataclass
from src.harmony.core.types import RuleViolation, Voicing, to_satb, parse_key


class NonChordToneType(str, Enum):
    NONE = "none"
    PASSING = "passing"           # Проходящий
    NEIGHBOR = "neighbor"         # Вспомогательный
    SUSPENSION = "suspension"     # Задержание
    ANTICIPATION = "anticipation" # Предъём


@dataclass
class NonChordToneAnalysis:
    tone_type: NonChordToneType
    voice_index: int              # 0: S, 1: A, 2: T, 3: B
    pitch: int
    is_valid: bool
    violations: list[RuleViolation]


def classify_nct(
    prev_pitch: int | None,
    curr_pitch: int,
    next_pitch: int | None,
    chord_pcs: Any,
    is_downbeat: bool = False,
) -> str | None:
    """
    Classifies a soprano melodic pitch relative to chord pitch classes.
    Returns: 'passing' | 'neighbor' | 'suspension' | 'chord_tone' | None
    
    Rules:
    - chord_tone: curr_pitch % 12 is in chord_pcs.
    - suspension: tone held from previous pitch (d1 == 0), on downbeat (is_downbeat == True),
                  resolves down by step (d2 in (-1, -2)).
    - passing: moves in the same direction by step (abs(d1) in (1, 2), abs(d2) in (1, 2), d1 * d2 > 0)
               between surrounding pitches.
    - neighbor: moves by step (abs(d1) in (1, 2)) and returns back to the same pitch (next_pitch == prev_pitch).
    """
    norm_pcs = {pc % 12 for pc in chord_pcs}
    if (curr_pitch % 12) in norm_pcs:
        return "chord_tone"

    if prev_pitch is None or next_pitch is None:
        return None

    d1 = curr_pitch - prev_pitch
    d2 = next_pitch - curr_pitch

    # Suspension: held note on downbeat resolving down by step
    if d1 == 0 and is_downbeat and d2 in (-1, -2):
        return "suspension"

    # Passing tone: stepwise motion in the same direction
    if abs(d1) in (1, 2) and abs(d2) in (1, 2) and (d1 * d2 > 0):
        return "passing"

    # Neighbor tone: step and return
    if abs(d1) in (1, 2) and next_pitch == prev_pitch:
        return "neighbor"

    return None


def classify_melodic_tone(
    prev_pitch: int,
    curr_pitch: int,
    next_pitch: int,
    is_curr_chord_tone: bool,
    is_downbeat: bool = False,
) -> tuple[NonChordToneType, list[RuleViolation]]:
    """
    Classifies a pitch between two surrounding pitches (prev -> curr -> next).
    Returns (NonChordToneType, violations).
    """
    if is_curr_chord_tone:
        return NonChordToneType.NONE, []

    violations: list[RuleViolation] = []
    d1 = curr_pitch - prev_pitch
    d2 = next_pitch - curr_pitch

    # 1. Задержание (Suspension):
    # Tone held from previous chord (d1 == 0), appears on downbeat, resolves down by step (d2 == -1 or -2)
    if d1 == 0 and is_downbeat:
        if d2 in (-1, -2):
            return NonChordToneType.SUSPENSION, []
        elif d2 in (1, 2):
            # Upward suspension (задержание снизу) - permitted in Brigade, but rarer
            return NonChordToneType.SUSPENSION, []
        else:
            violations.append(
                RuleViolation(
                    rule_id="NCT_SUSPENSION_UNRESOLVED",
                    severity="hard_gate",
                    penalty=100000.0,
                    description=f"Suspension at pitch {curr_pitch} must resolve by step, but leaped by {d2} semitones.",
                )
            )
            return NonChordToneType.SUSPENSION, violations

    # 2. Проходящий звук (Passing tone):
    # Must move in the same direction by step: prev -> curr (step) -> next (step)
    if abs(d1) in (1, 2) and abs(d2) in (1, 2) and (d1 * d2 > 0):
        if is_downbeat:
            # Downbeat passing tone is permitted (тяжелый проходящий), but soft-penalized in classical vocal style
            violations.append(
                RuleViolation(
                    rule_id="NCT_PASSING_ON_DOWNBEAT",
                    severity="soft_penalty",
                    penalty=3.0,
                    description=f"Accented (downbeat) passing tone at pitch {curr_pitch}.",
                )
            )
        return NonChordToneType.PASSING, violations

    # 3. Вспомогательный звук (Neighbor / Auxiliary tone):
    # Moves by step and returns back: prev -> curr (step) -> prev (step back)
    if abs(d1) in (1, 2) and (curr_pitch + d2 == prev_pitch):
        return NonChordToneType.NEIGHBOR, []

    # 4. Предъём (Anticipation):
    # Steps into tone on weak beat, next chord holds same tone (d2 == 0)
    if abs(d1) in (1, 2) and d2 == 0 and not is_downbeat:
        return NonChordToneType.ANTICIPATION, []

    # If it is not a chord tone and fits none of the classical NCT patterns -> illegal leap to non-chord tone!
    violations.append(
        RuleViolation(
            rule_id="NCT_ILLEGAL_LEAP_NON_CHORD_TONE",
            severity="hard_gate",
            penalty=100000.0,
            description=f"Illegal non-chord tone at pitch {curr_pitch}: unresolved leap (d1={d1}, d2={d2}).",
        )
    )
    return NonChordToneType.NONE, violations


def check_voice_embellishments(
    prev_voicing: Any,
    curr_voicing: Any,
    next_voicing: Any,
    curr_chord_tones: set[int],
    is_downbeat: bool = False,
) -> list[RuleViolation]:
    """
    Validates all 4 voices across a 3-chord window (prev -> curr -> next)
    for strict classical handling of non-chord embellishments.
    """
    violations: list[RuleViolation] = []
    p_satb = to_satb(prev_voicing)
    c_satb = to_satb(curr_voicing)
    n_satb = to_satb(next_voicing)

    for v_idx in range(4):
        p_pitch = p_satb[v_idx]
        c_pitch = c_satb[v_idx]
        n_pitch = n_satb[v_idx]

        is_chord_tone = (c_pitch % 12) in {t % 12 for t in curr_chord_tones}
        _, v_violations = classify_melodic_tone(
            prev_pitch=p_pitch,
            curr_pitch=c_pitch,
            next_pitch=n_pitch,
            is_curr_chord_tone=is_chord_tone,
            is_downbeat=is_downbeat,
        )
        violations.extend(v_violations)

    return violations
