"""
Tests for HarmonizationService comparing direct service invocation with REST API.
Verifies identical contract, ranking, chords, and cost.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.service import HarmonizationService

client = TestClient(app)


def test_service_and_api_identical_successful_melody():
    service = HarmonizationService()
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
        "max_plans": 50,
    }

    # Direct service call
    service_res = service.harmonize(payload)

    # API call
    api_res = client.post("/api/harmonize", json=payload)
    assert api_res.status_code == 200
    api_data = api_res.json()

    assert service_res["is_success"] is True
    assert api_data["is_success"] is True

    # Compare top-1 chords, voicings, cost
    s_best = service_res["best_candidate"]
    a_best = api_data["best_candidate"]

    assert s_best["chords"] == a_best["chords"]
    assert s_best["cost"] == a_best["cost"]
    assert len(service_res["candidates"]) == len(api_data["candidates"])
    assert service_res["error"] is None
    assert api_data["error"] is None


def test_service_and_api_identical_secondary_dominants_disallowed():
    service = HarmonizationService()
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

    service_res = service.harmonize(payload)
    api_res = client.post("/api/harmonize", json=payload)
    assert api_res.status_code == 200
    api_data = api_res.json()

    assert service_res["is_success"] is False
    assert api_data["is_success"] is False
    assert service_res["candidates"] == []
    assert api_data["candidates"] == []
    assert service_res["error"]["code"] == "SECONDARY_DOMINANTS_DISABLED"
    assert api_data["error"]["code"] == "SECONDARY_DOMINANTS_DISABLED"
    assert service_res["error"]["code"] == api_data["error"]["code"]
