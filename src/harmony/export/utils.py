"""
Internal normalization and pitch spelling utilities for score exporters.
"""

from __future__ import annotations

from typing import Any


# Key signature fifths offset mapping
_MAJOR_FIFTHS: dict[str, int] = {
    "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5, "F#": 6, "C#": 7,
    "F": -1, "BB": -2, "EB": -3, "AB": -4, "DB": -5, "GB": -6, "CB": -7,
}
_MINOR_FIFTHS: dict[str, int] = {
    "A": 0, "E": 1, "B": 2, "F#": 3, "C#": 4, "G#": 5, "D#": 6, "A#": 7,
    "D": -1, "G": -2, "C": -3, "F": -4, "BB": -5, "EB": -6, "AB": -7,
}

# Standard scale spelling steps for fifths (-7 to +7)
# Pitch class 0..11 to (step, alter) for sharp and flat orientations
_SHARP_SPELLING: list[tuple[str, int]] = [
    ("C", 0),   # 0
    ("C", 1),   # 1 C#
    ("D", 0),   # 2
    ("D", 1),   # 3 D#
    ("E", 0),   # 4
    ("F", 0),   # 5
    ("F", 1),   # 6 F#
    ("G", 0),   # 7
    ("G", 1),   # 8 G#
    ("A", 0),   # 9
    ("A", 1),   # 10 A#
    ("B", 0),   # 11
]

_FLAT_SPELLING: list[tuple[str, int]] = [
    ("C", 0),   # 0
    ("D", -1),  # 1 Db
    ("D", 0),   # 2
    ("E", -1),  # 3 Eb
    ("E", 0),   # 4
    ("F", 0),   # 5
    ("G", -1),  # 6 Gb
    ("G", 0),   # 7
    ("A", -1),  # 8 Ab
    ("A", 0),   # 9
    ("B", -1),  # 10 Bb
    ("B", 0),   # 11
]


def extract_satb(voicing: Any) -> tuple[int, int, int, int]:
    """
    Extracts (soprano, alto, tenor, bass) integer MIDI pitches from any voicing representation.
    Supports Voicing dataclass, NamedTuple, tuple/list, and dict.
    """
    if hasattr(voicing, "soprano") and hasattr(voicing, "alto") and hasattr(voicing, "tenor") and hasattr(voicing, "bass"):
        return (
            int(getattr(voicing, "soprano")),
            int(getattr(voicing, "alto")),
            int(getattr(voicing, "tenor")),
            int(getattr(voicing, "bass")),
        )
    if isinstance(voicing, (tuple, list)) and len(voicing) == 4:
        return (int(voicing[0]), int(voicing[1]), int(voicing[2]), int(voicing[3]))
    if isinstance(voicing, dict):
        s = voicing.get("soprano", voicing.get("S", voicing.get("s", 60)))
        a = voicing.get("alto", voicing.get("A", voicing.get("a", 55)))
        t = voicing.get("tenor", voicing.get("T", voicing.get("t", 48)))
        b = voicing.get("bass", voicing.get("B", voicing.get("b", 40)))
        return (int(s), int(a), int(t), int(b))
    raise ValueError(f"Cannot extract SATB pitches from voicing: {voicing!r}")


def extract_chord_symbol(chord: Any) -> str:
    """
    Normalizes chord symbol to clean Roman numeral string representation.
    """
    if chord is None:
        return ""
    if isinstance(chord, str):
        return chord.strip()
    if hasattr(chord, "symbol"):
        return str(chord.symbol).strip()
    if hasattr(chord, "function"):
        fn = chord.function
        fn_val = fn.value if hasattr(fn, "value") else str(fn)
        inv = getattr(chord, "inversion", None)
        if inv is not None:
            inv_sym = getattr(inv, "symbol", "")
            if inv_sym and inv_sym not in fn_val:
                return f"{fn_val}{inv_sym}"
        return fn_val.strip()
    return str(chord).strip()


