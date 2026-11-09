"""
Core domain model for the four-part harmony engine (SATB).

Provides fundamental abstractions based on classical Russian music theory
(Бригадный учебник гармонии — Способин, Дубовский, Евсеев, Соколов):
- Pitch, PitchClass, ScaleDegree, Interval
- Key, Mode
- ChordFunction, Inversion, ChordDefinition
- Voicing, Spacing, Voice
"""

from __future__ import annotations

from .chord import ChordDefinition, ChordFunction, Inversion
from .key import Key, Mode
from .modulation import (
    FirstDegreeRelations,
    PivotChord,
    RelatedKeyInfo,
    SecondaryDominant,
    build_modulation_plan,
    find_pivot_chords,
    get_related_keys_first_degree,
    get_secondary_dominants,
)
from .pitch import Interval, Pitch, PitchClass, ScaleDegree
from .voicing import Spacing, Voice, Voicing

__all__ = [
    # Pitch & scale domain
    "PitchClass",
    "Pitch",
    "ScaleDegree",
    "Interval",
    # Key & mode domain
    "Mode",
    "Key",
    # Chord & harmonic function domain
    "ChordFunction",
    "Inversion",
    "ChordDefinition",
    # Voicing & texture domain
    "Voicing",
    "Spacing",
    "Voice",
    # Modulation & tonality domain
    "FirstDegreeRelations",
    "RelatedKeyInfo",
    "get_related_keys_first_degree",
    "PivotChord",
    "find_pivot_chords",
    "build_modulation_plan",
    "SecondaryDominant",
    "get_secondary_dominants",
]
