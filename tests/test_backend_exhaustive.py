"""
Exhaustive test suite for Backend Importers, Exporters, Grader, and REST API.
Verifies classical harmony validation, pedagogical diagnostics, MusicXML/MIDI compliance,
and REST endpoints under Moscow Conservatory (Brigade) standards.
"""

from __future__ import annotations

import base64
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import mido
import pytest
from fastapi.testclient import TestClient

from backend.api import router
from backend.exporters import build_colored_musicxml, generate_midi_bytes
from backend.grader import grade_satb_solution
from backend.importers import (
    midi_to_note_name,
    parse_midi_file,
    parse_musicxml_content,
    parse_text_melody,
)
from backend.main import app
from src.harmony.core.types import Chord, Key, TimeSignature, Voicing
from src.harmony.export.midi import export_to_midi
from src.harmony.export.musicxml import export_to_musicxml

client = TestClient(app)


# ============================================================================
# 1. Grader ("Консерваторский инспектор") Tests
# ============================================================================

def test_grader_clean_progression():
    """Valid classical T -> S -> D -> T progression in C Major must pass without errors."""
    voicings = [
        Voicing(64, 60, 55, 48),  # T: C-E-G-C (soprano E4, alto C4, tenor G3, bass C3)
        Voicing(65, 60, 57, 41),  # S: F-A-C-F (soprano F4, alto C4, tenor A3, bass F2)
        Voicing(62, 59, 55, 43),  # D: G-B-D-G (soprano D4, alto B3, tenor G3, bass G2) - contrary motion!
        Voicing(64, 60, 55, 48),  # T: C-E-G-C (soprano E4, alto C4, tenor G3, bass C3)
    ]
    chords = ["T", "S", "D", "T"]
    rep = grade_satb_solution(voicings, key="C Major", chords=chords)

    assert rep.is_valid is True
    assert rep.hard_violations_count == 0
    assert rep.total_violations == 0
    assert rep.problem_measures == []
    assert "5 (Отлично" in rep.grade
    assert "Безупречное голосоведение" in rep.summary_verdict


def test_grader_parallel_fifths_exact_diagnostics():
    """
    Parallel fifths between Soprano and Bass:
    C-E-G-C -> D-F-A-D (parallel fifths S-B: 67-48=19 -> 69-50=19).
    Must report exact Russian message, measure 1, and involved voices ['сопрано', 'бас'].
    """
    voicings = [
        Voicing(67, 64, 60, 48),  # Soprano G4, Bass C3 (interval = 19 semitones -> pure 5th + octave)
        Voicing(69, 65, 62, 50),  # Soprano A4, Bass D3 (interval = 19 semitones -> pure 5th + octave)
    ]
    rep = grade_satb_solution(voicings, key="C Major")

    assert rep.is_valid is False
    assert rep.hard_violations_count > 0
    assert 1 in rep.problem_measures

    p5_violations = [v for v in rep.violations if v["rule_id"] == "PARALLEL_FIFTHS"]
    assert len(p5_violations) >= 1

    # Find the specific Soprano-Bass parallel fifth violation
    sb_p5 = next((v for v in p5_violations if "сопрано" in v["voices"] and "бас" in v["voices"]), None)
    assert sb_p5 is not None, f"Expected Soprano-Bass parallel fifth, got: {p5_violations}"
    assert sb_p5["measure"] == 1
    assert sb_p5["chord_index"] == 2
    assert "Параллельные квинты между сопрано и бас (G4-C3 → A4-D3)" in sb_p5["message_ru"]
    assert "сопрано" in sb_p5["voices"]
    assert "бас" in sb_p5["voices"]
    assert any("сопрано: G4 -> A4" in n for n in sb_p5["notes"])
    assert any("бас: C3 -> D3" in n for n in sb_p5["notes"])


def test_grader_forbidden_d_to_k64():
    """
    Progression D -> K64 is a forbidden functional syntax regression.
    Must report SYNTAX_NO_D_TO_K64 with exact Russian message and measure 1.
    """
    voicings = [
        Voicing(62, 59, 55, 43),  # D: G-B-D
        Voicing(64, 60, 55, 43),  # K64: C-E-G over bass G
    ]
    chords = ["D", "K64"]
    rep = grade_satb_solution(voicings, key="C Major", chords=chords)

    assert rep.is_valid is False
    d_k64_viols = [v for v in rep.violations if v["rule_id"] == "SYNTAX_NO_D_TO_K64"]
    assert len(d_k64_viols) == 1
    v = d_k64_viols[0]
    assert v["measure"] == 1
    assert v["chord_index"] == 2
    assert v["message_ru"] == "Такт 1: Запрещенный переход из доминанты в кадансовый квартсекстаккорд (D -> K64)"


