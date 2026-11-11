"""
Key detection and canonical keys catalog.
Provides 24 canonical keys (12 major, 12 harmonic minor) and automatic key detection.
"""

from __future__ import annotations

from typing import Any, Sequence
from src.harmony.core.types import Key

CANONICAL_KEYS = [
    # 12 Majors
    {"tonic": "C", "mode": "Major", "name": "C-dur (До мажор)", "fifths": 0},
    {"tonic": "G", "mode": "Major", "name": "G-dur (Соль мажор)", "fifths": 1},
    {"tonic": "D", "mode": "Major", "name": "D-dur (Ре мажор)", "fifths": 2},
    {"tonic": "A", "mode": "Major", "name": "A-dur (Ля мажор)", "fifths": 3},
    {"tonic": "E", "mode": "Major", "name": "E-dur (Ми мажор)", "fifths": 4},
    {"tonic": "B", "mode": "Major", "name": "H-dur (Си мажор)", "fifths": 5},
    {"tonic": "F#", "mode": "Major", "name": "F#-dur (Фа-диез мажор)", "fifths": 6},
    {"tonic": "Db", "mode": "Major", "name": "Des-dur (Ре-бемоль мажор)", "fifths": -5},
    {"tonic": "Ab", "mode": "Major", "name": "As-dur (Ля-бемоль мажор)", "fifths": -4},
    {"tonic": "Eb", "mode": "Major", "name": "Es-dur (Ми-бемоль мажор)", "fifths": -3},
    {"tonic": "Bb", "mode": "Major", "name": "B-dur (Си-бемоль мажор)", "fifths": -2},
    {"tonic": "F", "mode": "Major", "name": "F-dur (Фа мажор)", "fifths": -1},

    # 12 Harmonic Minors
    {"tonic": "A", "mode": "MinorHarmonic", "name": "a-moll (Ля минор)", "fifths": 0},
    {"tonic": "E", "mode": "MinorHarmonic", "name": "e-moll (Ми минор)", "fifths": 1},
    {"tonic": "B", "mode": "MinorHarmonic", "name": "h-moll (Си минор)", "fifths": 2},
    {"tonic": "F#", "mode": "MinorHarmonic", "name": "fis-moll (Фа-диез минор)", "fifths": 3},
    {"tonic": "C#", "mode": "MinorHarmonic", "name": "cis-moll (До-диез минор)", "fifths": 4},
    {"tonic": "G#", "mode": "MinorHarmonic", "name": "gis-moll (Соль-диез минор)", "fifths": 5},
    {"tonic": "D#", "mode": "MinorHarmonic", "name": "dis-moll (Ре-диез минор)", "fifths": 6},
    {"tonic": "Bb", "mode": "MinorHarmonic", "name": "b-moll (Си-бемоль минор)", "fifths": -5},
    {"tonic": "F", "mode": "MinorHarmonic", "name": "f-moll (Фа минор)", "fifths": -4},
    {"tonic": "C", "mode": "MinorHarmonic", "name": "c-moll (До минор)", "fifths": -3},
    {"tonic": "G", "mode": "MinorHarmonic", "name": "g-moll (Соль минор)", "fifths": -2},
    {"tonic": "D", "mode": "MinorHarmonic", "name": "d-moll (Ре минор)", "fifths": -1},
]


import math

# Krumhansl-Kessler key profiles (distribution over 12 semitones from tonic)
# Major profile: tonic, b2, 2, b3, 3, 4, #4, 5, b6, 6, b7, 7
KRUMHANSL_MAJOR: tuple[float, ...] = (
    6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88
)
# Minor profile: tonic, b2, 2, b3, 3, 4, #4, 5, b6, 6, b7, 7
KRUMHANSL_MINOR: tuple[float, ...] = (
    6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17
)

# Standard duration weights (relative to quarter note = 1.0)
DURATION_WEIGHTS: dict[str, float] = {
    "whole": 4.0,
    "dotted_whole": 6.0,
    "half": 2.0,
    "dotted_half": 3.0,
    "quarter": 1.0,
    "dotted_quarter": 1.5,
    "eighth": 0.5,
    "dotted_eighth": 0.75,
    "sixteenth": 0.25,
    "dotted_sixteenth": 0.375,
    "thirtysecond": 0.125,
    "32nd": 0.125,
    "16th": 0.25,
    "8th": 0.5,
    "4th": 1.0,
}


