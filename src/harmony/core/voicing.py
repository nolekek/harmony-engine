"""
Core domain model: Voicing, Spacing, and Voice ranges.

Implements the 4-part SATB vertical slice (Soprano, Alto, Tenor, Bass),
voice-ordering invariants (no voice crossing), acoustic spacing rules,
voice range limits, and spacing classification (Close / Wide / Mixed)
per the Brigada harmony textbook (docs/BRIGADE_RULES.md, docs/MATH_MODEL.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Iterator, Optional, Sequence, Union

from .chord import ChordDefinition
from .pitch import Interval, Pitch, PitchClass


class Voice(str, Enum):
    """The four classical SATB choir voices."""

    SOPRANO = "Soprano"
    ALTO = "Alto"
    TENOR = "Tenor"
    BASS = "Bass"


class Spacing(str, Enum):
    """
    Chord spacing (расположение аккорда):
    - CLOSE (Тесное): S-A and A-T without skipped chord tones (intervals <= 4 semitones / 3rd, 4th).
    - WIDE (Широкое / Open): S-A and A-T have exactly one chord tone skipped (intervals 5-12 / 5th, 6th, 8ve).
    - MIXED (Смешанное): mixed spacing, leaps, or irregular seventh chord arrangements.
    """

    CLOSE = "Close"
    WIDE = "Wide"
    MIXED = "Mixed"

    # Alias for wide
    OPEN = "Wide"


@dataclass(frozen=True, slots=True)
class Voicing:
    """
    A 4-part SATB chord voicing vertical slice: (Soprano, Alto, Tenor, Bass).
    
    Immutable, hashable, and equipped with verification methods for:
    - Voice ordering (S >= A >= T >= B, no voice crossing)
    - Acoustic spacing limits (S-A <= 12, A-T <= 12, T-B <= 24)
    - Standard voice range constraints
    - Spacing classification (Close / Wide / Mixed)
    """

    soprano: Pitch
    alto: Pitch
    tenor: Pitch
    bass: Pitch

    # Standard vocal ranges from Brigada textbook (docs/BRIGADE_RULES.md)
    # Soprano: C4 - A5 (60 - 81)
    # Alto:    G3 - D5 (55 - 74)
    # Tenor:   C3 - G4 (48 - 67)
    # Bass:    E2 - C4 (40 - 60)
    RANGES: ClassVar[dict[Voice, tuple[int, int]]] = {
        Voice.SOPRANO: (60, 81),
        Voice.ALTO: (55, 74),
        Voice.TENOR: (48, 67),
        Voice.BASS: (40, 60),
    }

    # Short aliases
    @property
    def S(self) -> Pitch:
        """Soprano pitch."""
        return self.soprano

    @property
    def A(self) -> Pitch:
        """Alto pitch."""
        return self.alto

    @property
    def T(self) -> Pitch:
        """Tenor pitch."""
        return self.tenor

    @property
    def B(self) -> Pitch:
        """Bass pitch."""
        return self.bass

    # -------------------------------------------------------------------------
    # Constructors
    # -------------------------------------------------------------------------

    @classmethod
    def from_midi(cls, s: int, a: int, t: int, b: int) -> Voicing:
        """Create Voicing from 4 integer MIDI numbers (S, A, T, B)."""
        return cls(
            soprano=Pitch.from_midi(s),
            alto=Pitch.from_midi(a),
            tenor=Pitch.from_midi(t),
            bass=Pitch.from_midi(b),
        )

    @classmethod
    def from_tuple(cls, satb: tuple[int, int, int, int]) -> Voicing:
        """Create Voicing from a 4-tuple of MIDI numbers (S, A, T, B)."""
        return cls.from_midi(satb[0], satb[1], satb[2], satb[3])

    @classmethod
    def from_pitches(cls, s: Pitch, a: Pitch, t: Pitch, b: Pitch) -> Voicing:
        """Create Voicing from 4 Pitch instances."""
        return cls(soprano=s, alto=a, tenor=t, bass=b)

    @classmethod
    def from_names(cls, s: str, a: str, t: str, b: str) -> Voicing:
        """Create Voicing from 4 note names (e.g. 'C5', 'G4', 'E4', 'C3')."""
        return cls(
            soprano=Pitch.from_name(s),
            alto=Pitch.from_name(a),
            tenor=Pitch.from_name(t),
            bass=Pitch.from_name(b),
        )

    # -------------------------------------------------------------------------
    # Invariant & Ordering Checks
    # -------------------------------------------------------------------------

    @property
    def is_ordered(self) -> bool:
        """
        True if voices are strictly non-crossing: S >= A >= T >= B.
        """
        return (
            self.soprano.midi_number >= self.alto.midi_number >=
            self.tenor.midi_number >= self.bass.midi_number
        )

    @property
    def has_voice_crossing(self) -> bool:
        """True if any voice cross is present (S < A, A < T, or T < B)."""
        return not self.is_ordered

    # -------------------------------------------------------------------------
    # Voice Intervals
    # -------------------------------------------------------------------------

    @property
    def interval_sa(self) -> Interval:
        """Interval from Alto up to Soprano (S - A)."""
        diff = self.soprano.midi_number - self.alto.midi_number
        return Interval(diff)

    @property
    def interval_at(self) -> Interval:
        """Interval from Tenor up to Alto (A - T)."""
        diff = self.alto.midi_number - self.tenor.midi_number
        return Interval(diff)

    @property
    def interval_tb(self) -> Interval:
        """Interval from Bass up to Tenor (T - B)."""
        diff = self.tenor.midi_number - self.bass.midi_number
        return Interval(diff)

    @property
    def interval_st(self) -> Interval:
        """Interval from Tenor up to Soprano (S - T)."""
        diff = self.soprano.midi_number - self.tenor.midi_number
        return Interval(diff)

    @property
    def interval_sb(self) -> Interval:
        """Interval from Bass up to Soprano (S - B)."""
        diff = self.soprano.midi_number - self.bass.midi_number
        return Interval(diff)

    @property
    def interval_ab(self) -> Interval:
        """Interval from Bass up to Alto (A - B)."""
        diff = self.alto.midi_number - self.bass.midi_number
        return Interval(diff)

    # -------------------------------------------------------------------------
    # Range and Spacing Constraint Checks
    # -------------------------------------------------------------------------

    def in_ranges(self) -> bool:
        """
        Check if all 4 voices reside within standard Brigada vocal limits:
        S: 60..81, A: 55..74, T: 48..67, B: 40..60.
        """
        s_min, s_max = self.RANGES[Voice.SOPRANO]
        a_min, a_max = self.RANGES[Voice.ALTO]
        t_min, t_max = self.RANGES[Voice.TENOR]
        b_min, b_max = self.RANGES[Voice.BASS]

        return (
            s_min <= self.soprano.midi_number <= s_max
            and a_min <= self.alto.midi_number <= a_max
            and t_min <= self.tenor.midi_number <= t_max
            and b_min <= self.bass.midi_number <= b_max
        )

    def range_violations(self) -> list[str]:
        """Return human-readable list of range violations, empty if valid."""
        violations = []
        voices = [
            (Voice.SOPRANO, self.soprano),
            (Voice.ALTO, self.alto),
            (Voice.TENOR, self.tenor),
            (Voice.BASS, self.bass),
        ]
        for v_name, pitch in voices:
            v_min, v_max = self.RANGES[v_name]
            if not (v_min <= pitch.midi_number <= v_max):
                violations.append(
                    f"{v_name.value} {pitch.note_name} (MIDI {pitch.midi_number}) "
                    f"outside [{v_min}, {v_max}]."
                )
        return violations

    def is_spacing_valid(self) -> bool:
        """
        Check if acoustic spacing bounds are satisfied:
        - S - A <= 12 (no upper voice gap > 1 octave)
        - A - T <= 12 (no upper voice gap > 1 octave)
        - T - B <= 24 (bass-tenor gap <= 2 octaves)
        - No voice crossing (is_ordered)
        """
        if not self.is_ordered:
            return False
        return (
            self.interval_sa.semitones <= 12
            and self.interval_at.semitones <= 12
            and self.interval_tb.semitones <= 24
        )

    def spacing_violations(self) -> list[str]:
        """Return list of spacing rule violations."""
        violations = []
        if not self.is_ordered:
            violations.append(
                f"Voice crossing: S={self.soprano.midi_number}, A={self.alto.midi_number}, "
                f"T={self.tenor.midi_number}, B={self.bass.midi_number}"
            )
        if self.interval_sa.semitones > 12:
            violations.append(f"S-A distance exceeds octave ({self.interval_sa.semitones} st > 12).")
        if self.interval_at.semitones > 12:
            violations.append(f"A-T distance exceeds octave ({self.interval_at.semitones} st > 12).")
        if self.interval_tb.semitones > 24:
            violations.append(f"T-B distance exceeds two octaves ({self.interval_tb.semitones} st > 24).")
        return violations

    def is_statically_valid(self) -> bool:
        """Complete static validity per MATH_MODEL.md section 2.2."""
        return self.is_ordered and self.in_ranges() and self.is_spacing_valid()

    # -------------------------------------------------------------------------
    # Spacing Classification (Close / Wide / Mixed)
    # -------------------------------------------------------------------------

    def determine_spacing(self, chord_def: Optional[ChordDefinition] = None) -> Spacing:
        """
        Determine spacing (Close, Wide, or Mixed).
        
        If chord_def is provided, spacing is evaluated by counting skipped chord tones:
        - Close: 0 chord tones skipped between S-A and 0 between A-T.
        - Wide: 1 chord tone skipped between S-A and 1 between A-T.
        - Mixed: any other distribution.
        
        If chord_def is not provided, interval thresholds are used:
        - Close: S-A <= 4 and A-T <= 4.
        - Wide: 5 <= S-A <= 12 and 5 <= A-T <= 12.
        - Mixed: otherwise.
        """
        if chord_def is not None:
            # Count intermediate chord tones strictly between S and A
            sa_chord_tones = sum(
                1 for m in range(self.alto.midi_number + 1, self.soprano.midi_number)
                if PitchClass.from_midi(m) in chord_def.pitch_classes
            )
            # Count intermediate chord tones strictly between A and T
            at_chord_tones = sum(
                1 for m in range(self.tenor.midi_number + 1, self.alto.midi_number)
                if PitchClass.from_midi(m) in chord_def.pitch_classes
            )

            if sa_chord_tones == 0 and at_chord_tones == 0:
                return Spacing.CLOSE
            if sa_chord_tones == 1 and at_chord_tones == 1:
                return Spacing.WIDE
            return Spacing.MIXED

        # Heuristic interval-based spacing
        sa = self.interval_sa.semitones
        at = self.interval_at.semitones

        if sa <= 4 and at <= 4:
            return Spacing.CLOSE
        if 5 <= sa <= 12 and 5 <= at <= 12:
            return Spacing.WIDE
        return Spacing.MIXED

    # -------------------------------------------------------------------------
    # Conversions and Sequence Interface
    # -------------------------------------------------------------------------

    def to_midi_tuple(self) -> tuple[int, int, int, int]:
        """Return 4-tuple of MIDI numbers (S, A, T, B)."""
        return (
            self.soprano.midi_number,
            self.alto.midi_number,
            self.tenor.midi_number,
            self.bass.midi_number,
        )

    def to_pitches(self) -> tuple[Pitch, Pitch, Pitch, Pitch]:
        """Return 4-tuple of Pitch objects (S, A, T, B)."""
        return (self.soprano, self.alto, self.tenor, self.bass)

    def to_pitch_classes(self) -> tuple[PitchClass, PitchClass, PitchClass, PitchClass]:
        """Return 4-tuple of PitchClasses (S, A, T, B)."""
        return (
            self.soprano.pitch_class,
            self.alto.pitch_class,
            self.tenor.pitch_class,
            self.bass.pitch_class,
        )

    def __iter__(self) -> Iterator[Pitch]:
        """Iterate over voices in order: Soprano, Alto, Tenor, Bass."""
        yield self.soprano
        yield self.alto
        yield self.tenor
        yield self.bass

    def __len__(self) -> int:
        return 4

    def __getitem__(self, idx: Union[int, Voice]) -> Pitch:
        if isinstance(idx, Voice):
            if idx == Voice.SOPRANO:
                return self.soprano
            if idx == Voice.ALTO:
                return self.alto
            if idx == Voice.TENOR:
                return self.tenor
            if idx == Voice.BASS:
                return self.bass
        if isinstance(idx, int):
            if idx == 0:
                return self.soprano
            if idx == 1:
                return self.alto
            if idx == 2:
                return self.tenor
            if idx == 3:
                return self.bass
            raise IndexError(f"Voicing index out of range (0..3), got {idx}.")
        raise TypeError(f"Invalid index type: {type(idx)}.")

    def __str__(self) -> str:
        return f"({self.soprano.note_name}, {self.alto.note_name}, {self.tenor.note_name}, {self.bass.note_name})"

    def __repr__(self) -> str:
        return (
            f"Voicing(S={self.soprano.note_name}({self.soprano.midi_number}), "
            f"A={self.alto.note_name}({self.alto.midi_number}), "
            f"T={self.tenor.note_name}({self.tenor.midi_number}), "
            f"B={self.bass.note_name}({self.bass.midi_number}))"
        )