def test_grader_weak_beat_k64():
    """
    Cadential K64 must be placed on a downbeat (strong or relatively strong beat).
    Here K64 is placed on beat 2 in 4/4 meter (weak beat).
    Must report CADENCE_K64_STRONG_BEAT with exact Russian message and measure 1.
    """
    voicings = [
        Voicing(64, 60, 55, 48),  # T (beat 1, strong)
        Voicing(64, 60, 55, 43),  # K64 (beat 2, weak!)
        Voicing(62, 59, 55, 43),  # D (beat 3)
        Voicing(60, 60, 55, 48),  # T (measure 2, beat 1)
    ]
    chords = ["T", "K64", "D", "T"]
    durations = ["quarter", "quarter", "half", "whole"]
    rep = grade_satb_solution(
        voicings,
        key="C Major",
        chords=chords,
        durations=durations,
        time_signature="4/4",
    )

    assert rep.is_valid is False
    k64_db_viols = [v for v in rep.violations if v["rule_id"] == "CADENCE_K64_STRONG_BEAT"]
    assert len(k64_db_viols) == 1
    v = k64_db_viols[0]
    assert v["measure"] == 1
    assert v["chord_index"] == 2
    assert v["message_ru"] == "Такт 1: Каденционный K64 обязан стоять на сильной доле относительно последующей доминанты"


def test_grader_bad_doubling_third_in_main_triad():
    """
    In root-position main triads (T, S, D), doubling the third is forbidden.
    In C Major T, doubling E4 in Soprano and Alto must trigger DOUBLING_MAIN_TRIAD_ROOT
    with exact Russian message and voices ['сопрано', 'альт'].
    """
    voicings = [
        Voicing(64, 64, 55, 48),  # Soprano E4, Alto E4 (third doubled), Tenor G3, Bass C3
    ]
    chords = ["T"]
    rep = grade_satb_solution(voicings, key="C Major", chords=chords)

    assert rep.is_valid is False
    doub_viols = [v for v in rep.violations if v["rule_id"] == "DOUBLING_MAIN_TRIAD_ROOT"]
    assert len(doub_viols) >= 1

    third_doub = next(
        (v for v in doub_viols if "удвоена терция вместо примы" in v["message_ru"]),
        None,
    )
    assert third_doub is not None
    assert third_doub["measure"] == 1
    assert third_doub["chord_index"] == 1
    assert "сопрано" in third_doub["voices"]
    assert "альт" in third_doub["voices"]
    assert "Такт 1: Недопустимое удвоение в главном трезвучии (удвоена терция вместо примы)" in third_doub["message_ru"]


def test_grader_bad_doubling_k64():
    """In K64, the bass note (scale degree 5) must be strictly doubled."""
    # Bass is G2 (43), but voices are E4, C4, E4 (third doubled instead of bass)
    voicings = [
        Voicing(64, 60, 64, 43),
    ]
    chords = ["K64"]
    rep = grade_satb_solution(voicings, key="C Major", chords=chords)

    assert rep.is_valid is False
    k64_doub = next((v for v in rep.violations if v["rule_id"] == "DOUBLING_K64_BASS_ONLY"), None)
    assert k64_doub is not None
    assert "Удвоена терция в квартсекстаккорде K64 (в K64 удваивается строго бас/квинта)" in k64_doub["message_ru"]


def test_grader_deceptive_cadence_bad_doubling():
    """In deceptive cadence (D -> VI), the third of VI (tonic degree 1) must strictly be doubled."""
    # In C Major: D (G-B-D-G) -> VI (A-C-E-A, doubled root A instead of third C)
    voicings = [
        Voicing(62, 59, 55, 43),  # D: Soprano D4, Alto B3, Tenor G3, Bass G2
        Voicing(69, 64, 57, 45),  # VI: Soprano A4, Alto E4, Tenor A3, Bass A2 (Root A tripled, Third C missing!)
    ]
    chords = ["D", "VI"]
    rep = grade_satb_solution(voicings, key="C Major", chords=chords)

    assert rep.is_valid is False
    vi_doub = next((v for v in rep.violations if v["rule_id"] == "DOUBLING_DECEPTIVE_VI_THIRD"), None)
    assert vi_doub is not None
    assert "В трезвучии VI ступени при прерванном обороте (D -> VI) обязана удваиваться терция" in vi_doub["message_ru"]


