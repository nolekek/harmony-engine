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


def detect_key_from_melody(melody: Sequence[int | dict[str, Any]]) -> dict[str, Any]:
    """
    Auto-detects the musical key from a soprano melody sequence.
    Scores candidates based on:
    - Final cadence tone (degree I is decisive)
    - Starting tone (degrees I, III, V)
    - Harmonic scale degree fit (bonus for scale notes, penalty for non-scale)
    - Harmonic minor leading tone detection
    """
    pitches: list[int] = []
    for m in melody:
        if isinstance(m, dict):
            pitches.append(int(m["pitch"]))
        else:
            pitches.append(int(m))

    if not pitches:
        return CANONICAL_KEYS[0]

    pcs = [p % 12 for p in pitches]
    first_pc = pcs[0]
    last_pc = pcs[-1]

    best_key = CANONICAL_KEYS[0]
    best_score = -9999.0

    for cand in CANONICAL_KEYS:
        k_obj = Key(tonic=cand["tonic"], mode=cand["mode"])
        scale_pcs = set(k_obj.scale_pcs)
        tonic_pc = k_obj.tonic_pc
        is_minor = "minor" in cand["mode"].lower()

        score = 0.0

        # 1. Final note: in classical melodies, almost universally ends on degree I (tonic)
        if last_pc == tonic_pc:
            score += 60.0
        elif last_pc in scale_pcs:
            score += 15.0
        else:
            score -= 40.0

        # 2. First note: typically degrees I, III, or V
        third_pc = (tonic_pc + (3 if is_minor else 4)) % 12
        fifth_pc = (tonic_pc + 7) % 12
        if first_pc == tonic_pc:
            score += 25.0
        elif first_pc in (third_pc, fifth_pc):
            score += 15.0
        elif first_pc in scale_pcs:
            score += 5.0
        else:
            score -= 20.0

        # 3. Fit of all notes into the scale
        for pc in pcs:
            if pc in scale_pcs:
                score += 8.0
            else:
                score -= 15.0

        # 4. Leading tone bonus for harmonic minor
        if is_minor:
            leading_pc = (tonic_pc + 11) % 12
            if leading_pc in pcs:
                score += 35.0  # Raised 7th degree strongly indicates harmonic minor

        if score > best_score:
            best_score = score
            best_key = cand

    return best_key
