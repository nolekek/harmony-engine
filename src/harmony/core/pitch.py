"""
Core domain model: Pitch, PitchClass, ScaleDegree, and Interval.

Provides fundamental representations of musical pitch in 12-tone equal temperament (12-TET),
conforming to standard MIDI specifications and Russian classical music theory
(Бригадный учебник гармонии).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar, Optional, Union


_SHARP_NAMES: tuple[str, ...] = (
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
)
_FLAT_NAMES: tuple[str, ...] = (
    "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"
)
_RUSSIAN_NAMES: tuple[str, ...] = (
    "До", "До#", "Ре", "Ре#", "Ми", "Фа", "Фа#", "Соль", "Соль#", "Ля", "Ля#", "Си"
)


class PitchClass(IntEnum):
    """
    Pitch class representation in modulo 12 arithmetic (Z_12).
    
    Values range from 0 (C) through 11 (B).
    Enharmonic aliases are provided (e.g., C_SHARP == DB == 1).
    """

    C = 0
    C_SHARP = 1
    DB = 1
    D = 2
    D_SHARP = 3
    EB = 3
    E = 4
    F = 5
    F_SHARP = 6
    GB = 6
    G = 7
    G_SHARP = 8
    AB = 8
    A = 9
    A_SHARP = 10
    BB = 10
    B = 11

    @classmethod
    def from_name(cls, name: str) -> PitchClass:
        """
        Parse pitch class from note name string (e.g. 'C', 'C#', 'Db', 'F♯', 'B♭', 'H').
        """
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Pitch class name cannot be empty.")

        # Normalize unicode accidentals and case
        normalized = cleaned.replace("♯", "#").replace("♭", "b")
        upper = normalized.upper()

        name_map = {
            "C": 0, "B#": 0,
            "C#": 1, "DB": 1,
            "D": 2,
            "D#": 3, "EB": 3,
            "E": 4, "FB": 4,
            "F": 5, "E#": 5,
            "F#": 6, "GB": 6,
            "G": 7,
            "G#": 8, "AB": 8,
            "A": 9,
            "A#": 10, "BB": 10,
            "B": 11, "CB": 11, "H": 11,
        }

        if upper in name_map:
            return cls(name_map[upper])

        raise ValueError(f"Unknown pitch class name: '{name}'. Expected note like C, C#, Db, etc.")

    @classmethod
    def from_midi(cls, midi: int) -> PitchClass:
        """Convert MIDI number to PitchClass (midi % 12)."""
        return cls(midi % 12)

    @property
    def sharp_name(self) -> str:
        """Standard sharp note name (e.g. 'C#')."""
        return self.SHARP_NAMES[self.value]

    @property
    def flat_name(self) -> str:
        """Standard flat note name (e.g. 'Db')."""
        return self.FLAT_NAMES[self.value]

    @property
    def russian_name(self) -> str:
        """Russian note name (e.g. 'До#')."""
        return self.RUSSIAN_NAMES[self.value]

    def transpose(self, semitones: int) -> PitchClass:
        """Transpose pitch class by given number of semitones."""
        return PitchClass((self.value + semitones) % 12)

    def interval_to(self, other: PitchClass) -> int:
        """Number of semitones ascending from self to other modulo 12."""
        return (other.value - self.value) % 12

    def __int__(self) -> int:
        return self.midi_number

    def __str__(self) -> str:
        return self.sharp_name

    def __repr__(self) -> str:
        return f"PitchClass.{self.name}({self.value}, '{self.sharp_name}')"

    def __add__(self, other: Union[int, Interval]) -> PitchClass:
        if isinstance(other, int):
            return PitchClass((self.value + other) % 12)
        if isinstance(other, Interval):
            return PitchClass((self.value + other.semitones) % 12)
        return NotImplemented

    def __sub__(self, other: Union[int, Interval, PitchClass]) -> Union[PitchClass, int]:
        if isinstance(other, int):
            return PitchClass((self.value - other) % 12)
        if isinstance(other, Interval):
            return PitchClass((self.value - other.semitones) % 12)
        if isinstance(other, PitchClass):
            return (self.value - other.value) % 12
        return NotImplemented


PitchClass.SHARP_NAMES = _SHARP_NAMES  # type: ignore[attr-defined]
PitchClass.FLAT_NAMES = _FLAT_NAMES    # type: ignore[attr-defined]
PitchClass.RUSSIAN_NAMES = _RUSSIAN_NAMES  # type: ignore[attr-defined]


@dataclass(frozen=True, slots=True)
class Interval:
    """
    Musical interval representation with semitone distance and Russian music theory naming.
    
    Supports simple and compound intervals:
    0: ч1, 1: м2, 2: б2, 3: м3 (или ув2), 4: б3, 5: ч4, 6: тритон (ув4/ум5),
    7: ч5, 8: м6, 9: б6, 10: м7, 11: б7, 12: ч8, etc.
    """

    semitones: int
    name: str = ""

    STANDARD_NAMES: ClassVar[dict[int, str]] = {
        0: "ч1",
        1: "м2",
        2: "б2",
        3: "м3",
        4: "б3",
        5: "ч4",
        6: "тритон",
        7: "ч5",
        8: "м6",
        9: "б6",
        10: "м7",
        11: "б7",
        12: "ч8",
        13: "м9",
        14: "б9",
        15: "м10",
        16: "б10",
        17: "ч11",
        18: "ув11",
        19: "ч12",
        24: "ч15",
    }

    NAME_TO_SEMITONES: ClassVar[dict[str, int]] = {
        "ч1": 0, "прима": 0,
        "м2": 1, "малая секунда": 1,
        "б2": 2, "большая секунда": 2,
        "ув2": 3, "увеличенная секунда": 3,
        "м3": 3, "малая терция": 3,
        "б3": 4, "большая терция": 4,
        "ч4": 5, "чистая кварта": 5,
        "ув4": 6, "ум5": 6, "тритон": 6,
        "ч5": 7, "чистая квинта": 7,
        "м6": 8, "малая секста": 8,
        "б6": 9, "большая секста": 9,
        "м7": 10, "малая септима": 10,
        "б7": 11, "большая септима": 11,
        "ч8": 12, "октава": 12, "чистая октава": 12,
        "м9": 13, "малая нона": 13,
        "б9": 14, "большая нона": 14,
        "м10": 15, "малая децима": 15,
        "б10": 16, "большая децима": 16,
        "ч11": 17, "чистая ундецима": 17,
        "ув11": 18,
        "ч12": 19, "дуодецима": 19, "чистая дуодецима": 19,
        "ч15": 24, "двойная октава": 24,
    }

    def __post_init__(self) -> None:
        if not self.name:
            abs_st = abs(self.semitones)
            default_name = self.STANDARD_NAMES.get(abs_st, f"{abs_st}st")
            object.__setattr__(self, "name", default_name)

    @classmethod
    def from_semitones(cls, semitones: int, name: Optional[str] = None) -> Interval:
        """Create an Interval from integer semitone count and optional custom name."""
        return cls(semitones=semitones, name=name or "")

    @classmethod
    def from_name(cls, name: str) -> Interval:
        """Create an Interval from its standard Russian name (e.g. 'ч5', 'ув2', 'м7')."""
        cleaned = name.strip().lower()
        # Direct check
        for key, st in cls.NAME_TO_SEMITONES.items():
            if cleaned == key.lower():
                return cls(semitones=st, name=name.strip())
        raise ValueError(f"Unknown interval name: '{name}'.")

    @classmethod
    def from_pitches(cls, lower: Pitch, upper: Pitch) -> Interval:
        """Calculate interval directed from lower pitch to upper pitch."""
        diff = upper.midi_number - lower.midi_number
        return cls(semitones=diff)

    @property
    def abs_semitones(self) -> int:
        """Absolute semitone distance."""
        return abs(self.semitones)

    @property
    def simple_semitones(self) -> int:
        """Interval modulo 12 (within one octave)."""
        return self.abs_semitones % 12

    @property
    def octaves(self) -> int:
        """Number of full octaves spanned."""
        return self.abs_semitones // 12

    @property
    def is_unison(self) -> bool:
        """True if interval is a perfect unison (0 semitones)."""
        return self.abs_semitones == 0

    @property
    def is_step(self) -> bool:
        """True if interval is stepwise motion (minor or major second, 1 or 2 semitones)."""
        return self.abs_semitones in (1, 2)

    @property
    def is_leap(self) -> bool:
        """True if interval is a melodic leap (>= 3 semitones)."""
        return self.abs_semitones >= 3

    @property
    def is_tritone(self) -> bool:
        """True if interval is an augmented 4th / diminished 5th (6 semitones mod 12)."""
        return self.simple_semitones == 6

    @property
    def is_perfect_fifth(self) -> bool:
        """True if interval is a perfect fifth (7 semitones mod 12)."""
        return self.simple_semitones == 7

    @property
    def is_perfect_octave(self) -> bool:
        """True if interval is an exact multiple of an octave (> 0 semitones)."""
        return self.abs_semitones > 0 and self.abs_semitones % 12 == 0

    @property
    def is_augmented_second(self) -> bool:
        """True if marked explicitly as an augmented second (3 semitones)."""
        return self.abs_semitones == 3 and "ув2" in self.name.lower()

    @property
    def is_seventh(self) -> bool:
        """True if interval is a seventh (10 or 11 semitones mod 12)."""
        return self.simple_semitones in (10, 11)

    def __int__(self) -> int:
        return self.midi_number

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Interval(semitones={self.semitones}, name='{self.name}')"

    def __add__(self, other: Interval) -> Interval:
        if isinstance(other, Interval):
            return Interval(self.semitones + other.semitones)
        return NotImplemented

    def __sub__(self, other: Interval) -> Interval:
        if isinstance(other, Interval):
            return Interval(self.semitones - other.semitones)
        return NotImplemented

    def __neg__(self) -> Interval:
        return Interval(-self.semitones, name=self.name)

    def __lt__(self, other: Union[Interval, int]) -> bool:
        other_val = other.semitones if isinstance(other, Interval) else other
        return self.semitones < other_val

    def __le__(self, other: Union[Interval, int]) -> bool:
        other_val = other.semitones if isinstance(other, Interval) else other
        return self.semitones <= other_val

    def __gt__(self, other: Union[Interval, int]) -> bool:
        other_val = other.semitones if isinstance(other, Interval) else other
        return self.semitones > other_val

    def __ge__(self, other: Union[Interval, int]) -> bool:
        other_val = other.semitones if isinstance(other, Interval) else other
        return self.semitones >= other_val


@dataclass(frozen=True, slots=True)
class ScaleDegree:
    """
    Scale degree (ступень лада) I..VII with optional chromatic alterations.
    
    degree: 1 to 7 (corresponds to I, II, III, IV, V, VI, VII).
    alteration: -2 (bb), -1 (b), 0 (natural), +1 (#), +2 (##).
    """

    degree: int
    alteration: int = 0

    ROMAN_NUMERALS: ClassVar[tuple[str, ...]] = (
        "", "I", "II", "III", "IV", "V", "VI", "VII"
    )

    def __post_init__(self) -> None:
        if not (1 <= self.degree <= 7):
            raise ValueError(f"Scale degree must be in 1..7, got {self.degree}.")
        if not (-2 <= self.alteration <= 2):
            raise ValueError(f"Alteration must be in -2..+2, got {self.alteration}.")

    @classmethod
    def from_str(cls, s: str) -> ScaleDegree:
        """
        Parse scale degree from roman numeral string (e.g. 'I', 'IV', 'VII#', 'bII', '#VII').
        """
        raw = s.strip()
        if not raw:
            raise ValueError("Scale degree string cannot be empty.")

        roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}

        # Check prefix alteration (e.g. 'bII', '#VII', 'bbVI')
        prefix_match = re.match(r"^(bb|b|##|#)?(VII|VI|IV|V|III|II|I)(bb|b|##|#)?$", raw, re.IGNORECASE)
        if not prefix_match:
            # Try numeric degree like '1', '4', '7#'
            num_match = re.match(r"^(bb|b|##|#)?([1-7])(bb|b|##|#)?$", raw, re.IGNORECASE)
            if not num_match:
                raise ValueError(f"Invalid scale degree format: '{s}'.")
            pre, num_str, post = num_match.groups()
            deg_int = int(num_str)
        else:
            pre, rom_str, post = prefix_match.groups()
            deg_int = roman_map[rom_str.upper()]

        alt_str = (pre or "") + (post or "")
        alt_str = alt_str.lower().replace("♯", "#").replace("♭", "b")

        alt_val = 0
        if alt_str == "#":
            alt_val = 1
        elif alt_str == "##":
            alt_val = 2
        elif alt_str == "b":
            alt_val = -1
        elif alt_str == "bb":
            alt_val = -2
        elif alt_str:
            raise ValueError(f"Unrecognized alteration in '{s}': '{alt_str}'.")

        return cls(degree=deg_int, alteration=alt_val)

    @property
    def roman(self) -> str:
        """Roman numeral for the degree without alteration (e.g. 'VII')."""
        return self.ROMAN_NUMERALS[self.degree]

    @property
    def alteration_symbol(self) -> str:
        """String accidental symbol ('b', '#', or empty)."""
        if self.alteration == 1:
            return "#"
        if self.alteration == 2:
            return "##"
        if self.alteration == -1:
            return "b"
        if self.alteration == -2:
            return "bb"
        return ""

    @property
    def name(self) -> str:
        """Full name with alteration (e.g. 'VII#', 'bII', 'I')."""
        if self.alteration < 0:
            return f"{self.alteration_symbol}{self.roman}"
        return f"{self.roman}{self.alteration_symbol}"

    @property
    def index(self) -> int:
        """0-based scale degree index (0..6)."""
        return self.degree - 1

    @property
    def is_tonic(self) -> bool:
        """True if unaltered degree I."""
        return self.degree == 1 and self.alteration == 0

    @property
    def is_subdominant(self) -> bool:
        """True if unaltered degree IV."""
        return self.degree == 4 and self.alteration == 0

    @property
    def is_dominant(self) -> bool:
        """True if unaltered degree V."""
        return self.degree == 5 and self.alteration == 0

    @property
    def is_leading_tone(self) -> bool:
        """True if degree VII (leading tone)."""
        return self.degree == 7

    def __int__(self) -> int:
        return self.midi_number

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"ScaleDegree({self.degree}, alteration={self.alteration}, name='{self.name}')"


# Predefined scale degree constants
ScaleDegree.I = ScaleDegree(1, 0)       # type: ignore[attr-defined]
ScaleDegree.II = ScaleDegree(2, 0)      # type: ignore[attr-defined]
ScaleDegree.III = ScaleDegree(3, 0)     # type: ignore[attr-defined]
ScaleDegree.IV = ScaleDegree(4, 0)      # type: ignore[attr-defined]
ScaleDegree.V = ScaleDegree(5, 0)       # type: ignore[attr-defined]
ScaleDegree.VI = ScaleDegree(6, 0)      # type: ignore[attr-defined]
ScaleDegree.VII = ScaleDegree(7, 0)     # type: ignore[attr-defined]
ScaleDegree.VII_SHARP = ScaleDegree(7, 1)  # type: ignore[attr-defined]
ScaleDegree.FLAT_II = ScaleDegree(2, -1)   # type: ignore[attr-defined]
ScaleDegree.FLAT_VI = ScaleDegree(6, -1)   # type: ignore[attr-defined]


@dataclass(frozen=True, slots=True)
class Pitch:
    """
    Absolute musical pitch represented as a standard MIDI note number (0..127).
    
    Middle C (C4) is MIDI 60.
    Provides octave calculation, pitch class projection, and arithmetic.
    """

    midi_number: int

    def __post_init__(self) -> None:
        if not (0 <= self.midi_number <= 127):
            raise ValueError(f"MIDI note number must be in range 0..127, got {self.midi_number}.")

    @classmethod
    def from_midi(cls, midi: int) -> Pitch:
        """Create Pitch from raw MIDI integer."""
        return cls(midi_number=midi)

    @classmethod
    def from_name(cls, name: str) -> Pitch:
        """
        Parse pitch from scientific pitch notation (e.g. 'C4', 'G#3', 'Bb2', 'C-1').
        """
        cleaned = name.strip()
        match = re.match(r"^([A-Ga-gHh][#♯b♭]?)(-?\d+)$", cleaned)
        if not match:
            raise ValueError(f"Invalid pitch name format: '{name}'. Expected format like 'C4', 'G#3'.")
        note_part, oct_part = match.groups()
        pc = PitchClass.from_name(note_part)
        octave = int(oct_part)
        midi = (octave + 1) * 12 + pc.value
        return cls(midi_number=midi)

    @property
    def octave(self) -> int:
        """Scientific octave number (e.g. 4 for C4 = 60)."""
        return (self.midi_number // 12) - 1

    @property
    def pitch_class(self) -> PitchClass:
        """PitchClass in Z_12 (midi_number % 12)."""
        return PitchClass(self.midi_number % 12)

    @property
    def note_name(self) -> str:
        """Standard scientific note name with sharp preference (e.g. 'C4', 'F#3')."""
        return f"{self.pitch_class.sharp_name}{self.octave}"

    def get_note_name(self, prefer_flat: bool = False) -> str:
        """Get note name with preferred accidental representation."""
        pc_name = self.pitch_class.flat_name if prefer_flat else self.pitch_class.sharp_name
        return f"{pc_name}{self.octave}"

    def transpose(self, semitones: int) -> Pitch:
        """Return a new Pitch shifted by the given semitone delta."""
        return Pitch(self.midi_number + semitones)

    def __int__(self) -> int:
        return self.midi_number

    def __str__(self) -> str:
        return self.note_name

    def __repr__(self) -> str:
        return f"Pitch(midi={self.midi_number}, name='{self.note_name}')"

    def __lt__(self, other: Union[Pitch, int]) -> bool:
        other_val = other.midi_number if isinstance(other, Pitch) else other
        return self.midi_number < other_val

    def __le__(self, other: Union[Pitch, int]) -> bool:
        other_val = other.midi_number if isinstance(other, Pitch) else other
        return self.midi_number <= other_val

    def __gt__(self, other: Union[Pitch, int]) -> bool:
        other_val = other.midi_number if isinstance(other, Pitch) else other
        return self.midi_number > other_val

    def __ge__(self, other: Union[Pitch, int]) -> bool:
        other_val = other.midi_number if isinstance(other, Pitch) else other
        return self.midi_number >= other_val

    def __add__(self, other: Union[int, Interval]) -> Pitch:
        if isinstance(other, int):
            return Pitch(self.midi_number + other)
        if isinstance(other, Interval):
            return Pitch(self.midi_number + other.semitones)
        return NotImplemented

    def __sub__(self, other: Union[int, Interval, Pitch]) -> Union[Pitch, Interval]:
        if isinstance(other, int):
            return Pitch(self.midi_number - other)
        if isinstance(other, Interval):
            return Pitch(self.midi_number - other.semitones)
        if isinstance(other, Pitch):
            return Interval(self.midi_number - other.midi_number)
        return NotImplemented
