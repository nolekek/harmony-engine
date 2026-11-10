"""
Tests for structured API diagnostics under T9-backend.
Verifies failure reporting with exact diagnostic codes and details.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_diagnostics_no_feasible_plan():
    """Melody [72, 71, 69] (C5-B4-A4) has candidate plans, but all are blocked by Viterbi."""
    payload = {
        "melody": [
            {"pitch": 72, "duration": "half"},
            {"pitch": 71, "duration": "half"},
            {"pitch": 69, "duration": "half"},
        ],
        "key": {"tonic": "C", "mode": "Major"},
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is False
    assert data["candidates"] == []
    assert "error" in data and data["error"] is not None
    err = data["error"]
    assert err["code"] == "NO_FEASIBLE_PLAN"
    assert isinstance(err["diagnostics"], list)
    assert len(err["diagnostics"]) > 0
    first_diag = err["diagnostics"][0]
    assert "step" in first_diag
    assert "chord" in first_diag
    assert "blocked" in first_diag
    assert "message" in first_diag


def test_diagnostics_secondary_dominants_disabled():
    """Melody [64,66,67,64,62,60] requires secondary dominants; disallowed flag yields error code."""
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
    assert "error" in data and data["error"] is not None
    err = data["error"]
    assert err["code"] == "SECONDARY_DOMINANTS_DISABLED"
    assert "Без побочных доминант" in err["message"]


def test_diagnostics_success_melody():
    """Successful melody [60,64,67,72] returns is_success=True and error is None."""
    payload = {
        "melody": [
            {"pitch": 60, "duration": "half", "is_downbeat": True},
            {"pitch": 64, "duration": "half", "is_downbeat": False},
            {"pitch": 67, "duration": "half", "is_downbeat": True},
            {"pitch": 72, "duration": "half", "is_downbeat": True},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "max_plans": 50,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    assert len(data["candidates"]) >= 1
    assert data.get("error") is None
