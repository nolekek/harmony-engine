"""
Tests for time signatures (meters), meter changes, and dotted durations.
Verifies symbolic metric calculations, MusicXML dots and times, MIDI ticks, and pipeline integration.
"""

import xml.etree.ElementTree as ET
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.harmony.core.types import (
    Key,
    Chord,
    Voicing,
    TimeSignature,
    parse_duration_quarters,
    quarters_to_xml_type_and_dots,
    calculate_metric_structure,
)
from src.harmony.export.musicxml import export_to_musicxml
from src.harmony.export.midi import export_to_midi
from src.harmony.pipeline import Harmonizer
from backend.main import app
from backend.importers import parse_text_melody
from backend.grader import grade_satb_solution

client = TestClient(app)


def test_time_signature_parsing_and_measure_duration():
    ts44 = TimeSignature.parse("4/4")
    assert ts44.beats == 4
    assert ts44.beat_type == 4
    assert ts44.measure_duration_quarters == 4.0

    ts34 = TimeSignature.parse("3/4")
    assert ts34.beats == 3
    assert ts34.beat_type == 4
    assert ts34.measure_duration_quarters == 3.0

    ts68 = TimeSignature.parse("6/8")
    assert ts68.beats == 6
    assert ts68.beat_type == 8
    assert ts68.measure_duration_quarters == 3.0

    ts_cut = TimeSignature.parse("c/")
    assert ts_cut.beats == 2
    assert ts_cut.beat_type == 2
    assert ts_cut.measure_duration_quarters == 4.0


def test_time_signature_downbeat_accents():
    ts44 = TimeSignature(4, 4)
    assert ts44.is_downbeat(0.0) is True
    assert ts44.is_downbeat(1.0) is False
    assert ts44.is_downbeat(2.0) is True   # Secondary accent in 4/4
    assert ts44.is_downbeat(3.0) is False

    ts34 = TimeSignature(3, 4)
    assert ts34.is_downbeat(0.0) is True
    assert ts34.is_downbeat(1.0) is False  # In 3/4, beat 2 is weak
    assert ts34.is_downbeat(2.0) is False  # In 3/4, beat 3 is weak

    ts68 = TimeSignature(6, 8)
    assert ts68.is_downbeat(0.0) is True
    assert ts68.is_downbeat(0.5) is False
    assert ts68.is_downbeat(1.0) is False
    assert ts68.is_downbeat(1.5) is True   # 4th eighth note is secondary accent in 6/8


def test_dotted_durations_conversion():
    assert parse_duration_quarters("whole") == 4.0
    assert parse_duration_quarters("dotted_half") == 3.0
    assert parse_duration_quarters("half.") == 3.0
    assert parse_duration_quarters("half") == 2.0
    assert parse_duration_quarters("dotted_quarter") == 1.5
    assert parse_duration_quarters("quarter.") == 1.5
    assert parse_duration_quarters("quarter") == 1.0
    assert parse_duration_quarters("dotted_eighth") == 0.75
    assert parse_duration_quarters("eighth.") == 0.75
    assert parse_duration_quarters("eighth") == 0.5
    assert parse_duration_quarters("sixteenth") == 0.25

    xml_t, dots = quarters_to_xml_type_and_dots(3.0)
    assert xml_t == "half" and dots == 1

    xml_t, dots = quarters_to_xml_type_and_dots(1.5)
    assert xml_t == "quarter" and dots == 1

    xml_t, dots = quarters_to_xml_type_and_dots(0.75)
    assert xml_t == "eighth" and dots == 1


def test_metric_structure_34_and_measure_grouping():
    # 3 measures of 3/4:
    # m1: quarter (1.0) + quarter (1.0) + quarter (1.0)
    # m2: dotted_half (3.0)
    # m3: half (2.0) + quarter (1.0)
    notes = [
        {"pitch": 64, "duration": "quarter"},
        {"pitch": 65, "duration": "quarter"},
        {"pitch": 67, "duration": "quarter"},
        {"pitch": 69, "duration": "dotted_half"},
        {"pitch": 67, "duration": "half"},
        {"pitch": 65, "duration": "quarter"},
    ]
    struct = calculate_metric_structure(notes, default_time_signature="3/4")
    assert len(struct) == 6

    # Measure 1
    assert struct[0]["measure"] == 1 and struct[0]["is_downbeat"] is True
    assert struct[1]["measure"] == 1 and struct[1]["is_downbeat"] is False
    assert struct[2]["measure"] == 1 and struct[2]["is_downbeat"] is False

    # Measure 2
    assert struct[3]["measure"] == 2 and struct[3]["is_downbeat"] is True
    assert struct[3]["duration"] == "dotted_half"

    # Measure 3
    assert struct[4]["measure"] == 3 and struct[4]["is_downbeat"] is True
    assert struct[5]["measure"] == 3 and struct[5]["is_downbeat"] is False