def test_grader_metric_measures_and_downbeats_multi_measure():
    """
    Tests measure calculation in 3/4 meter:
    3 quarter notes per measure.
    Measure 1: chords 1, 2, 3 (quarters)
    Measure 2: chords 4, 5, 6 (quarters)
    Measure 3: chords 7, 8 (chords 7->8 has parallel fifths).
    Verify that the violation reports measure 3, not measure 1 or 2!
    """
    voicings = [
        # Measure 1
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
        Voicing(64, 60, 55, 48),
        # Measure 2
        Voicing(65, 60, 57, 41),
        Voicing(67, 59, 55, 43),
        Voicing(64, 60, 55, 48),
        # Measure 3: Chords 7 and 8 have parallel fifths
        Voicing(67, 64, 60, 48),  # Chord 7 (G4 / C3)
        Voicing(69, 65, 62, 50),  # Chord 8 (A4 / D3)
    ]
    durations = ["quarter"] * len(voicings)
    rep = grade_satb_solution(
        voicings,
        key="C Major",
        durations=durations,
        time_signature="3/4",
    )

    assert rep.is_valid is False
    assert 3 in rep.problem_measures
    p5_viols = [v for v in rep.violations if v["rule_id"] == "PARALLEL_FIFTHS"]
    assert any(v["measure"] == 3 and v["chord_index"] == 8 for v in p5_viols)


def test_grader_empty_score():
    """Empty score must return invalid GraderReport with EMPTY_SCORE rule."""
    rep = grade_satb_solution([])
    assert rep.is_valid is False
    assert rep.total_violations == 1
    assert rep.violations[0]["rule_id"] == "EMPTY_SCORE"
    assert rep.grade == "2 (Не зачтено)"


# ============================================================================
# 2. Exporters & Importers Tests
# ============================================================================

@pytest.mark.parametrize("meter", ["3/4", "4/4", "6/8"])
@pytest.mark.parametrize(
    "dur_name,dur_list",
    [
        ("whole", ["whole", "whole"]),
        ("dotted_half", ["dotted_half", "dotted_half"]),
        ("half", ["half", "half", "half", "half"]),
        ("dotted_quarter", ["dotted_quarter", "dotted_quarter", "dotted_quarter", "dotted_quarter"]),
        ("quarter", ["quarter", "quarter", "quarter", "quarter"]),
        ("dotted_eighth", ["dotted_eighth", "dotted_eighth", "dotted_eighth", "dotted_eighth"]),
        ("eighth", ["eighth", "eighth", "eighth", "eighth"]),
    ],
)
def test_musicxml_all_meters_and_durations_validity(meter: str, dur_name: str, dur_list: list[str]):
    """
    Verifies that MusicXML export generates structurally valid MusicXML 3.1
    for all combinations of meters (3/4, 4/4, 6/8) and note durations,
    including dotted half, dotted quarter, and dotted eighth.
    """
    voicings = [Voicing(64, 60, 55, 48) for _ in dur_list]
    chords = ["T"] * len(dur_list)

    # 1. Standard export
    raw_xml = export_to_musicxml(
        voicings=voicings,
        chords=chords,
        key="C Major",
        durations=dur_list,
        time_signature=meter,
    )
    root = ET.fromstring(raw_xml)
    assert root.tag == "score-partwise"
    assert root.attrib.get("version") == "3.1"

    # Verify time signature element in measure 1
    m1 = root.find(".//measure[@number='1']")
    assert m1 is not None
    ts_beats = m1.find(".//time/beats")
    ts_type = m1.find(".//time/beat-type")
    assert ts_beats is not None and ts_type is not None

    expected_beats, expected_type = meter.split("/")
    assert ts_beats.text == expected_beats
    assert ts_type.text == expected_type

    # Verify note types and dots
    notes = root.findall(".//note")
    assert len(notes) > 0
    if "dotted" in dur_name:
        dot_elems = root.findall(".//dot")
        assert len(dot_elems) > 0, f"Expected <dot/> elements for {dur_name}"

    # 2. Colored MusicXML export
    colored_xml = build_colored_musicxml(
        voicings=voicings,
        chords=chords,
        key="C Major",
        durations=dur_list,
        time_signature=meter,
    )
    col_root = ET.fromstring(colored_xml)
    assert col_root.tag == "score-partwise"

    # Check colors per voice
    v1_notes = [n for n in col_root.findall(".//note") if n.find("voice") is not None and n.find("voice").text == "1"]
    v4_notes = [n for n in col_root.findall(".//note") if n.find("voice") is not None and n.find("voice").text == "4"]
    assert any(n.attrib.get("color") == "#2563eb" for n in v1_notes)  # Soprano blue
    assert any(n.attrib.get("color") == "#dc2626" for n in v4_notes)  # Bass red

    # Check that lyric was transferred under voice 4 (Bass)
    bass_lyrics = [n.find(".//lyric/text").text for n in v4_notes if n.find(".//lyric/text") is not None]
    assert "T" in bass_lyrics


