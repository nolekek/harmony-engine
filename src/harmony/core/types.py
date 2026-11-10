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

    @classmethod
    def parse(cls, val: Any) -> "Key":
        """
        Parses Key from string, dict, or Key instance.
        Supports 'C Major', 'A minor', 'c-moll', 'G-dur', 'F# minor', 'Bb Major', etc.
        """
        if isinstance(val, Key):
            return val
        if hasattr(val, "tonic") and hasattr(val, "mode"):
            t = val.tonic
            t_str = t.sharp_name if hasattr(t, "sharp_name") else str(t)
            m = val.mode
            m_str = m.value if hasattr(m, "value") else str(m)
            return cls(tonic=t_str, mode=m_str)
        if isinstance(val, Mapping):
            return cls(tonic=str(val.get("tonic", "C")), mode=str(val.get("mode", "Major")))
        if isinstance(val, str):
            import re
            cleaned = val.strip()
            german_match = re.match(r"^([A-Ga-g][#bB♭♯]?)[-_](dur|moll)$", cleaned, re.IGNORECASE)
            if german_match:
                note_str, mode_str = german_match.groups()
                is_min = mode_str.lower() == "moll"
                return cls(tonic=note_str.capitalize(), mode="MinorHarmonic" if is_min else "Major")

            parts = re.split(r"[\s:_]+", cleaned)
            if len(parts) >= 2:
                note_str = parts[0]
                mode_str = "_".join(parts[1:]).lower()
                is_min = "minor" in mode_str or "moll" in mode_str
                return cls(tonic=note_str.capitalize(), mode="MinorHarmonic" if is_min else "Major")

            raw = parts[0]
            is_min = raw[0].islower() or (len(raw) > 1 and raw.endswith("m") and not raw.endswith("b"))
            note_str = raw.rstrip("m").rstrip("M")
            return cls(tonic=note_str.capitalize(), mode="MinorHarmonic" if is_min else "Major")
        return cls("C", "Major")

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
        k = Key.parse(key)
        return k.tonic_pc, k.normalized_mode
    if isinstance(key, str):
        # E.g. "C", "Am", "c-moll", "G-dur", "C Major", "A Minor"
        k = Key.parse(key)
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
    if isinstance(chord, str):
        sym = chord
    elif isinstance(chord, Chord):
        sym = chord.function
    elif hasattr(chord, "function"):
        fn = chord.function
        fn_val = fn.value if hasattr(fn, "value") else str(fn)
        if hasattr(chord, "inversion") and chord.inversion is not None:
            inv = chord.inversion
            inv_val = inv.value if hasattr(inv, "value") else str(inv)
            if fn_val.upper().startswith("K"):
                sym = "K64"
            elif inv_val in ("53", "0", 0, "ROOT", "root", "", None):
                sym = fn_val
            else:
                sym = f"{fn_val}{inv_val}"
        else:
            sym = fn_val
    elif hasattr(chord, "value"):
        sym = str(chord.value)
    elif hasattr(chord, "symbol"):
        sym = str(chord.symbol)
    else:
        sym = str(chord)

    # Normalize accents / slashes / spaces
    cleaned = sym.strip().replace("^", "").replace("/", "")
    # Check common synonyms (T64 is deliberately excluded from K64 per Brigade rules)
    upper_c = cleaned.upper()
    if upper_c in ("K64", "K6/4", "CAD64", "I64"):
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


@dataclass(frozen=True)
class TimeSignature:
    """
    Musical time signature (meter), e.g. 4/4, 3/4, 6/8, 2/4.
    """
    beats: int = 4
    beat_type: int = 4

    @property
    def measure_duration_quarters(self) -> float:
        """Total duration of one complete measure in quarter notes."""
        return self.beats * (4.0 / self.beat_type)

    @classmethod
    def parse(cls, val: Any) -> "TimeSignature":
        if isinstance(val, TimeSignature):
            return val
        if isinstance(val, (tuple, list)) and len(val) >= 2:
            return cls(int(val[0]), int(val[1]))
        if isinstance(val, str):
            s = val.strip().lower()
            if s == "c":
                return cls(4, 4)
            if s in ("c/", "cut", "alla_breve", "allabreve"):
                return cls(2, 2)
            if "/" in s:
                parts = s.split("/")
                return cls(int(parts[0]), int(parts[1]))
        return cls(4, 4)

    def is_downbeat(self, beat_offset_quarters: float) -> bool:
        """
        Determines whether a quarter-note offset from measure start is a metric downbeat/accent.
        """
        offset = round(beat_offset_quarters, 4)
        if offset == 0.0:
            return True
        # Secondary downbeat in 4/4 or 2/2 (the 3rd quarter note)
        if self.beats == 4 and self.beat_type == 4 and abs(offset - 2.0) < 1e-4:
            return True
        if self.beats == 2 and self.beat_type == 2 and abs(offset - 2.0) < 1e-4:
            return True
        # In 6/8, the 4th eighth note (offset 1.5 quarters) is the secondary accent
        if self.beats == 6 and self.beat_type == 8 and abs(offset - 1.5) < 1e-4:
            return True
        return False

    def __str__(self) -> str:
        return f"{self.beats}/{self.beat_type}"