def extract_key_info(key: Any) -> tuple[str, str, int, bool, int]:
    """
    Returns (tonic_name, mode_name, tonic_pc, is_minor, fifths).
    """
    tonic_name = "C"
    mode_name = "Major"
    tonic_pc = 0
    is_minor = False

    if hasattr(key, "tonic") and hasattr(key, "mode"):
        t = getattr(key, "tonic")
        if hasattr(t, "sharp_name"):
            tonic_name = t.sharp_name
            tonic_pc = t.value
        elif hasattr(t, "name"):
            tonic_name = str(t.name)
            tonic_pc = getattr(t, "value", 0)
        else:
            tonic_name = str(t).strip()
            tonic_pc = getattr(key, "tonic_pc", 0)

        m = getattr(key, "mode")
        if hasattr(m, "is_minor"):
            is_minor = bool(m.is_minor)
            mode_name = m.value if hasattr(m, "value") else str(m)
        else:
            mode_str = str(m).strip()
            mode_name = mode_str
            is_minor = "minor" in mode_str.lower() or "moll" in mode_str.lower()

    elif isinstance(key, dict):
        tonic_name = str(key.get("tonic", "C")).strip()
        mode_str = str(key.get("mode", "Major")).strip()
        mode_name = mode_str
        is_minor = "minor" in mode_str.lower() or "moll" in mode_str.lower()

    elif isinstance(key, str):
        cleaned = key.strip()
        if "-moll" in cleaned.lower() or "minor" in cleaned.lower() or cleaned.islower():
            is_minor = True
            mode_name = "MinorHarmonic"
        else:
            mode_name = "Major"
        raw_tonic = cleaned.split("-")[0].split()[0].replace("moll", "").replace("dur", "").strip().rstrip("m").rstrip("M")
        tonic_name = raw_tonic or "C"

    # Calculate fifths for standard key signatures
    norm_tonic = tonic_name.upper().replace("♯", "#").replace("♭", "b")
    if is_minor:
        fifths = _MINOR_FIFTHS.get(norm_tonic, 0)
    else:
        fifths = _MAJOR_FIFTHS.get(norm_tonic, 0)

    return tonic_name, mode_name, tonic_pc, is_minor, fifths


def midi_to_spelled_note(midi: int, fifths: int = 0, is_minor: bool = False) -> tuple[str, int, int, str]:
    """
    Spells a MIDI pitch number (0..127) as (step, alter, octave, note_name).
    Example: 60 -> ('C', 0, 4, 'C4'), 61 with fifths=1 -> ('C', 1, 4, 'C#4').
    """
    pc = midi % 12
    octave = (midi // 12) - 1

    # In minor keys with harmonic minor, raised 7th degree is standard
    # e.g., in A minor (fifths=0), pc 8 is G#
    prefer_sharp = fifths >= 0
    if is_minor and fifths == 0 and pc == 8:  # G# in A minor
        step, alter = "G", 1
    elif is_minor and fifths == -1 and pc == 1:  # C# in D minor
        step, alter = "C", 1
    elif is_minor and fifths == -2 and pc == 6:  # F# in G minor
        step, alter = "F", 1
    elif is_minor and fifths == -3 and pc == 11:  # B natural in C minor
        step, alter = "B", 0
    else:
        if prefer_sharp:
            step, alter = _SHARP_SPELLING[pc]
        else:
            step, alter = _FLAT_SPELLING[pc]

    alter_str = "#" if alter == 1 else ("b" if alter == -1 else "")
    name = f"{step}{alter_str}{octave}"
    return step, alter, octave, name


def classify_voicing_spacing(s: int, a: int, t: int) -> str:
    """
    Classifies spacing into 'Close', 'Wide', or 'Mixed' based on SAT intervals.
    """
    d_sa = s - a
    d_at = a - t
    if d_sa <= 4 and d_at <= 4:
        return "Close"
    if (d_sa >= 5 or d_at >= 5) and (d_sa <= 12 and d_at <= 12):
        return "Wide"
    return "Mixed"
