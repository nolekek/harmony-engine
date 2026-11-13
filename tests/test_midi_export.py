"""
Tests for Standard MIDI Format 1 exporter (T25; REPORT #57, #58; BK-13).
Verifies:
- 4 tracks in Format 1 (Soprano, Alto, Tenor, Bass)
- Channels 0..3 with Program Change 52 (Choir Aahs) on each channel
- Exact durations from `durations` parameter (not hardcoded half)
- Byte-level MThd and MTrk validation
"""

import struct
import tempfile
from pathlib import Path

from src.harmony.core.types import Voicing
from src.harmony.export.midi import export_to_midi


def parse_midi_raw_bytes(data: bytes) -> dict:
    """Manually parses MIDI binary structure without relying on external libraries."""
    assert data.startswith(b"MThd"), "File must start with MThd chunk"
    length, fmt, num_tracks, division = struct.unpack(">IHHH", data[4:14])
    assert length == 6, f"MThd length must be 6, got {length}"

    offset = 14
    tracks = []
    while offset < len(data):
        assert data[offset : offset + 4] == b"MTrk", f"Expected MTrk at offset {offset}"
        track_len = struct.unpack(">I", data[offset + 4 : offset + 8])[0]
        track_data = data[offset + 8 : offset + 8 + track_len]
        tracks.append(track_data)
        offset += 8 + track_len

    return {
        "format": fmt,
        "num_tracks": num_tracks,
        "division": division,
        "tracks": tracks,
    }


def test_midi_format_1_four_tracks_and_program_change():
    """Checks Format 1, 4 tracks, channels 0..3, and Program Change 52 (Choir Aahs)."""
    voicings = [
        Voicing(64, 60, 55, 48),  # E4, C4, G3, C3
        Voicing(65, 60, 57, 41),  # F4, C4, A3, F2
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        midi_path = Path(tmpdir) / "choir_format1.mid"
        export_to_midi(voicings, midi_path)
        assert midi_path.exists()

        raw_data = midi_path.read_bytes()
        parsed = parse_midi_raw_bytes(raw_data)

        # Header asserts
        assert parsed["format"] == 1, f"Expected MIDI Format 1, got {parsed['format']}"
        assert parsed["num_tracks"] == 4, f"Expected 4 tracks, got {parsed['num_tracks']}"
        assert len(parsed["tracks"]) == 4, "Must contain exactly 4 MTrk chunks"

        # Check Program Change 52 (0x34) on channels 0..3
        for ch, track_data in enumerate(parsed["tracks"]):
            expected_pc_byte = 0xC0 | ch
            found_pc = False
            for i in range(len(track_data) - 1):
                if track_data[i] == expected_pc_byte and track_data[i + 1] == 52:
                    found_pc = True
                    break
            assert found_pc, f"Track {ch} (channel {ch}) missing Program Change 52 (0x{expected_pc_byte:02X} 0x34)"

            # Ensure track ends with End of Track meta (FF 2F 00)
            assert b"\xFF\x2F\x00" in track_data, f"Track {ch} missing End of Track marker"


def test_midi_durations_not_hardcoded_half():
    """
    Checks that notes have durations derived from the `durations` parameter.
    For quarter note: ticks = 480 (division * 1.0)
    For whole note: ticks = 1920 (division * 4.0)
    """
    voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(60, 60, 55, 48),
    ]
    durations = ["quarter", "whole"]

    with tempfile.TemporaryDirectory() as tmpdir:
        midi_path = Path(tmpdir) / "durations_test.mid"
        export_to_midi(voicings, midi_path, durations=durations)

        raw_data = midi_path.read_bytes()
        parsed = parse_midi_raw_bytes(raw_data)
        division = parsed["division"]
        assert division == 480

        # In Soprano track (track 0), check Note-Off deltas
        # Quarter note = 480 ticks. In variable-length quantity:
        # 480 = 0x01E0 -> 0x83 0x60
        # Whole note = 1920 ticks.
        # 1920 = 0x0780 -> 0x8F 0x00
        soprano_track = parsed["tracks"][0]

        # 480 ticks delta encoded: 0x83 0x60 followed by Note Off status 0x80
        quarter_note_off = bytes([0x83, 0x60, 0x80, 64, 0])
        assert quarter_note_off in soprano_track, "Soprano quarter note off with 480 ticks not found"

        # Whole note = 1920 ticks encoded: 0x8F 0x00 followed by Note Off status 0x80
        whole_note_off = bytes([0x8F, 0x00, 0x80, 60, 0])
        assert whole_note_off in soprano_track, "Soprano whole note off with 1920 ticks not found"


def test_midi_import_variable_durations_and_metric_grid():
    """
    Tests that parse_midi_file computes actual durations and metric coordinates
    using MetricGrid instead of hardcoding 'half' and i % 2 == 0.
    """
    from backend.importers import parse_midi_file

    # 3 chords in 4/4: quarter (1 beat), quarter (1 beat), half (2 beats) = 1 full measure
    voicings = [
        Voicing(64, 60, 55, 48),  # Beat 0: downbeat
        Voicing(65, 60, 57, 41),  # Beat 1: off-beat
        Voicing(67, 59, 55, 43),  # Beat 2: secondary downbeat
    ]
    durations = ["quarter", "quarter", "half"]

    with tempfile.TemporaryDirectory() as tmpdir:
        midi_path = Path(tmpdir) / "metric_test.mid"
        export_to_midi(voicings, midi_path, durations=durations, time_signature="4/4")
        midi_bytes = midi_path.read_bytes()

        parsed = parse_midi_file(midi_bytes)

        soprano = parsed["soprano_melody"]
        assert len(soprano) == 3

        # Durations must NOT be hardcoded half
        assert soprano[0]["duration"] == "quarter"
        assert soprano[1]["duration"] == "quarter"
        assert soprano[2]["duration"] == "half"

        # Downbeats: in 4/4 meter, beat 0 (quarter 0) is downbeat, beat 1 (quarter 1) is NOT, beat 2 (quarter 2) is downbeat
        assert soprano[0]["is_downbeat"] is True
        assert soprano[1]["is_downbeat"] is False
        assert soprano[2]["is_downbeat"] is True

        # Measures must be 1 for all of them
        assert soprano[0]["measure"] == 1
        assert soprano[1]["measure"] == 1
        assert soprano[2]["measure"] == 1

