"""
Core domain model: ChordFunction, Inversion, and ChordDefinition.

Implements harmonic functions, inversions, chord tone factor composition,
and voice doubling constraints according to the Brigada harmony textbook
(Дубовский, Евсеев, Способин, Соколов — «Учебник гармонии»).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Optional, Sequence, Union

from .key import Key, Mode
from .pitch import Pitch, PitchClass, ScaleDegree


class ChordFunction(str, Enum):
    """
    Classical harmonic functions:
    - T: Tonic (I degree)
    - S: Subdominant (IV degree)
    - D: Dominant (V degree)
    - II: Supertonic (II degree)
    - VI: Submediant (VI degree)
    - VII: Leading-tone triad / chord (VII degree)
    - K64: Cadential Six-Four chord (каденционный квартсекстаккорд)
    """

    T = "T"
    S = "S"
    D = "D"
    II = "II"
    VI = "VI"
    VII = "VII"
    K64 = "K64"

    @classmethod
    def from_str(cls, s: str) -> ChordFunction:
        """Parse ChordFunction case-insensitively, supporting 't', 's', 'd', 'k64', etc."""
        cleaned = s.strip().upper()
        if cleaned in ("T", "TONIC"):
            return cls.T
        if cleaned in ("S", "SUBDOMINANT"):
            return cls.S
        if cleaned in ("D", "DOMINANT"):
            return cls.D
        if cleaned in ("II", "2"):
            return cls.II
        if cleaned in ("VI", "6"):
            return cls.VI
        if cleaned in ("VII", "7"):
            return cls.VII
        if cleaned in ("K64", "K6/4", "CADENTIAL64", "CAD64"):
            return cls.K64
        raise ValueError(f"Unknown chord function: '{s}'.")

    @property
    def root_scale_degree(self) -> ScaleDegree:
        """The fundamental scale degree associated with this function."""
        if self in (ChordFunction.T, ChordFunction.K64):
            return ScaleDegree(1, 0)
        if self == ChordFunction.S:
            return ScaleDegree(4, 0)
        if self == ChordFunction.D:
            return ScaleDegree(5, 0)
        if self == ChordFunction.II:
            return ScaleDegree(2, 0)
        if self == ChordFunction.VI:
            return ScaleDegree(6, 0)
        if self == ChordFunction.VII:
            return ScaleDegree(7, 0)
        raise ValueError(f"Unknown root degree for {self}")

    @property
    def is_tonic_group(self) -> bool:
        """True if belonging to the tonic harmonic group (T, VI)."""
        return self in (ChordFunction.T, ChordFunction.VI)

    @property
    def is_subdominant_group(self) -> bool:
        """True if belonging to the subdominant harmonic group (S, II)."""
        return self in (ChordFunction.S, ChordFunction.II)

    @property
    def is_dominant_group(self) -> bool:
        """True if belonging to the dominant harmonic group (D, VII, K64)."""
        return self in (ChordFunction.D, ChordFunction.VII, ChordFunction.K64)


class Inversion(str, Enum):
    """
    Chord inversions in classical figured bass:
    - ROOT / 53: Трезвучие в основном виде (5/3)
    - SEXTA / 6: Секстаккорд (6)
    - QUARTSEXTA / 64: Квартсекстаккорд (6/4)
    - SEPTIMA / 7: Септаккорд в основном виде (7)
    - QUINTSEXTA / 65: Квинтсекстаккорд (6/5, 1-е обращение септаккорда)
    - TERZQUART / 43: Терцквартаккорд (4/3, 2-е обращение септаккорда)
    - SECUNDA / 2: Секундаккорд (2, 3-е обращение септаккорда)
    """

    ROOT = "53"
    SEXTA = "6"
    QUARTSEXTA = "64"
    SEPTIMA = "7"
    QUINTSEXTA = "65"
    TERZQUART = "43"
    SECUNDA = "2"

    @classmethod
    def from_str(cls, s: str) -> Inversion:
        """
        Parse Inversion from various notation strings:
        '53', '5/3', 'root', '6', '64', '6/4', '7', '65', '6/5', '43', '4/3', '2'.
        """
        cleaned = s.strip().lower().replace("/", "")
        mapping = {
            "53": cls.ROOT,
            "root": cls.ROOT,
            "triad": cls.ROOT,
            "6": cls.SEXTA,
            "sexta": cls.SEXTA,
            "64": cls.QUARTSEXTA,
            "quartsexta": cls.QUARTSEXTA,
            "7": cls.SEPTIMA,
            "septima": cls.SEPTIMA,
            "seventh": cls.SEPTIMA,
            "65": cls.QUINTSEXTA,
            "quintsexta": cls.QUINTSEXTA,
            "43": cls.TERZQUART,
            "terzquart": cls.TERZQUART,
            "2": cls.SECUNDA,
            "secunda": cls.SECUNDA,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown inversion string: '{s}'.")

    @property
    def is_seventh(self) -> bool:
        """True if the inversion represents a 4-note seventh chord."""
        return self in (
            Inversion.SEPTIMA,
            Inversion.QUINTSEXTA,
            Inversion.TERZQUART,
            Inversion.SECUNDA,
        )

    @property
    def is_triad(self) -> bool:
        """True if the inversion represents a 3-note triad."""
        return not self.is_seventh

    @property
    def bass_factor(self) -> str:
        """The default chord factor positioned in the bass."""
        if self in (Inversion.ROOT, Inversion.SEPTIMA):
            return "root"
        if self in (Inversion.SEXTA, Inversion.QUINTSEXTA):
            return "third"
        if self in (Inversion.QUARTSEXTA, Inversion.TERZQUART):
            return "fifth"
        if self == Inversion.SECUNDA:
            return "seventh"
        raise ValueError(f"Unknown bass factor for {self}")

    @property
    def symbol(self) -> str:
        """Standard figured bass symbol."""
        if self == Inversion.ROOT:
            return "5/3"
        if self == Inversion.SEXTA:
            return "6"
        if self == Inversion.QUARTSEXTA:
            return "6/4"
        if self == Inversion.SEPTIMA:
            return "7"
        if self == Inversion.QUINTSEXTA:
            return "6/5"
        if self == Inversion.TERZQUART:
            return "4/3"
        if self == Inversion.SECUNDA:
            return "2"
        return self.value


@dataclass(frozen=True, slots=True)
class ChordDefinition:
    """
    Concrete chord definition in a specific key.
    
    Contains:
    - function: harmonic function (T, S, D, II, VI, VII, K64)
    - inversion: inversion (53, 6, 64, 7, 65, 43, 2)
    - key: tonality
    - is_seventh: whether chord is a 7th chord
    - bass_factor: chord factor present in the bass ('root', 'third', 'fifth', 'seventh')
    
    Provides factor pitch classes, bass pitch class, allowed doublings, and
    validation against Brigada textbook rules (docs/BRIGADE_RULES.md).
    """

    function: ChordFunction
    inversion: Inversion
    key: Key
    is_seventh: bool = False
    bass_factor: Optional[str] = None

    def __post_init__(self) -> None:
        # Determine is_seventh if inversion implies it
        if self.inversion.is_seventh:
            object.__setattr__(self, "is_seventh", True)

        # Set default bass factor if not explicitly given
        if self.bass_factor is None:
            if self.function == ChordFunction.K64:
                # K64 always has scale degree V (the fifth of tonic) in bass
                object.__setattr__(self, "bass_factor", "fifth")
            else:
                object.__setattr__(self, "bass_factor", self.inversion.bass_factor)

    @classmethod
    def from_string(cls, name: str, key: Key) -> ChordDefinition:
        """
        Parse ChordDefinition from notation like 'T', 'T6', 'K64', 'D7', 'D43', 's6', 'VI'.
        """
        raw = name.strip()
        if not raw:
            raise ValueError("Chord definition string cannot be empty.")

        # K64 special case
        if raw.upper().startswith("K"):
            return cls(function=ChordFunction.K64, inversion=Inversion.QUARTSEXTA, key=key)

        # Patterns like:
        # T, T6, T64, T53
        # S, S6, S64, s, s6
        # D, D6, D7, D65, D43, D2
        # VI, VI6
        # II, II6, II7, II65
        # VII, VII7
        pattern = r"^(T|S|D|II|VI|VII|t|s|d)(53|64|65|43|6|7|2)?$"
        match = re.match(pattern, raw)
        if not match:
            raise ValueError(f"Unrecognized chord notation: '{name}'.")

        fn_str, inv_str = match.groups()
        fn = ChordFunction.from_str(fn_str)
        if inv_str:
            inv = Inversion.from_str(inv_str)
        else:
            inv = Inversion.ROOT

        is_seventh = inv.is_seventh or (inv_str == "7")
        return cls(function=fn, inversion=inv, key=key, is_seventh=is_seventh)

    @property
    def root(self) -> PitchClass:
        """Root pitch class of the chord."""
        return self.key.pitch_class_for_degree(self.function.root_scale_degree)

    @property
    def third(self) -> PitchClass:
        """
        Third pitch class of the chord.
        
        In D (Dominant) in minor keys, the third is always raised to the leading tone
        (гармонический вид — мажорная доминанта!).
        """
        if self.function == ChordFunction.D:
            return self.key.leading_tone

        if self.function in (ChordFunction.T, ChordFunction.K64):
            return self.key.pitch_class_for_degree(ScaleDegree(3, 0))
        if self.function == ChordFunction.S:
            return self.key.pitch_class_for_degree(ScaleDegree(6, 0))
        if self.function == ChordFunction.II:
            return self.key.pitch_class_for_degree(ScaleDegree(4, 0))
        if self.function == ChordFunction.VI:
            return self.key.pitch_class_for_degree(ScaleDegree(1, 0))
        if self.function == ChordFunction.VII:
            return self.key.pitch_class_for_degree(ScaleDegree(2, 0))
        raise ValueError(f"Unknown third for {self.function}")

    @property
    def fifth(self) -> PitchClass:
        """Fifth pitch class of the chord."""
        if self.function in (ChordFunction.T, ChordFunction.K64):
            return self.key.pitch_class_for_degree(ScaleDegree(5, 0))
        if self.function == ChordFunction.S:
            return self.key.pitch_class_for_degree(ScaleDegree(1, 0))
        if self.function == ChordFunction.D:
            return self.key.pitch_class_for_degree(ScaleDegree(2, 0))
        if self.function == ChordFunction.II:
            return self.key.pitch_class_for_degree(ScaleDegree(6, 0))
        if self.function == ChordFunction.VI:
            return self.key.pitch_class_for_degree(ScaleDegree(3, 0))
        if self.function == ChordFunction.VII:
            return self.key.pitch_class_for_degree(ScaleDegree(4, 0))
        raise ValueError(f"Unknown fifth for {self.function}")

    @property
    def seventh(self) -> Optional[PitchClass]:
        """Seventh pitch class of the chord, if a seventh chord."""
        if not self.is_seventh:
            return None
        if self.function == ChordFunction.D:
            return self.key.pitch_class_for_degree(ScaleDegree(4, 0))
        if self.function == ChordFunction.II:
            return self.key.pitch_class_for_degree(ScaleDegree(1, 0))
        if self.function == ChordFunction.VII:
            return self.key.pitch_class_for_degree(ScaleDegree(6, 0))
        if self.function == ChordFunction.T:
            return self.key.pitch_class_for_degree(ScaleDegree(7, 0))
        if self.function == ChordFunction.S:
            return self.key.pitch_class_for_degree(ScaleDegree(3, 0))
        return None

    @property
    def factors(self) -> dict[str, PitchClass]:
        """Mapping from factor name ('root', 'third', 'fifth', 'seventh') to PitchClass."""
        result = {
            "root": self.root,
            "third": self.third,
            "fifth": self.fifth,
        }
        if self.is_seventh and self.seventh is not None:
            result["seventh"] = self.seventh
        return result

    @property
    def pitch_classes(self) -> frozenset[PitchClass]:
        """Frozenset of all pitch classes comprising this chord."""
        return frozenset(self.factors.values())

    @property
    def bass_pitch_class(self) -> PitchClass:
        """The exact PitchClass required in the bass voice."""
        assert self.bass_factor is not None
        return self.factors[self.bass_factor]

    @property
    def allowed_doublings(self) -> tuple[str, ...]:
        """
        Allowed voice doubling factors according to Brigada rules:
        - Main triads (T, S, D) in 5/3: double ROOT ('root', rarely 'fifth'). Third STRICTLY forbidden.
        - Sextachords (T6, S6, D6): double ROOT or FIFTH ('root', 'fifth').
        - K64: STRICTLY double BASS (fifth of triad: 'fifth').
        - D7 root position: full (no doubling) or incomplete (double root: 'root').
        - D7 inversions (65, 43, 2): ALWAYS complete, no doublings allowed ('none').
        - VI triad: double THIRD ('third') in deceptive cadence (D -> VI), or ROOT ('root').
        - II6: double THIRD ('third' - IV scale degree) or ROOT ('root').
        """
        # K64
        if self.function == ChordFunction.K64:
            return ("fifth",)

        # Seventh chords
        if self.is_seventh:
            if self.inversion == Inversion.ROOT:
                # Full D7 (no doubling) or incomplete D7 (doubled root, fifth omitted)
                return ("none", "root")
            # Inversions of 7th chords must be complete in Brigada style
            return ("none",)

        # Deceptive cadence VI
        if self.function == ChordFunction.VI:
            return ("third", "root")

        # II6
        if self.function == ChordFunction.II and self.inversion == Inversion.SEXTA:
            return ("third", "root")

        # Main triads in root position (T, S, D)
        if self.inversion == Inversion.ROOT:
            return ("root", "fifth")

        # Sextachords (T6, S6, D6)
        if self.inversion == Inversion.SEXTA:
            return ("root", "fifth")

        # Quartsextachords (passing / auxiliary)
        if self.inversion == Inversion.QUARTSEXTA:
            return ("fifth",)

        return ("root", "fifth")

    def factor_of(self, pc: Union[Pitch, PitchClass, int]) -> Optional[str]:
        """Identify which chord factor ('root', 'third', 'fifth', 'seventh') corresponds to pc."""
        target_pc = pc.pitch_class if isinstance(pc, Pitch) else (
            pc if isinstance(pc, PitchClass) else PitchClass(pc % 12)
        )
        for factor_name, factor_pc in self.factors.items():
            if factor_pc == target_pc:
                return factor_name
        return None

    def validate_voicing(
        self,
        pitches: Sequence[Union[Pitch, PitchClass, int]],
        is_deceptive_cadence: bool = False,
    ) -> tuple[bool, str]:
        """
        Validate whether the 4 voices in pitches (S, A, T, B) satisfy chord tones,
        bass requirement, and Brigada doubling rules.
        
        Returns (is_valid: bool, reason: str).
        """
        if len(pitches) != 4:
            return False, f"Expected 4 voices, got {len(pitches)}."

        pcs = [
            p.pitch_class if isinstance(p, Pitch) else (
                p if isinstance(p, PitchClass) else PitchClass(p % 12)
            )
            for p in pitches
        ]
        s_pc, a_pc, t_pc, b_pc = pcs

        # 1. Check all pitch classes belong to the chord
        for idx, pc in enumerate(pcs):
            if pc not in self.pitch_classes:
                return False, f"Voice {idx} ({pc}) is not a chord tone of {self}."

        # 2. Check bass note matches required bass factor
        if b_pc != self.bass_pitch_class:
            return (
                False,
                f"Bass pitch class {b_pc} does not match required inversion bass {self.bass_pitch_class} ({self.bass_factor})."
            )

        # 3. Factor distribution
        factor_counts: Counter[str] = Counter()
        for pc in pcs:
            factor = self.factor_of(pc)
            assert factor is not None
            factor_counts[factor] += 1

        # Check special doubling rules
        # 3.1. K64 strictly doubles fifth (the bass)
        if self.function == ChordFunction.K64:
            if factor_counts["fifth"] != 2:
                return (
                    False,
                    f"K64 must strictly double the bass (fifth). Got fifth count = {factor_counts['fifth']}."
                )
            if factor_counts["root"] != 1 or factor_counts["third"] != 1:
                return False, "K64 must contain root, third, and doubled fifth."
            return True, "Valid K64 doubling (doubled fifth)."

        # 3.2. Deceptive VI triad
        if self.function == ChordFunction.VI and is_deceptive_cadence:
            if factor_counts["third"] != 2:
                return (
                    False,
                    f"Deceptive VI resolution (D -> VI) strictly requires doubling the third (tonic scale degree). Got third count = {factor_counts['third']}."
                )
            return True, "Valid deceptive VI doubling (doubled third)."

        # 3.3. Main triads in root position (T, S, D in 5/3): doubling third is forbidden!
        if self.function in (ChordFunction.T, ChordFunction.S, ChordFunction.D) and self.inversion == Inversion.ROOT:
            if factor_counts["third"] > 1:
                return False, f"Doubling the third in main triad {self.function} 5/3 is strictly forbidden by Brigada rules."

        # 3.4. Dominant seventh inversions (65, 43, 2): must be complete (all 4 factors once)
        if self.is_seventh and self.inversion != Inversion.ROOT:
            for req in ("root", "third", "fifth", "seventh"):
                if factor_counts[req] != 1:
                    return (
                        False,
                        f"Seventh chord inversion {self.inversion.symbol} must be complete. Factor '{req}' count = {factor_counts[req]}."
                    )
            return True, "Valid complete 7th chord inversion."

        # 3.5. Dominant seventh root position (D7): complete or incomplete (doubled root, no fifth)
        if self.is_seventh and self.inversion == Inversion.ROOT:
            is_complete = all(factor_counts[f] == 1 for f in ("root", "third", "fifth", "seventh"))
            is_incomplete = (
                factor_counts["root"] == 2
                and factor_counts["third"] == 1
                and factor_counts["seventh"] == 1
                and factor_counts["fifth"] == 0
            )
            if not (is_complete or is_incomplete):
                return (
                    False,
                    f"D7 must be complete (1,1,1,1) or incomplete with doubled root (root:2, 3rd:1, 7th:1, 5th:0). Got {dict(factor_counts)}."
                )
            return True, "Valid D7 distribution."

        # 3.6. General triad doubling check
        doubled_factors = [f for f, count in factor_counts.items() if count >= 2]
        if not doubled_factors:
            return False, "Triad in 4 voices must double one chord tone."

        primary_doubled = doubled_factors[0]
        if primary_doubled not in self.allowed_doublings:
            return (
                False,
                f"Doubling factor '{primary_doubled}' is not permitted for {self}. Allowed: {self.allowed_doublings}."
            )

        return True, f"Valid voicing (doubled {primary_doubled})."

    def __str__(self) -> str:
        fn_str = self.function.value
        inv_str = "" if self.inversion == Inversion.ROOT else self.inversion.symbol
        return f"{fn_str}{inv_str} ({self.key.name})"

    def __repr__(self) -> str:
        return (
            f"ChordDefinition(function={self.function.value}, inversion={self.inversion.name}, "
            f"key='{self.key.name}', is_seventh={self.is_seventh}, bass_factor='{self.bass_factor}')"
        )