def test_metric_structure_meter_change():
    # Measure 1-2 in 4/4, Measure 3 in 3/4
    notes = [
        {"pitch": 60, "duration": "half"},
        {"pitch": 62, "duration": "half"},
        {"pitch": 64, "duration": "whole"},
        {"pitch": 65, "duration": "dotted_half", "time_signature": "3/4"},
    ]
    struct = calculate_metric_structure(notes, default_time_signature="4/4")
    assert struct[0]["measure"] == 1 and str(struct[0]["time_signature"]) == "4/4"
    assert struct[1]["measure"] == 1
    assert struct[2]["measure"] == 2 and str(struct[2]["time_signature"]) == "4/4"
    assert struct[3]["measure"] == 3 and str(struct[3]["time_signature"]) == "3/4"
    assert struct[3]["time_sig_changed"] is True


def test_musicxml_export_with_34_and_dots():
    voicings = [
        Voicing(64, 60, 55, 48),  # C4:dotted_quarter
        Voicing(65, 60, 57, 41),  # D4:eighth
        Voicing(67, 60, 55, 43),  # E4:quarter
        Voicing(64, 60, 55, 48),  # C4:dotted_half
    ]
    chords = ["T", "S", "D", "T"]
    durations = ["dotted_quarter", "eighth", "quarter", "dotted_half"]

    xml_str = export_to_musicxml(
        voicings=voicings,
        chords=chords,
        key="C Major",
        title="Waltz in 3/4",
        durations=durations,
        time_signature="3/4",
    )

    root = ET.fromstring(xml_str)
    # Check time element in measure 1
    beats = root.find(".//measure[@number='1']//time/beats")
    assert beats is not None and beats.text == "3"
    beat_type = root.find(".//measure[@number='1']//time/beat-type")
    assert beat_type is not None and beat_type.text == "4"

    # Check that <dot/> exists on the dotted notes
    dots = root.findall(".//note/dot")
    assert len(dots) >= 4  # 1 in soprano m1 (dotted_quarter), 1 in soprano m2 (dotted_half), plus other voices

    # Verify measures: measure 1 has 3 chords (1.5 + 0.5 + 1.0 = 3.0), measure 2 has 1 chord (3.0)
    m1_soprano = root.findall(".//measure[@number='1']//note[voice='1']")
    assert len(m1_soprano) == 3

    m2_soprano = root.findall(".//measure[@number='2']//note[voice='1']")
    assert len(m2_soprano) == 1


def test_midi_export_with_variable_durations():
    voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
    ]
    durations = ["dotted_quarter", "eighth"]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_mid = Path(tmpdir) / "test_dots.mid"
        export_to_midi(
            voicings=voicings,
            output_path=out_mid,
            durations=durations,
            time_signature="3/4",
        )
        assert out_mid.exists()
        raw_bytes = out_mid.read_bytes()
        # Verify MIDI header
        assert raw_bytes.startswith(b"MThd")
        # Verify Time Signature meta event presence (FF 58 04 03 02 ...)
        assert b"\xFF\x58\x04\x03\x02" in raw_bytes


def test_parse_text_with_meter_and_dots():
    # Parse text with leading meter and dotted durations
    text = "[3/4] C4:dotted_quarter D4:eighth E4:quarter F4:dotted_half"
    notes = parse_text_melody(text, key_tonic="C", key_mode="Major")
    assert len(notes) == 4
    assert notes[0]["duration"] == "dotted_quarter"
    assert notes[0]["is_downbeat"] is True
    assert notes[0]["measure"] == 1
    assert notes[1]["duration"] == "eighth"
    assert notes[1]["is_downbeat"] is False
    assert notes[2]["duration"] == "quarter"
    assert notes[2]["measure"] == 1
    assert notes[3]["duration"] == "dotted_half"
    assert notes[3]["measure"] == 2
    assert notes[3]["is_downbeat"] is True


def test_harmonizer_pipeline_with_34_meter():
    harmonizer = Harmonizer()
    melody = [
        {"pitch": 64, "duration": "quarter"},
        {"pitch": 65, "duration": "quarter"},
        {"pitch": 67, "duration": "quarter"},
        {"pitch": 64, "duration": "dotted_half"},
    ]
    res = harmonizer.harmonize(melody=melody, key="C Major", time_signature="3/4")
    assert res.is_success is True
    assert len(res.solutions) > 0
    best = res.best_solution
    assert best.time_signature == "3/4"
    xml_str = best.to_musicxml()
    assert "<beats>3</beats>" in xml_str
    assert "<beat-type>4</beat-type>" in xml_str
    assert "<dot/>" in xml_str


def test_api_harmonize_and_grade_with_34():
    payload = {
        "melody": [
            {"pitch": 64, "duration": "dotted_quarter"},
            {"pitch": 65, "duration": "eighth"},
            {"pitch": 67, "duration": "quarter"},
            {"pitch": 64, "duration": "dotted_half"},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "3/4",
    }
    r = client.post("/api/harmonize", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["is_success"] is True
    cand = data["candidates"][0]
    assert cand["time_signature"] == "3/4"
    assert "<beats>3</beats>" in cand["musicxml"]
    assert "<dot/>" in cand["musicxml"]

    # Test grader with time_signature
    grade_payload = {
        "voicings": cand["voicings"],
        "key": {"tonic": "C", "mode": "Major"},
        "chords": cand["chords"],
        "time_signature": "3/4",
        "durations": cand["durations"],
    }
    r_grade = client.post("/api/grade", json=grade_payload)
    assert r_grade.status_code == 200
    g_data = r_grade.json()
    assert "report" in g_data
    assert "<beats>3</beats>" in g_data["musicxml"]
