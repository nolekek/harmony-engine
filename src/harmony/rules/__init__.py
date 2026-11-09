"""
Validation rules and engine for four-part harmony following the Brigade textbook.
"""

from src.harmony.core.types import (
    Voicing,
    Key,
    Chord,
    RuleViolation,
    ValidationResult,
    to_satb,
    parse_key,
    parse_chord_symbol,
)
from src.harmony.rules.spacing import (
    check_voice_ranges,
    check_voice_crossing,
    check_texture_spacing,
    validate_spacing,
    STANDARD_VOICE_RANGES,
    EXTENDED_VOICE_RANGES,
)
from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
    check_voice_overlapping,
    check_melodic_intervals,
    validate_voice_leading,
)
from src.harmony.rules.doubling import (
    check_main_triad_doubling,
    check_k64_doubling,
    check_deceptive_vi_doubling,
    check_doubling,
    get_triad_tones,
)
from src.harmony.rules.resolutions import (
    check_seventh_resolution,
    check_d43_resolution,
    check_leading_tone_resolution,
    validate_resolutions,
)
from src.harmony.rules.engine import (
    RuleEngine,
)
from src.harmony.rules.non_chord_tones import (
    NonChordToneType,
    classify_melodic_tone,
    check_voice_embellishments,
)

__all__ = [
    # Core types
    "Voicing",
    "Key",
    "Chord",
    "RuleViolation",
    "ValidationResult",
    "to_satb",
    "parse_key",
    "parse_chord_symbol",
    # Spacing
    "check_voice_ranges",
    "check_voice_crossing",
    "check_texture_spacing",
    "validate_spacing",
    "STANDARD_VOICE_RANGES",
    "EXTENDED_VOICE_RANGES",
    # Voice leading
    "check_parallel_fifths_and_octaves",
    "check_contrary_fifths_and_octaves",
    "check_hidden_fifths_and_octaves",
    "check_voice_overlapping",
    "check_melodic_intervals",
    "validate_voice_leading",
    # Doubling
    "check_main_triad_doubling",
    "check_k64_doubling",
    "check_deceptive_vi_doubling",
    "check_doubling",
    "get_triad_tones",
    # Resolutions
    "check_seventh_resolution",
    "check_d43_resolution",
    "check_leading_tone_resolution",
    "validate_resolutions",
    # Engine
    "RuleEngine",
]