def test_midi_export_inspection():
    """
    Verifies MIDI export generates valid SMF Format 1 with:
    - ticks_per_beat = 480
    - Exact Time Signature Meta Event
    - Set Tempo Meta Event matching BPM
    - Note-on and note-off events for all 4 voices (one track per voice)
    """
    voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
        Voicing(64, 60, 55, 48),
    ]
    durations = ["half", "quarter", "quarter"]
    bpm = 100

    midi_bytes = generate_midi_bytes(
        voicings=voicings,
        bpm=bpm,
        durations=durations,
        time_signature="3/4",
    )
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))

    assert mid.type == 1
    assert mid.ticks_per_beat == 480
    assert len(mid.tracks) == 4

    # Check meta events in the first (conductor/global) track
    track = mid.tracks[0]
    time_sigs = [msg for msg in track if msg.type == "time_signature"]
    tempos = [msg for msg in track if msg.type == "set_tempo"]

    assert len(time_sigs) >= 1
    assert time_sigs[0].numerator == 3
    assert time_sigs[0].denominator == 4

    assert len(tempos) >= 1
    expected_tempo = int(60_000_000 / bpm)
    assert abs(tempos[0].tempo - expected_tempo) <= 1

    # Check note on / note off across all voice tracks
    note_ons = [msg for t in mid.tracks for msg in t if msg.type == "note_on" and msg.velocity > 0]
    note_offs = [
        msg for t in mid.tracks for msg in t
        if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)
    ]

    assert len(note_ons) == 3 * 4  # 3 chords * 4 voices
    assert len(note_offs) == 3 * 4


def test_importers_text_melody_exhaustive():
    """
    Verifies parse_text_melody for all input formats:
    - note names with octave ('C4 E4 F4 G4')
    - comma-separated note names ('C4, E4, F4, G4')
    - note names with duration ('C4:dotted_quarter D4:eighth E4:dotted_half')
    - inline meter tags ('[3/4] C4:quarter E4:quarter G4:quarter')
    - leading meter ('3/4 C4:quarter E4:quarter G4:quarter')
    - scale degrees relative to key ('1 3 4 5')
    - comma-separated MIDI pitches ('60, 64, 65, 67')
    """
    # 1. Note names
    res1 = parse_text_melody("C4 E4 F4 G4")
    assert [n["pitch"] for n in res1] == [60, 64, 65, 67]
    assert [n["name"] for n in res1] == ["C4", "E4", "F4", "G4"]

    # 2. Comma separated
    res2 = parse_text_melody("C4, E4, F4, G4")
    assert [n["pitch"] for n in res2] == [60, 64, 65, 67]

    # 3. Dotted durations
    res3 = parse_text_melody("C4:dotted_quarter D4:eighth E4:dotted_half")
    assert [n["duration"] for n in res3] == ["dotted_quarter", "eighth", "dotted_half"]

    # 4. Inline meter [3/4]
    res4 = parse_text_melody("[3/4] C4:quarter E4:quarter G4:quarter")
    assert res4[0]["time_signature"] == "3/4"
    assert res4[0]["is_downbeat"] is True
    assert res4[1]["is_downbeat"] is False

    # 5. Leading meter 3/4
    res5 = parse_text_melody("3/4 C4:quarter E4:quarter G4:quarter")
    assert res5[0]["time_signature"] == "3/4"

    # 6. Scale degrees in G Major (1=G4/67, 3=B4/71, 5=D4/62 in octave 4)
    res6 = parse_text_melody("1 3 5", key_tonic="G", key_mode="Major")
    assert [n["pitch"] for n in res6] == [67, 71, 62]

    # 7. MIDI pitch numbers
    res7 = parse_text_melody("60, 64, 65, 67")
    assert [n["pitch"] for n in res7] == [60, 64, 65, 67]


