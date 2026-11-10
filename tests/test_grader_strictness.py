"""
Tests for student grader strictness and validation contract under T7.
Verifies mandatory chords parameter, length matching, function whitelist, and RuleEngine enforcement.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_grade_missing_chords():
    """POST /api/grade without chords must return 422 Unprocessable Entity."""
    payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}
        ],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 422


def test_grade_length_mismatch():
    """Mismatch between voicings and chords counts must return 422."""
    payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48},
            {"soprano": 65, "alto": 60, "tenor": 57, "bass": 45},
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48},
        ],
        "chords": ["T"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 422


def test_grade_unknown_chord_function():
    """Invalid chord function like 'V' (Roman numeral 5) must return 422."""
    payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}
        ],
        "chords": ["V"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 422
    assert "Неизвестная функция аккорда" in str(res.json())


def test_grade_bad_unison_voicing():
    """Voicing with voice unison [(64,60,48,48)] must yield hard violations and not start with '5'."""
    payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 48, "bass": 48}
        ],
        "chords": ["T"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 200
    data = res.json()
    rep = data["report"]
    assert rep["hard_violations_count"] >= 1
    assert not rep["grade"].startswith("5")


def test_grade_clean_voicing():
    """Clean textbook voicing [(64,60,55,48)] in C-dur with 'T' must yield zero hard violations and grade 5 or 4."""
    payload = {
        "voicings": [
            {"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}
        ],
        "chords": ["T"],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/grade", json=payload)
    assert res.status_code == 200
    data = res.json()
    rep = data["report"]
    assert rep["hard_violations_count"] == 0
    assert rep["grade"].startswith("5") or rep["grade"].startswith("4")
