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
]
