"""
Core domain model: Key and Mode.

Defines tonality, modal scale structures, degree calculations, note membership,
and modal melodic tendencies (тяготения) in classical functional harmony
(Бригадный учебник).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Optional, Union

from .pitch import Interval, Pitch, PitchClass, ScaleDegree


class Mode(str, Enum):
    """
    Musical modes used in classical functional harmony.
    
    Major (натуральный мажор)
    MinorHarmonic (гармонический минор - основной рабочий лад классической гармонии)
    MinorNatural (натуральный минор)
    MinorMelodic (мелодический минор - восходящий)
    """

    MAJOR = "Major"
    MINOR_HARMONIC = "MinorHarmonic"
    MINOR_NATURAL = "MinorNatural"
    MINOR_MELODIC = "MinorMelodic"

    @property
    def intervals(self) -> tuple[int, ...]:
        """Semitone offsets from tonic for degrees I through VII."""
        if self == Mode.MAJOR:
            return (0, 2, 4, 5, 7, 9, 11)
        if self == Mode.MINOR_HARMONIC:
            return (0, 2, 3, 5, 7, 8, 11)
        if self == Mode.MINOR_NATURAL:
            return (0, 2, 3, 5, 7, 8, 10)
        if self == Mode.MINOR_MELODIC:
            return (0, 2, 3, 5, 7, 9, 11)
        raise ValueError(f"Unknown mode: {self}")

    @property
    def is_major(self) -> bool:
        """True if the mode has a major third (4 semitones)."""
        return self == Mode.MAJOR

    @property
    def is_minor(self) -> bool:
        """True if the mode has a minor third (3 semitones)."""
        return self in (Mode.MINOR_HARMONIC, Mode.MINOR_NATURAL, Mode.MINOR_MELODIC)

    @classmethod
    def from_str(cls, s: str) -> Mode:
        """
        Parse Mode from diverse naming conventions.
        
        Supports: 'Major', 'dur', 'мажор', 'MinorHarmonic', 'moll', 'minor', 'гармонический минор', etc.
        """
        cleaned = s.strip().lower().replace("-", "_").replace(" ", "_")
        if cleaned in ("major", "dur", "maj", "мажор"):
            return cls.MAJOR
        if cleaned in ("minorharmonic", "minor_harmonic", "moll_harmonic", "гармонический_минор", "harmonic_minor"):
            return cls.MINOR_HARMONIC
        if cleaned in ("minornatural", "minor_natural", "натуральный_минор", "natural_minor"):
            return cls.MINOR_NATURAL
        if cleaned in ("minormelodic", "minor_melodic", "мелодический_минор", "melodic_minor"):
            return cls.MINOR_MELODIC
        if cleaned in ("minor", "moll", "минор"):
            # In classical harmony (Бригадный), unqualified minor is harmonic minor
            return cls.MINOR_HARMONIC
        raise ValueError(f"Unknown mode representation: '{s}'.")


@dataclass(frozen=True, slots=True)
class Key:
    """
    Tonality defined by a tonic PitchClass and a Mode.
    
    Provides scale degree mapping, pitch membership queries, and melodic tendencies
    (ладовые тяготения: вводный тон VII, неустойчивые ступени II, IV, VI, VII).
    """

    tonic: PitchClass
    mode: Mode

    def __post_init__(self) -> None:
        if isinstance(self.tonic, str):
            object.__setattr__(self, "tonic", PitchClass.from_name(self.tonic))
        elif isinstance(self.tonic, int) and not isinstance(self.tonic, PitchClass):
            object.__setattr__(self, "tonic", PitchClass(self.tonic % 12))
        if isinstance(self.mode, str):
            object.__setattr__(self, "mode", Mode.from_str(self.mode))

    # Classical unstable scale degrees in Brigada harmony
    UNSTABLE_DEGREES: ClassVar[tuple[ScaleDegree, ...]] = (
        ScaleDegree(2, 0),
        ScaleDegree(4, 0),
        ScaleDegree(6, 0),
        ScaleDegree(7, 0),
    )

    # Classical stable scale degrees (tonic triad degrees)
    STABLE_DEGREES: ClassVar[tuple[ScaleDegree, ...]] = (
        ScaleDegree(1, 0),
        ScaleDegree(3, 0),
        ScaleDegree(5, 0),
    )

    @classmethod
    def from_string(cls, s: str) -> Key:
        """
        Parse Key from string representations.
        
        Examples:
        - 'C Major', 'C:Major', 'C_Major', 'C-dur'
        - 'A MinorHarmonic', 'a-moll', 'G:Minor'
        - 'F# Major', 'Eb MinorHarmonic'
        """
        cleaned = s.strip()
        # Check classic German notation: 'C-dur', 'a-moll', 'c#-moll', 'Es-dur'
        german_match = re.match(r"^([A-Ga-g][#b♭♯]?)[-_](dur|moll)$", cleaned, re.IGNORECASE)
        if german_match:
            note_str, mode_str = german_match.groups()
            tonic = PitchClass.from_name(note_str)
            mode = Mode.MAJOR if mode_str.lower() == "dur" else Mode.MINOR_HARMONIC
            return cls(tonic=tonic, mode=mode)

        # Split on whitespace, colon or underscore
        parts = re.split(r"[\s:_]+", cleaned)
        if len(parts) == 1:
            # Single letter capitalized might imply major, lower might imply minor
            raw = parts[0]
            if raw[0].islower():
                return cls(tonic=PitchClass.from_name(raw), mode=Mode.MINOR_HARMONIC)
            return cls(tonic=PitchClass.from_name(raw), mode=Mode.MAJOR)
        if len(parts) >= 2:
            tonic = PitchClass.from_name(parts[0])
            mode_str = "_".join(parts[1:])
            mode = Mode.from_str(mode_str)
            return cls(tonic=tonic, mode=mode)

        raise ValueError(f"Cannot parse Key from '{s}'.")

    @property
    def name(self) -> str:
        """String representation like 'C Major' or 'A MinorHarmonic'."""
        return f"{self.tonic.sharp_name} {self.mode.value}"

    @property
    def scale_pitch_classes(self) -> list[PitchClass]:
        """Ordered list of the 7 scale PitchClasses (I to VII)."""
        return [
            PitchClass((self.tonic.value + delta) % 12)
            for delta in self.mode.intervals
        ]

    @property
    def scale_pitch_classes_set(self) -> frozenset[PitchClass]:
        """Frozenset of diatonic pitch classes in this key."""
        return frozenset(self.scale_pitch_classes)

    def get_scale_degrees(self) -> list[ScaleDegree]:
        """Returns standard scale degrees I..VII."""
        return [ScaleDegree(i, 0) for i in range(1, 8)]

    def pitch_class_for_degree(self, degree: Union[ScaleDegree, int]) -> PitchClass:
        """
        Compute the PitchClass for a given scale degree (1..7 or ScaleDegree).
        
        Properly applies chromatic alterations if present (e.g., VII# in minor, bII).
        """
        if isinstance(degree, int):
            if not (1 <= degree <= 7):
                raise ValueError(f"Degree must be in 1..7, got {degree}.")
            delta = self.mode.intervals[degree - 1]
            return PitchClass((self.tonic.value + delta) % 12)

        if isinstance(degree, ScaleDegree):
            base_delta = self.mode.intervals[degree.degree - 1]
            total_delta = base_delta + degree.alteration
            return PitchClass((self.tonic.value + total_delta) % 12)

        raise TypeError(f"Expected ScaleDegree or int, got {type(degree)}.")

    def degree_for_pitch_class(
        self,
        pc: Union[PitchClass, Pitch, int],
        prefer_flat: bool = True,
    ) -> Optional[ScaleDegree]:
        """
        Find the ScaleDegree corresponding to a pitch class, or None if non-scale.
        
        prefer_flat: If True, prefer 'bII', 'bVI', 'bVII' over 'I#', 'V#', 'VI#'.
        """
        target_pc = pc.pitch_class if isinstance(pc, Pitch) else (
            pc if isinstance(pc, PitchClass) else PitchClass(pc % 12)
        )

        # 1. Check natural scale degrees first
        scale_pcs = self.scale_pitch_classes
        for idx, scale_pc in enumerate(scale_pcs):
            if scale_pc == target_pc:
                return ScaleDegree(idx + 1, 0)

        # 2. Check standard classical chromatic alterations
        # In classical harmony (Способин / Бригада):
        # bII (Neapolitan), #IV (tritone), bVI (minor subdominant), bVII (natural 7), #VII (leading tone in natural minor)
        semitones_from_tonic = (target_pc.value - self.tonic.value) % 12

        if prefer_flat:
            candidates = [
                ScaleDegree(2, -1),  # bII
                ScaleDegree(4, 1),   # #IV
                ScaleDegree(6, -1),  # bVI
                ScaleDegree(7, -1),  # bVII
                ScaleDegree(7, 1),   # #VII
                ScaleDegree(1, 1),   # #I
                ScaleDegree(2, 1),   # #II
                ScaleDegree(3, -1),  # bIII
                ScaleDegree(5, 1),   # #V
            ]
        else:
            candidates = [
                ScaleDegree(1, 1),   # #I
                ScaleDegree(4, 1),   # #IV
                ScaleDegree(5, 1),   # #V
                ScaleDegree(7, 1),   # #VII
                ScaleDegree(2, -1),  # bII
                ScaleDegree(6, -1),  # bVI
                ScaleDegree(7, -1),  # bVII
                ScaleDegree(2, 1),   # #II
                ScaleDegree(3, -1),  # bIII
            ]

        for sd in candidates:
            if self.pitch_class_for_degree(sd) == target_pc:
                return sd

        return None

    def contains(self, note: Union[Pitch, PitchClass, int]) -> bool:
        """Check if pitch or pitch class is a diatonic member of this key."""
        target_pc = note.pitch_class if isinstance(note, Pitch) else (
            note if isinstance(note, PitchClass) else PitchClass(note % 12)
        )
        return target_pc in self.scale_pitch_classes_set

    # -------------------------------------------------------------------------
    # Modal attractions & Melodic tendencies (Ладовые тяготения)
    # -------------------------------------------------------------------------

    @property
    def leading_tone(self) -> PitchClass:
        """
        The leading tone (вводный тон, VII degree).
        
        In Major and MinorHarmonic, this is located 1 semitone below the tonic.
        """
        return self.pitch_class_for_degree(ScaleDegree(7, 0))

    @property
    def unstable_degrees(self) -> tuple[ScaleDegree, ...]:
        """Unstable scale degrees (неустойчивые ступени II, IV, VI, VII)."""
        return self.UNSTABLE_DEGREES

    @property
    def stable_degrees(self) -> tuple[ScaleDegree, ...]:
        """Stable scale degrees (устойчивые ступени I, III, V)."""
        return self.STABLE_DEGREES

    @property
    def unstable_pitch_classes(self) -> tuple[PitchClass, ...]:
        """PitchClasses of unstable scale degrees (II, IV, VI, VII)."""
        return tuple(self.pitch_class_for_degree(deg) for deg in self.UNSTABLE_DEGREES)

    @property
    def stable_pitch_classes(self) -> tuple[PitchClass, ...]:
        """PitchClasses of stable scale degrees (I, III, V)."""
        return tuple(self.pitch_class_for_degree(deg) for deg in self.STABLE_DEGREES)

    def is_stable(self, note: Union[Pitch, PitchClass, ScaleDegree, int]) -> bool:
        """Check if note corresponds to a stable degree (I, III, V)."""
        if isinstance(note, ScaleDegree):
            return note.degree in (1, 3, 5) and note.alteration == 0
        pc = note.pitch_class if isinstance(note, Pitch) else (
            note if isinstance(note, PitchClass) else PitchClass(note % 12)
        )
        return pc in self.stable_pitch_classes

    def is_unstable(self, note: Union[Pitch, PitchClass, ScaleDegree, int]) -> bool:
        """Check if note corresponds to an unstable degree (II, IV, VI, VII)."""
        if isinstance(note, ScaleDegree):
            return note.degree in (2, 4, 6, 7)
        pc = note.pitch_class if isinstance(note, Pitch) else (
            note if isinstance(note, PitchClass) else PitchClass(note % 12)
        )
        return pc in self.unstable_pitch_classes

    def is_leading_tone(self, note: Union[Pitch, PitchClass, ScaleDegree, int]) -> bool:
        """Check if note is the leading tone (вводный тон VII)."""
        if isinstance(note, ScaleDegree):
            return note.degree == 7
        pc = note.pitch_class if isinstance(note, Pitch) else (
            note if isinstance(note, PitchClass) else PitchClass(note % 12)
        )
        return pc == self.leading_tone

    def get_tendency_resolutions(self, degree: ScaleDegree) -> list[ScaleDegree]:
        """
        Return the classical melodic resolution targets for an unstable degree.
        
        VII -> I  (leading tone resolves up a half step to tonic)
        IV  -> III (subdominant tritone member resolves down to third)
        VI  -> V   (resolves down to fifth)
        II  -> I, III (supertonic resolves down to tonic or up to third)
        """
        if degree.degree == 7:
            return [ScaleDegree(1, 0)]
        if degree.degree == 4:
            return [ScaleDegree(3, 0)]
        if degree.degree == 6:
            return [ScaleDegree(5, 0)]
        if degree.degree == 2:
            return [ScaleDegree(1, 0), ScaleDegree(3, 0)]
        return []

    def get_pitch_tendency_resolutions(self, note: Union[Pitch, PitchClass, int]) -> list[PitchClass]:
        """Return target PitchClasses for natural tendency resolution of a given note."""
        sd = self.degree_for_pitch_class(note)
        if sd is None:
            return []
        target_degrees = self.get_tendency_resolutions(sd)
        return [self.pitch_class_for_degree(tgt) for tgt in target_degrees]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Key(tonic={self.tonic.sharp_name}, mode={self.mode.value})"
