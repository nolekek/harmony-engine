"""
Core domain types for Brigade Harmony Engine.
"""

from typing import NamedTuple, Any, Sequence, Mapping
from dataclasses import dataclass, field


class Voicing(NamedTuple):
    """
    Four-part vocal vertical slice (SATB).
    Immutable and hashable for DP state space.
    """
    soprano: int
    alto: int
    tenor: int
    bass: int

    @property
    def s(self) -> int:
        return self.soprano

    @property
    def a(self) -> int:
        return self.alto

    @property
    def t(self) -> int:
        return self.tenor

    @property
    def b(self) -> int:
        return self.bass

    def pitch_classes(self) -> tuple[int, int, int, int]:
        return (
            self.soprano % 12,
            self.alto % 12,
            self.tenor % 12,
            self.bass % 12,
        )


PITCH_CLASS_NAMES: dict[str, int] = {
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
    "B": 11, "H": 11, "CB": 11,
}

SCALE_INTERVALS: dict[str, tuple[int, ...]] = {
    "MAJOR": (0, 2, 4, 5, 7, 9, 11),
    "MINOR": (0, 2, 3, 5, 7, 8, 11),           # default harmonic minor in Brigade
    "MINORHARMONIC": (0, 2, 3, 5, 7, 8, 11),
    "MINORNATURAL": (0, 2, 3, 5, 7, 8, 10),
    "MINORMELODIC": (0, 2, 3, 5, 7, 9, 11),
}


@dataclass(frozen=True)
class Key:
    """
    Key definition: tonic name or pitch class and harmonic mode.
    """
    tonic: str = "C"
    mode: str = "Major"

    @property
    def tonic_pc(self) -> int:
        t = self.tonic.strip().upper()
        if t in PITCH_CLASS_NAMES:
            return PITCH_CLASS_NAMES[t]
        try:
            return int(self.tonic) % 12
        except ValueError:
            return 0

    @property
    def normalized_mode(self) -> str:
        m = self.mode.strip().upper().replace(" ", "").replace("_", "").replace("-", "")
        if "HARMONIC" in m:
            return "MINORHARMONIC"
        if "NATURAL" in m:
            return "MINORNATURAL"
        if "MINOR" in m:
            return "MINORHARMONIC"
        return "MAJOR"

    @property
    def scale_pcs(self) -> tuple[int, ...]:
        intervals = SCALE_INTERVALS.get(self.normalized_mode, SCALE_INTERVALS["MAJOR"])
        t0 = self.tonic_pc
        return tuple((t0 + iv) % 12 for iv in intervals)

    @property
    def name(self) -> str:
        return f"{self.tonic} {self.mode}"

    def __str__(self) -> str:
        return self.name

    def degree_to_pc(self, degree_1_indexed: int) -> int:
        idx = (degree_1_indexed - 1) % 7
        return self.scale_pcs[idx]


@dataclass(frozen=True)
class Chord:
    """
    Harmonic functional representation.
    """
    function: str
    inversion: int = 0
    is_seventh: bool = False
    is_downbeat: bool = False

    @property
    def symbol(self) -> str:
        return self.function


@dataclass(frozen=True)
class RuleViolation:
    """
    Record of a rule violation with metadata and severity.
    """
    rule_id: str
    severity: str = "hard_gate"  # "hard_gate" | "soft_penalty"
    penalty: float = 100000.0
    description: str = ""
    voices: tuple[int, ...] | None = None

    @property
    def is_hard(self) -> bool:
        return self.severity == "hard_gate"


@dataclass
class ValidationResult:
    """
    Result of validating a vertical state or transition.
    """
    is_valid: bool
    violations: list[RuleViolation] = field(default_factory=list)
    cost: float = 0.0

    @property
    def has_hard_violations(self) -> bool:
        return any(v.is_hard for v in self.violations)

    @property
    def hard_violations(self) -> list[RuleViolation]:
        return [v for v in self.violations if v.is_hard]

    @property
    def soft_violations(self) -> list[RuleViolation]:
        return [v for v in self.violations if not v.is_hard]


