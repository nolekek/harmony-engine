"""
Tests for MusicXML measure integrity, duration sums, tie generation, and backup boundaries (REPORT #8; §1.9; BK-03).
"""

import xml.etree.ElementTree as ET

from src.harmony.core.types import Voicing
from src.harmony.export.musicxml import export_to_musicxml


def test_musicxml_measures_duration_sum_and_ties_44():
    """
    REPORT §1.9: For default melody [64,65,67,64,62,60] with durations
    [half, half, half, half, half, whole] in 4/4 meter:
    - Every measure must have voice 1 duration sum == 16 divisions (divisions=4).
    - Notes crossing bar lines must be split with <tie> (<tie type='start'/>/<tie type='stop'/>)
      and <notations><tied .../></notations>.
    - <backup> durations must not exceed measure length (16 divisions).
    """
    voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
        Voicing(67, 60, 55, 43),
        Voicing(64, 60, 55, 48),
        Voicing(62, 59, 55, 43),
        Voicing(60, 60, 55, 48),
    ]
    chords = ["T", "S6", "D", "T", "D", "T"]
    durations = ["half", "half", "half", "half", "half", "whole"]

    xml_str = export_to_musicxml(
        voicings=voicings,
        chords=chords,
        key="C Major",
        durations=durations,
        time_signature="4/4",
    )

    root = ET.fromstring(xml_str)
    measures = root.findall(".//measure")
    assert len(measures) >= 3, "Expected at least 3 measures"

    found_tie_start = False
    found_tie_stop = False
    found_tied_notation = False

    for m in measures:
        m_num = m.get("number")
        notes = m.findall("note")

        # Voice 1 notes (including rests for voice 1)
        v1_notes = [n for n in notes if n.find("voice") is not None and n.find("voice").text == "1"]
        v1_dur_sum = sum(int(n.find("duration").text) for n in v1_notes if n.find("duration") is not None)
        assert v1_dur_sum == 16, f"Measure {m_num} voice 1 duration sum is {v1_dur_sum}, expected 16"

        # Check backups
        backups = [int(b.find("duration").text) for b in m.findall("backup") if b.find("duration") is not None]
        for b_dur in backups:
            assert b_dur <= 16, f"Measure {m_num} backup duration {b_dur} exceeds measure capacity 16"

        # Check ties
        for n in notes:
            for tie in n.findall("tie"):
                if tie.get("type") == "start":
                    found_tie_start = True
                elif tie.get("type") == "stop":
                    found_tie_stop = True
            for tied in n.findall(".//notations/tied"):
                if tied.get("type") in ("start", "stop"):
                    found_tied_notation = True

    assert found_tie_start, "Expected to find at least one <tie type='start'/>"
    assert found_tie_stop, "Expected to find at least one <tie type='stop'/>"
    assert found_tied_notation, "Expected to find <tied> notation element"


def test_musicxml_measures_duration_sum_34():
    """
    3/4 meter case: measure duration sum must equal 12 divisions (3 beats * 4 divs).
    Melody with notes crossing barline in 3/4.
    """
    voicings = [
        Voicing(64, 60, 55, 48),  # half (2 beats = 8 divs)
        Voicing(65, 60, 57, 41),  # half (2 beats = 8 divs) -> crosses barline at beat 3!
        Voicing(67, 60, 55, 43),  # half (2 beats = 8 divs)
    ]
    chords = ["T", "S", "D"]
    durations = ["half", "half", "half"]

    xml_str = export_to_musicxml(
        voicings=voicings,
        chords=chords,
        key="C Major",
        durations=durations,
        time_signature="3/4",
    )

    root = ET.fromstring(xml_str)
    measures = root.findall(".//measure")
    assert len(measures) >= 2

    for m in measures:
        m_num = m.get("number")
        notes = m.findall("note")
        v1_notes = [n for n in notes if n.find("voice") is not None and n.find("voice").text == "1"]
        v1_dur_sum = sum(int(n.find("duration").text) for n in v1_notes if n.find("duration") is not None)
        assert v1_dur_sum == 12, f"Measure {m_num} voice 1 duration sum is {v1_dur_sum}, expected 12"

        backups = [int(b.find("duration").text) for b in m.findall("backup") if b.find("duration") is not None]
        for b_dur in backups:
            assert b_dur <= 12, f"Measure {m_num} backup duration {b_dur} exceeds measure capacity 12"