def _parse_duration(val: Any) -> float:
    """Parse duration specifier (name, numeric, or dotted) to quarter-note weight."""
    if val is None:
        return 1.0
    if isinstance(val, (int, float)):
        return float(val) if val > 0 else 1.0
    if isinstance(val, str):
        s = val.strip().lower()
        if s in DURATION_WEIGHTS:
            return DURATION_WEIGHTS[s]
        try:
            num = float(s)
            return num if num > 0 else 1.0
        except ValueError:
            pass
        if s.endswith("."):
            base = s[:-1]
            return DURATION_WEIGHTS.get(base, 1.0) * 1.5
        if s.startswith("dotted_"):
            base = s[7:]
            return DURATION_WEIGHTS.get(base, 1.0) * 1.5
    return 1.0


def _pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Calculate Pearson correlation coefficient r between two 12-dimensional vectors."""
    n = len(x)
    if n == 0 or len(y) != n:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = 0.0
    var_x = 0.0
    var_y = 0.0
    for xi, yi in zip(x, y):
        dx = xi - mx
        dy = yi - my
        num += dx * dy
        var_x += dx * dx
        var_y += dy * dy
    denom = math.sqrt(var_x * var_y)
    if denom <= 1e-9:
        return 0.0
    return max(-1.0, min(1.0, num / denom))


def detect_key_from_melody(melody: Sequence[int | dict[str, Any]]) -> dict[str, Any]:
    """
    Auto-detects the musical key from a soprano melody sequence using a weighted
    Krumhansl-Schmuckler profile correlation algorithm.

    Scores candidates based on:
    - Pearson correlation of pitch-class distribution (weighted by note duration)
      with empirical Major and Minor key profiles (Krumhansl & Kessler).
    - Modest final tonic bonus (+12.0) to avoid hijacking half-cadence endings
      (such as C D E F G ending on G dominant or A B C D E ending on E dominant).
    - Melodic cadence bonuses for authentic (V -> I, +8.0) and deceptive/interrupted
      (V -> VI, +5.0) motions at the end of the melody.
    """
    pitches: list[int] = []
    durations: list[float] = []

    for m in melody:
        if isinstance(m, dict):
            if "pitch" not in m:
                continue
            pitches.append(int(m["pitch"]))
            durations.append(_parse_duration(m.get("duration")))
        elif hasattr(m, "pitch"):
            pitches.append(int(getattr(m, "pitch")))
            durations.append(_parse_duration(getattr(m, "duration", 1.0)))
        else:
            pitches.append(int(m))
            durations.append(1.0)

    if not pitches:
        return CANONICAL_KEYS[0]

    last_pc = pitches[-1] % 12
    penult_pc = pitches[-2] % 12 if len(pitches) >= 2 else None

    # Compute duration-weighted pitch class distribution vector (12 bins)
    x = [0.0] * 12
    for p, d in zip(pitches, durations):
        x[p % 12] += d

    best_key = CANONICAL_KEYS[0]
    best_score = -999999.0

    for cand in CANONICAL_KEYS:
        k_obj = Key(tonic=cand["tonic"], mode=cand["mode"])
        tonic_pc = k_obj.tonic_pc
        is_minor = "minor" in cand["mode"].lower()

        prof = KRUMHANSL_MINOR if is_minor else KRUMHANSL_MAJOR
        # Shift profile so that index 0 corresponds to cand tonic_pc
        shifted = [prof[(i - tonic_pc) % 12] for i in range(12)]
        r = _pearson_correlation(x, shifted)

        # Scale correlation to base score [-100.0, 100.0]
        score = r * 100.0

        # Modest final tonic bonus (capped <= 15.0)
        if last_pc == tonic_pc:
            score += 12.0

        # Cadence detection: V -> I or V -> VI at melody conclusion
        if penult_pc is not None:
            dom_pc = (tonic_pc + 7) % 12
            vi_pc = (tonic_pc + (8 if is_minor else 9)) % 12

            if penult_pc == dom_pc and last_pc == tonic_pc:
                score += 8.0
            elif penult_pc == dom_pc and (last_pc == vi_pc or (is_minor and last_pc == (tonic_pc + 9) % 12)):
                score += 5.0

        if score > best_score:
            best_score = score
            best_key = cand

    return best_key
