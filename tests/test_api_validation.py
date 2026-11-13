"""
Tests for CORS whitelist and API schema validation (T12 / REPORT #37, #38, #61, #62 / BK-08, BK-09).
"""

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_cors_origin_whitelist():
    # Disallowed origin should NOT receive Access-Control-Allow-Origin header
    headers = {
        "Origin": "http://evil.com",
    }
    res = client.get("/api/health", headers=headers)
    assert res.status_code == 200
    assert "access-control-allow-origin" not in res.headers or res.headers["access-control-allow-origin"] != "http://evil.com"
    assert res.headers.get("access-control-allow-origin") != "*"

    # Allowed origins
    for allowed in ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5173", "http://127.0.0.1:5173"]:
        res_allowed = client.get("/api/health", headers={"Origin": allowed})
        assert res_allowed.headers.get("access-control-allow-origin") == allowed


def test_validation_invalid_key():
    # Invalid tonic and alien mode -> 422
    payload = {
        "melody": [{"pitch": 60, "duration": "half"}],
        "key": {"tonic": "Z#", "mode": "AlienMode"},
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 422

    # Invalid tonic alone
    res_tonic = client.post("/api/harmonize", json={
        "melody": [{"pitch": 60}],
        "key": {"tonic": "H#?"},
    })
    assert res_tonic.status_code == 422

    # Invalid mode alone
    res_mode = client.post("/api/harmonize", json={
        "melody": [{"pitch": 60}],
        "key": {"mode": "AlienMode"},
    })
    assert res_mode.status_code == 422


def test_validation_invalid_max_plans():
    # max_plans = 0 -> 422
    res_zero = client.post("/api/harmonize", json={
        "melody": [{"pitch": 60}],
        "max_plans": 0,
    })
    assert res_zero.status_code == 422

    # max_plans = -10 -> 422
    res_neg = client.post("/api/harmonize", json={
        "melody": [{"pitch": 60}],
        "max_plans": -10,
    })
    assert res_neg.status_code == 422

    # max_plans = 101 -> 422 (limit is 100)
    res_overflow = client.post("/api/harmonize", json={
        "melody": [{"pitch": 60}],
        "max_plans": 101,
    })
    assert res_overflow.status_code == 422


def test_validation_melody_length():
    # 1000 notes -> 422 (max_length = 128)
    long_melody = [{"pitch": 60, "duration": "quarter"} for _ in range(1000)]
    res = client.post("/api/harmonize", json={"melody": long_melody})
    assert res.status_code == 422


def test_validation_pitch_range():
    # Pitch 300 -> 422
    res_high = client.post("/api/harmonize", json={
        "melody": [{"pitch": 300}],
    })
    assert res_high.status_code == 422

    # Pitch -5 -> 422
    res_low = client.post("/api/harmonize", json={
        "melody": [{"pitch": -5}],
    })
    assert res_low.status_code == 422


def test_validation_valid_request():
    payload = {
        "melody": [
            {"pitch": 64, "duration": "half", "is_downbeat": True},
            {"pitch": 65, "duration": "half", "is_downbeat": False},
            {"pitch": 62, "duration": "half", "is_downbeat": True},
            {"pitch": 60, "duration": "half", "is_downbeat": False},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "max_plans": 50,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "is_success" in data
