"""
ASCII score formatter for four-part SATB harmony.

Produces clear, human-readable terminal visualizations of chord voicings,
voice leading trajectories, and Roman numeral harmonic analyses.
"""

from __future__ import annotations

from typing import Any, Sequence

from .utils import (
    classify_voicing_spacing,
    extract_chord_symbol,
    extract_key_info,
    extract_satb,
    midi_to_spelled_note,
)


def format_ascii_score(
    voicings: Sequence[Any],
    chords: Sequence[Any] | None = None,
    key: Any = "C Major",
) -> str:
    """
    Format SATB voicings and harmonic analysis into a structured ASCII score.

    Args:
        voicings: List of voicings (Voicing objects, tuples, or dicts).
        chords: Optional list of chords/functions (Chord objects or strings).
        key: Key representation (Key object, string, or dict).

    Returns:
        Formatted multi-line ASCII string representation.
    """
    if not voicings:
        return "(empty score: no voicings provided)"

    tonic_name, mode_name, _, is_minor, fifths = extract_key_info(key)
    chord_list = list(chords) if chords is not None else []

    parsed_rows: list[dict[str, Any]] = []
    for i, v in enumerate(voicings):
        s, a, t, b = extract_satb(v)
        c = chord_list[i] if i < len(chord_list) else ""
        c_sym = extract_chord_symbol(c)

        _, _, _, s_name = midi_to_spelled_note(s, fifths, is_minor)
        _, _, _, a_name = midi_to_spelled_note(a, fifths, is_minor)
        _, _, _, t_name = midi_to_spelled_note(t, fifths, is_minor)
        _, _, _, b_name = midi_to_spelled_note(b, fifths, is_minor)

        spacing = classify_voicing_spacing(s, a, t)
        sa_int = s - a
        at_int = a - t
        tb_int = t - b

        parsed_rows.append({
            "idx": i + 1,
            "s_str": f"{s_name} ({s})",
            "a_str": f"{a_name} ({a})",
            "t_str": f"{t_name} ({t})",
            "b_str": f"{b_name} ({b})",
            "s_short": s_name,
            "a_short": a_name,
            "t_short": t_name,
            "b_short": b_name,
            "chord": c_sym or "-",
            "spacing": spacing,
            "intervals": f"SA:{sa_int} AT:{at_int} TB:{tb_int}",
        })

    lines: list[str] = []
    header_title = f"=== SATB HARMONY SCORE [{tonic_name} {mode_name}] ({len(voicings)} chords) ==="
    lines.append(header_title)
    lines.append("-" * len(header_title))

    # 1. Vertical Detailed Table
    col_idx = "#"
    col_s = "Soprano (S)"
    col_a = "Alto (A)"
    col_t = "Tenor (T)"
    col_b = "Bass (B)"
    col_ch = "Function"
    col_sp = "Spacing"
    col_iv = "Intervals"

    fmt = "{:<4} {:<13} {:<13} {:<13} {:<13} {:<10} {:<9} {:<14}"
    lines.append(fmt.format(col_idx, col_s, col_a, col_t, col_b, col_ch, col_sp, col_iv))
    lines.append("-" * 85)

    for r in parsed_rows:
        lines.append(fmt.format(
            f"{r['idx']}:",
            r["s_str"],
            r["a_str"],
            r["t_str"],
            r["b_str"],
            r["chord"],
            r["spacing"],
            r["intervals"],
        ))

    lines.append("-" * 85)
    lines.append("")

    # 2. Horizontal Voice-Leading Ribbon (Piano-roll / score view)
    lines.append("--- Linear Voice Trajectories ---")
    s_line = "  [S] " + " | ".join(f"{r['s_short']:<4}" for r in parsed_rows) + " |"
    a_line = "  [A] " + " | ".join(f"{r['a_short']:<4}" for r in parsed_rows) + " |"
    t_line = "  [T] " + " | ".join(f"{r['t_short']:<4}" for r in parsed_rows) + " |"
    b_line = "  [B] " + " | ".join(f"{r['b_short']:<4}" for r in parsed_rows) + " |"
    sep    = "  --- " + "-+-".join("----" for _ in parsed_rows) + "-+"
    f_line = "  [F] " + " | ".join(f"{r['chord']:<4}" for r in parsed_rows) + " |"

    lines.extend([s_line, a_line, t_line, b_line, sep, f_line])
    lines.append("=" * len(header_title))

    return "\n".join(lines)