DURATION_TO_QUARTERS: dict[str, float] = {
    "whole": 4.0,
    "dotted_whole": 6.0,
    "whole.": 6.0,
    "dotted_half": 3.0,
    "half_dot": 3.0,
    "half.": 3.0,
    "half": 2.0,
    "dotted_quarter": 1.5,
    "quarter_dot": 1.5,
    "quarter.": 1.5,
    "quarter": 1.0,
    "dotted_eighth": 0.75,
    "eighth_dot": 0.75,
    "eighth.": 0.75,
    "eighth": 0.5,
    "dotted_sixteenth": 0.375,
    "sixteenth": 0.25,
}


def parse_duration_quarters(dur: Any) -> float:
    """Converts a duration string, float, or int to quarter-note units."""
    if isinstance(dur, (int, float)):
        return float(dur)
    if isinstance(dur, str):
        key = dur.strip().lower()
        if key in DURATION_TO_QUARTERS:
            return DURATION_TO_QUARTERS[key]
        try:
            return float(key)
        except ValueError:
            pass
    return 2.0


def quarters_to_xml_type_and_dots(quarters: float) -> tuple[str, int]:
    """
    Returns (xml_type_name, dot_count) for a given duration in quarter units.
    """
    q = round(quarters, 4)
    if abs(q - 6.0) < 1e-4:
        return ("whole", 1)
    if abs(q - 4.0) < 1e-4:
        return ("whole", 0)
    if abs(q - 3.0) < 1e-4:
        return ("half", 1)
    if abs(q - 2.0) < 1e-4:
        return ("half", 0)
    if abs(q - 1.5) < 1e-4:
        return ("quarter", 1)
    if abs(q - 1.0) < 1e-4:
        return ("quarter", 0)
    if abs(q - 0.75) < 1e-4:
        return ("eighth", 1)
    if abs(q - 0.5) < 1e-4:
        return ("eighth", 0)
    if abs(q - 0.375) < 1e-4:
        return ("sixteenth", 1)
    if abs(q - 0.25) < 1e-4:
        return ("sixteenth", 0)
    if q >= 2.0:
        return ("half", 0)
    return ("quarter", 0)


def calculate_metric_structure(
    notes: Sequence[Any],
    default_time_signature: Any = "4/4",
) -> list[dict[str, Any]]:
    """
    Calculates exact metric coordinates for a sequence of melody notes or chord slices.
    Handles variable durations, dotted notes, and time signature changes.
    Returns for each note:
    - measure (int, 1-indexed)
    - offset_in_measure (float, in quarters)
    - is_downbeat (bool)
    - time_signature (TimeSignature)
    - duration (str)
    - duration_quarters (float)
    - time_sig_changed (bool)
    """
    curr_time_sig = TimeSignature.parse(default_time_signature)
    curr_measure = 1
    curr_offset = 0.0
    prev_time_sig = None

    result: list[dict[str, Any]] = []

    for n in notes:
        # Check if note carries its own time signature change
        note_time_sig = None
        if isinstance(n, dict):
            if "time_signature" in n and n["time_signature"]:
                note_time_sig = TimeSignature.parse(n["time_signature"])
            dur_raw = n.get("duration", "half")
            pitch = n.get("pitch", 60)
            explicit_db = n.get("is_downbeat")
        else:
            dur_raw = "half"
            pitch = int(n)
            explicit_db = None

        if note_time_sig is not None and note_time_sig != curr_time_sig:
            if curr_offset > 1e-4:
                curr_measure += 1
                curr_offset = 0.0
            curr_time_sig = note_time_sig

        dur_q = parse_duration_quarters(dur_raw)

        while curr_offset >= curr_time_sig.measure_duration_quarters - 1e-4:
            curr_measure += 1
            curr_offset -= curr_time_sig.measure_duration_quarters
        if abs(curr_offset) < 1e-4:
            curr_offset = 0.0

        time_sig_changed = (curr_time_sig != prev_time_sig)
        prev_time_sig = curr_time_sig

        if explicit_db is not None:
            is_db = bool(explicit_db)
        else:
            is_db = curr_time_sig.is_downbeat(curr_offset)

        xml_type, dots = quarters_to_xml_type_and_dots(dur_q)
        norm_dur_name = f"dotted_{xml_type}" if dots > 0 else xml_type

        result.append({
            "pitch": pitch,
            "duration": norm_dur_name,
            "duration_quarters": dur_q,
            "measure": curr_measure,
            "offset_in_measure": round(curr_offset, 4),
            "is_downbeat": is_db,
            "time_signature": curr_time_sig,
            "time_sig_changed": time_sig_changed,
        })

        curr_offset += dur_q

    return result
