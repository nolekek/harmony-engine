"""
Standard MIDI file exporter for four-part SATB voicings.
Pure Python implementation (no external dependencies required).
"""

from typing import Any, Sequence
import struct
from pathlib import Path
from src.harmony.core.types import Voicing, to_satb


def _encode_variable_length(value: int) -> bytes:
    """Encodes an integer into MIDI variable-length quantity bytes."""
    buffer = bytearray()
    buffer.append(value & 0x7F)
    value >>= 7
    while value > 0:
        buffer.append((value & 0x7F) | 0x80)
        value >>= 7
    buffer.reverse()
    return bytes(buffer)


def export_to_midi(
    voicings: Sequence[Voicing | tuple[int, int, int, int]],
    output_path: str | Path,
    bpm: int = 80,
    ticks_per_beat: int = 480,
) -> Path:
    """
    Exports a sequence of SATB voicings to a standard MIDI Format 0 file.
    Each chord is held for 2 beats (half note = 960 ticks at 480 tpb).
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    chord_duration_ticks = ticks_per_beat * 2  # Half note
    velocity = 80

    track_events = bytearray()

    # Meta: Set Tempo
    tempo_us = int(60_000_000 / bpm)
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xFF\x51\x03" + struct.pack(">I", tempo_us)[1:])

    # Emit each chord
    for v in voicings:
        satb = to_satb(v)

        # Note On for all 4 voices (delta_time = 0 between them)
        for i, pitch in enumerate(satb):
            delta = 0
            track_events.extend(_encode_variable_length(delta))
            track_events.extend(bytes([0x90, pitch, velocity]))

        # Note Off for all 4 voices after duration
        for i, pitch in enumerate(satb):
            delta = chord_duration_ticks if i == 0 else 0
            track_events.extend(_encode_variable_length(delta))
            track_events.extend(bytes([0x80, pitch, 0]))

    # Meta: End of Track
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xFF\x2F\x00")

    # Header chunk: MThd, len=6, format=0, tracks=1, division=ticks_per_beat
    header_chunk = b"MThd" + struct.pack(">IHHH", 6, 0, 1, ticks_per_beat)

    # Track chunk: MTrk, len, track_data
    track_chunk = b"MTrk" + struct.pack(">I", len(track_events)) + bytes(track_events)

    out_p.write_bytes(header_chunk + track_chunk)
    return out_p
