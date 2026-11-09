"""
Standard MIDI file exporter for four-part SATB voicings.
Pure Python implementation (no external dependencies required).
Supports variable durations, dotted notes, and time signature changes.
"""

from typing import Any, Sequence
import struct
import math
from pathlib import Path
from src.harmony.core.types import (
    Voicing,
    to_satb,
    TimeSignature,
    calculate_metric_structure,
)


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


def _encode_time_signature_event(time_sig: TimeSignature) -> bytes:
    """Encodes MIDI Time Signature Meta Event (FF 58 04 nn dd cc bb)."""
    dd = int(math.log2(time_sig.beat_type)) if time_sig.beat_type > 0 else 2
    return b"\xFF\x58\x04" + bytes([time_sig.beats, dd, 24, 8])


def export_to_midi(
    voicings: Sequence[Voicing | tuple[int, int, int, int]],
    output_path: str | Path,
    bpm: int = 80,
    ticks_per_beat: int = 480,
    durations: Sequence[Any] | None = None,
    time_signature: Any = "4/4",
) -> Path:
    """
    Exports a sequence of SATB voicings to a standard MIDI Format 0 file.
    Supports variable chord durations, dotted rhythms, and time signatures.
    """
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    melody_items = []
    for i, v in enumerate(voicings):
        dur = durations[i] if durations and i < len(durations) else "half"
        melody_items.append({"pitch": to_satb(v)[0], "duration": dur})

    metric_info = calculate_metric_structure(melody_items, default_time_signature=time_signature)

    velocity = 80
    track_events = bytearray()

    # Meta: Set Tempo
    tempo_us = int(60_000_000 / bpm)
    track_events.extend(_encode_variable_length(0))
    track_events.extend(b"\xFF\x51\x03" + struct.pack(">I", tempo_us)[1:])

    # Initial Time Signature
    init_ts = metric_info[0]["time_signature"] if metric_info else TimeSignature.parse(time_signature)
    track_events.extend(_encode_variable_length(0))
    track_events.extend(_encode_time_signature_event(init_ts))

    # Emit each chord
    for i, v in enumerate(voicings):
        satb = to_satb(v)
        info = metric_info[i]
        dur_quarters = info["duration_quarters"]
        chord_ticks = int(round(dur_quarters * ticks_per_beat))

        # Check for mid-piece time signature change
        if i > 0 and info["time_sig_changed"]:
            track_events.extend(_encode_variable_length(0))
            track_events.extend(_encode_time_signature_event(info["time_signature"]))

        # Note On for all 4 voices (delta_time = 0 between them)
        for voice_idx, pitch in enumerate(satb):
            delta = 0
            track_events.extend(_encode_variable_length(delta))
            track_events.extend(bytes([0x90, pitch, velocity]))

        # Note Off for all 4 voices after duration
        for voice_idx, pitch in enumerate(satb):
            delta = chord_ticks if voice_idx == 0 else 0
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
