"""
Tests for backend API gateway, importers, grader, and exporters.
"""

from fastapi.testclient import TestClient
from backend.main import app

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
        "chords": ["T", "S"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 200
    data = res.json()
    rep = data["report"]
    assert rep["is_valid"] is False
    assert rep["hard_violations_count"] > 0
    assert any("Параллельные квинты" in v["message_ru"] for v in rep["violations"])


def test_api_downbeat_false_preservation():
    # Melody [60, 64, 67, 72] C4 E4 G4 C5, 4/4
    # Note 1 has explicit is_downbeat: False
    melody = [
        {"pitch": 60, "duration": "half", "is_downbeat": True},
        {"pitch": 64, "duration": "half", "is_downbeat": False},
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 72, "duration": "half", "is_downbeat": True},
    ]
    from src.harmony.pipeline import Harmonizer
    h = Harmonizer()
    core_res = h.harmonize(melody, key="C Major", time_signature="4/4", max_plans=50)
    assert core_res.is_success is True

    res = client.post("/api/harmonize", json={
        "melody": melody,
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "max_plans": 50,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    # Compare chords and voicings between API and Harmonizer
    expected_chords = [c.function for c in core_res.solutions[0].chords]
    assert data["candidates"][0]["chords"] == expected_chords
    expected_voicings = [
        {"soprano": v.s, "alto": v.a, "tenor": v.t, "bass": v.b}
        for v in core_res.solutions[0].voicings
    ]
    assert data["candidates"][0]["voicings"] == expected_voicings


def test_api_secondary_dominants_disallowed():
    # Melody [64,66,67,64,62,60] (E F# G E D C), C-dur
    # Without secondary dominants, this melody cannot be harmonized
    # (F# requires DD). When allow_secondary_dominants=False, API must return is_success=False
    # with empty candidates and honest message.
    payload = {
        "melody": [
            {"pitch": 64, "duration": "half"},
            {"pitch": 66, "duration": "half"},
            {"pitch": 67, "duration": "half"},
            {"pitch": 64, "duration": "half"},
            {"pitch": 62, "duration": "half"},
            {"pitch": 60, "duration": "half"},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "allow_secondary_dominants": False,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is False
    assert data["candidates"] == []
    assert data["message"] == "Без побочных доминант невозможно гармонизовать заданную мелодию."