def to_satb(voicing: Any) -> tuple[int, int, int, int]:
    """
    Converts any compatible voicing structure to a 4-tuple (S, A, T, B).
    """
    if isinstance(voicing, Voicing):
        return (voicing.soprano, voicing.alto, voicing.tenor, voicing.bass)
    if hasattr(voicing, "soprano") and hasattr(voicing, "alto") and hasattr(voicing, "tenor") and hasattr(voicing, "bass"):
        return (int(voicing.soprano), int(voicing.alto), int(voicing.tenor), int(voicing.bass))
    if isinstance(voicing, (tuple, list)) and len(voicing) == 4:
        return (int(voicing[0]), int(voicing[1]), int(voicing[2]), int(voicing[3]))
    if isinstance(voicing, Mapping):
        # Support dict format e.g. {"soprano": 60, ...} or {"S": 60, ...}
        s = voicing.get("soprano", voicing.get("S", voicing.get("s")))
        a = voicing.get("alto", voicing.get("A", voicing.get("a")))
        t = voicing.get("tenor", voicing.get("T", voicing.get("t")))
        b = voicing.get("bass", voicing.get("B", voicing.get("b")))
        if s is not None and a is not None and t is not None and b is not None:
            return (int(s), int(a), int(t), int(b))
    raise ValueError(f"Cannot parse voicing into SATB 4-tuple: {voicing!r}")


def parse_key(key: Any) -> tuple[int, str]:
    """
    Extracts (tonic_pc, normalized_mode) from Key object, dict, or string.
    Supports both core.types.Key and core.key.Key seamlessly.
    """
    if hasattr(key, "tonic") and hasattr(key, "mode"):
        t = key.tonic
        if hasattr(t, "value"):  # PitchClass enum/class
            t_pc = int(t.value) % 12
        elif isinstance(t, int):
            t_pc = t % 12
        elif isinstance(t, str):
            t_str = t.strip().upper()
            t_pc = PITCH_CLASS_NAMES.get(t_str, 0)
        else:
            t_pc = 0

        m = key.mode
        m_str = m.value if hasattr(m, "value") else str(m)
        m_clean = m_str.strip().upper().replace(" ", "").replace("_", "").replace("-", "")
        if "HARMONIC" in m_clean:
            norm_mode = "MINORHARMONIC"
        elif "NATURAL" in m_clean:
            norm_mode = "MINORNATURAL"
        elif "MINOR" in m_clean:
            norm_mode = "MINORHARMONIC"
        else:
            norm_mode = "MAJOR"
        return t_pc, norm_mode

    if isinstance(key, Mapping):
        k = Key(tonic=str(key.get("tonic", "C")), mode=str(key.get("mode", "Major")))
        return k.tonic_pc, k.normalized_mode
    if isinstance(key, str):
        # E.g. "C", "Am", "c-moll", "G-dur"
        s = key.strip()
        is_minor = False
        if "-moll" in s.lower() or "m" in s[1:] or s.islower():
            is_minor = True
        tonic_part = s.split("-")[0].replace("moll", "").replace("dur", "").strip().rstrip("m").rstrip("M")
        k = Key(tonic=tonic_part or "C", mode="MinorHarmonic" if is_minor else "Major")
        return k.tonic_pc, k.normalized_mode
    if isinstance(key, int):
        return key % 12, "MAJOR"
    return 0, "MAJOR"


def parse_chord_symbol(chord: Any) -> str:
    """
    Normalizes a chord symbol to standard uppercase string representation.
    """
    if chord is None:
        return ""
    if isinstance(chord, Chord):
        sym = chord.function
    elif hasattr(chord, "function"):
        sym = str(chord.function)
    elif hasattr(chord, "symbol"):
        sym = str(chord.symbol)
    elif isinstance(chord, str):
        sym = chord
    else:
        sym = str(chord)

    # Normalize accents / slashes / spaces
    cleaned = sym.strip().replace("^", "").replace("/", "")
    # Check common synonyms
    upper_c = cleaned.upper()
    if upper_c in ("K64", "K6/4", "CAD64", "I64", "T64"):
        return "K64"
    if upper_c in ("D65", "D6/5"):
        return "D65"
    if upper_c in ("D43", "D4/3"):
        return "D43"
    if upper_c in ("D2",):
        return "D2"
    if upper_c in ("D7",):
        return "D7"
    if upper_c in ("T6", "T-6"):
        return "T6"
    if upper_c in ("S6", "S-6"):
        return "S6"
    if upper_c in ("D6", "D-6"):
        return "D6"
    return cleaned