def test_importers_musicxml_roundtrip():
    """
    Roundtrip test:
    SATB voicings -> MusicXML export -> parse_musicxml_content.
    Verifies that soprano melody, SATB voicings, key, and chords are accurately recovered.
    """
    original_voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
        Voicing(67, 59, 55, 43),
        Voicing(64, 60, 55, 48),
    ]
    original_chords = ["T", "S", "D", "T"]

    xml_text = build_colored_musicxml(
        voicings=original_voicings,
        chords=original_chords,
        key="C Major",
        time_signature="4/4",
    )
    parsed = parse_musicxml_content(xml_text)

    # Soprano melody pitches
    assert [n["pitch"] for n in parsed["soprano_melody"]] == [64, 65, 67, 64]

    # SATB voicings
    satb = parsed["satb_voicings"]
    assert len(satb) == 4
    for i in range(4):
        assert satb[i]["soprano"] == original_voicings[i].s
        assert satb[i]["alto"] == original_voicings[i].a
        assert satb[i]["tenor"] == original_voicings[i].t
        assert satb[i]["bass"] == original_voicings[i].b

    # Chords
    assert parsed["chords"] == original_chords
    assert parsed["detected_key"]["tonic"] == "C"
    assert parsed["detected_key"]["mode"] == "Major"


def test_importers_midi_roundtrip():
    """
    Roundtrip test:
    SATB voicings -> MIDI export -> parse_midi_file.
    Verifies that soprano melody and SATB voicings are recovered with correct pitches.
    """
    original_voicings = [
        Voicing(64, 60, 55, 48),
        Voicing(65, 60, 57, 41),
        Voicing(67, 59, 55, 43),
        Voicing(64, 60, 55, 48),
    ]
    midi_data = generate_midi_bytes(original_voicings, time_signature="4/4")
    parsed = parse_midi_file(midi_data)

    assert [n["pitch"] for n in parsed["soprano_melody"]] == [64, 65, 67, 64]
    assert len(parsed["satb_voicings"]) == 4
    for i in range(4):
        assert parsed["satb_voicings"][i]["soprano"] == original_voicings[i].s
        assert parsed["satb_voicings"][i]["alto"] == original_voicings[i].a
        assert parsed["satb_voicings"][i]["tenor"] == original_voicings[i].t
        assert parsed["satb_voicings"][i]["bass"] == original_voicings[i].b


# ============================================================================
# 3. REST API Gateway Tests
# ============================================================================

def test_api_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "brigade-harmony-web"


def test_api_keys_endpoint():
    res = client.get("/api/keys")
    assert res.status_code == 200
    keys = res.json()
    assert len(keys) == 24
    assert any(k["tonic"] == "C" and k["mode"] == "Major" for k in keys)
    assert any("C-dur" in k["name"] for k in keys)


def test_api_detect_key_endpoint():
    # C Major melody: E4, F4, G4, D4, C4
    melody = [{"pitch": 64}, {"pitch": 65}, {"pitch": 67}, {"pitch": 62}, {"pitch": 60}]
    res = client.post("/api/detect-key", json=melody)
    assert res.status_code == 200
    det = res.json()
    assert det["tonic"] == "C"
    assert det["mode"] == "Major"


def test_api_parse_text_endpoint():
    payload = {
        "text": "C4:quarter E4:quarter F4:quarter G4:quarter",
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
    }
    res = client.post("/api/parse-text", json=payload)
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 4
    assert notes[0]["name"] == "C4"
    assert notes[0]["duration"] == "quarter"


