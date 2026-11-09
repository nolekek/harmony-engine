"""
Tests for backend API gateway, importers, grader, and exporters.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.importers import parse_text_melody, parse_musicxml_content, parse_midi_file
from backend.key_detector import detect_key_from_melody
from backend.grader import grade_satb_solution
from src.harmony.core.types import Key, Voicing

client = TestClient(app)


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_api_keys():
    res = client.get("/api/keys")
    assert res.status_code == 200
    keys = res.json()
    assert len(keys) == 24


def test_api_parse_text():
    # Note names
    res = client.post("/api/parse-text", json={"text": "C4 E4 F4 G4", "key": {"tonic": "C", "mode": "Major"}})
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 4
    assert [n["pitch"] for n in notes] == [60, 64, 65, 67]

    # Scale degrees
    res2 = client.post("/api/parse-text", json={"text": "1 3 4 5", "key": {"tonic": "C", "mode": "Major"}})
    assert res2.status_code == 200
    notes2 = res2.json()
    assert [n["pitch"] for n in notes2] == [60, 64, 65, 67]


def test_api_detect_key():
    melody = [{"pitch": 64}, {"pitch": 65}, {"pitch": 67}, {"pitch": 62}, {"pitch": 60}]
    res = client.post("/api/detect-key", json=melody)
    assert res.status_code == 200
    detected = res.json()
    assert detected["tonic"] == "C"
    assert detected["mode"] == "Major"


def test_api_harmonize():
    payload = {
        "melody": [
            {"pitch": 64, "is_downbeat": True, "duration": "half"},
            {"pitch": 65, "is_downbeat": False, "duration": "half"},
            {"pitch": 67, "is_downbeat": True, "duration": "half"},
            {"pitch": 62, "is_downbeat": False, "duration": "half"},
            {"pitch": 60, "is_downbeat": True, "duration": "half"},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "allow_extended_ranges": False,
        "allow_secondary_dominants": True,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert len(data["candidates"]) >= 1
    assert data["latency_ms"] < 1000  # fast latency check
    best = data["candidates"][0]
    assert len(best["chords"]) == 5
    assert len(best["voicings"]) == 5
    assert "color=" in best["musicxml"]
    assert "===" in best["ascii_score"]


def test_api_grade():
    # Submit bad voicings with parallel fifths
    payload = {
        "voicings": [
            {"soprano": 67, "alto": 60, "tenor": 55, "bass": 48},
            {"soprano": 69, "alto": 60, "tenor": 57, "bass": 50},
        ],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 200
    data = res.json()
    rep = data["report"]
    assert rep["is_valid"] is False
    assert rep["hard_violations_count"] > 0
    assert any("Параллельные квинты" in v["message_ru"] for v in rep["violations"])