def test_api_harmonize_endpoint_success():
    payload = {
        "melody": [
            {"pitch": 64, "is_downbeat": True, "duration": "half"},
            {"pitch": 65, "is_downbeat": False, "duration": "half"},
            {"pitch": 67, "is_downbeat": True, "duration": "half"},
            {"pitch": 62, "is_downbeat": False, "duration": "half"},
            {"pitch": 60, "is_downbeat": True, "duration": "half"},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "allow_extended_ranges": False,
        "allow_secondary_dominants": True,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert len(data["candidates"]) >= 1
    cand = data["candidates"][0]
    assert "musicxml" in cand
    assert "ascii_score" in cand
    assert len(cand["voicings"]) == 5


def test_api_harmonize_empty_melody_validation():
    payload = {
        "melody": [],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 400


def test_api_grade_endpoint_clean_and_violations():
    # 1. Clean progression
    clean_payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48},
            {"soprano": 65, "alto": 60, "tenor": 57, "bass": 41},
            {"soprano": 62, "alto": 59, "tenor": 55, "bass": 43},
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "chords": ["T", "S", "D", "T"],
    }
    res_clean = client.post("/api/grade", json=clean_payload)
    assert res_clean.status_code == 200
    rep_clean = res_clean.json()["report"]
    assert rep_clean["is_valid"] is True
    assert rep_clean["hard_violations_count"] == 0

    # 2. Progression with parallel fifths
    bad_payload = {
        "voicings": [
            {"soprano": 67, "alto": 64, "tenor": 60, "bass": 48},
            {"soprano": 69, "alto": 65, "tenor": 62, "bass": 50},
        ],
        "chords": ["T", "II"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res_bad = client.post("/api/grade", json=bad_payload)
    assert res_bad.status_code == 200
    rep_bad = res_bad.json()["report"]
    assert rep_bad["is_valid"] is False
    assert rep_bad["hard_violations_count"] > 0
    assert any("Параллельные квинты" in v["message_ru"] for v in rep_bad["violations"])


def test_api_import_file_multipart_and_json():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <score-partwise version="3.1">
      <part id="P1">
        <measure number="1">
          <attributes>
            <divisions>4</divisions>
            <key><fifths>0</fifths><mode>major</mode></key>
            <time><beats>4</beats><beat-type>4</beat-type></time>
            <staves>2</staves>
          </attributes>
          <note>
            <pitch><step>C</step><octave>4</octave></pitch>
            <duration>8</duration>
            <voice>1</voice>
            <type>half</type>
            <staff>1</staff>
          </note>
        </measure>
      </part>
    </score-partwise>"""

    # 1. Multipart form file upload
    res_form = client.post(
        "/api/import-file",
        files={"file": ("score.musicxml", xml_content.encode("utf-8"), "application/xml")},
    )
    assert res_form.status_code == 200
    data_form = res_form.json()
    assert data_form["format"] == "musicxml"
    assert len(data_form["soprano_melody"]) == 1
    assert data_form["soprano_melody"][0]["pitch"] == 60

    # 2. JSON upload with xml_content
    res_json_xml = client.post(
        "/api/import-file",
        json={"filename": "score.musicxml", "xml_content": xml_content},
    )
    assert res_json_xml.status_code == 200
    data_json_xml = res_json_xml.json()
    assert data_json_xml["format"] == "musicxml"
    assert data_json_xml["soprano_melody"][0]["pitch"] == 60

    # 3. JSON upload with base64 content
    b64_content = base64.b64encode(xml_content.encode("utf-8")).decode("ascii")
    res_b64 = client.post(
        "/api/import-file",
        json={"filename": "score.musicxml", "content_base64": b64_content},
    )
    assert res_b64.status_code == 200
    data_b64 = res_b64.json()
    assert data_b64["format"] == "musicxml"

    # 4. Invalid file extension
    res_invalid = client.post(
        "/api/import-file",
        json={"filename": "score.pdf", "xml_content": "dummy"},
    )
    assert res_invalid.status_code == 400


def test_api_export_midi_and_musicxml():
    voicings = [
        {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48},
        {"soprano": 65, "alto": 60, "tenor": 57, "bass": 41},
    ]

    # 1. Export MIDI
    midi_req = {
        "voicings": voicings,
        "bpm": 80,
        "time_signature": "4/4",
    }
    res_midi = client.post("/api/export/midi", json=midi_req)
    assert res_midi.status_code == 200
    assert res_midi.headers["content-type"] == "audio/midi"
    assert res_midi.content.startswith(b"MThd")

    # 2. Export MusicXML
    xml_req = {
        "voicings": voicings,
        "chords": ["T", "S"],
        "key": {"tonic": "C", "mode": "Major"},
        "title": "API Test",
        "time_signature": "4/4",
    }
    res_xml = client.post("/api/export/musicxml", json=xml_req)
    assert res_xml.status_code == 200
    assert "application/vnd.recordare.musicxml+xml" in res_xml.headers["content-type"]
    assert res_xml.text.startswith("<?xml")
    assert "<work-title>API Test</work-title>" in res_xml.text
