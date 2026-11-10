"""
Tests for honest top-3 candidate selection (T4 / REPORT #4 / BK-04).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api import select_top_candidates
from src.harmony.pipeline import Harmonizer

client = TestClient(app)


def test_select_top_candidates_pure_function():
    # Input with costs [-2, -6, -6, -10, 0]
    solutions = [
        {"id": "c1", "cost": -2.0, "tag": "first_-2"},
        {"id": "c2", "cost": -6.0, "tag": "first_-6"},
        {"id": "c3", "cost": -6.0, "tag": "second_-6"},
        {"id": "c4", "cost": -10.0, "tag": "min_-10"},
        {"id": "c5", "cost": 0.0, "tag": "zero"},
    ]
    top3 = select_top_candidates(solutions, k=3)

    assert len(top3) == 3
    assert [s["cost"] for s in top3] == [-10.0, -6.0, -6.0]
    # Verify stability: c2 ("first_-6") must come before c3 ("second_-6")
    assert top3[1]["tag"] == "first_-6"
    assert top3[2]["tag"] == "second_-6"
    # Verify ranks are updated
    assert [s["rank"] for s in top3] == [1, 2, 3]


def test_select_top_candidates_edge_cases():
    assert select_top_candidates([], k=3) == []
    single = [{"cost": 5.0}]
    res = select_top_candidates(single, k=3)
    assert len(res) == 1
    assert res[0]["cost"] == 5.0
    assert res[0]["rank"] == 1


def test_api_harmonize_honest_top3():
    # Melody [64, 65, 62, 67] (E F D G, half, C-dur, max_plans=50)
    # Total successful plans are 5 (costs: -6.0, -1.0, 4.0, 6.0, 8.0).
    # With honest top-3 selection, the candidates must be [-6.0, -1.0, 4.0].
    # Early break previously returned [-6.0, 4.0, 6.0], missing the -1.0 plan.
    payload = {
        "melody": [
            {"pitch": 64, "duration": "half", "is_downbeat": True},
            {"pitch": 65, "duration": "half", "is_downbeat": False},
            {"pitch": 62, "duration": "half", "is_downbeat": True},
            {"pitch": 67, "duration": "half", "is_downbeat": False},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "max_plans": 50,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["is_success"] is True
    candidates = data["candidates"]
    assert len(candidates) == 3

    costs = [c["cost"] for c in candidates]
    # First candidate has minimal cost
    assert costs[0] == -6.0
    # Second candidate must be -1.0, NOT 4.0
    assert costs[1] == -1.0
    assert costs[2] == 4.0
    assert costs == sorted(costs)


def test_pipeline_honest_top3():
    h = Harmonizer()
    melody = [
        {"pitch": 64, "duration": "half", "is_downbeat": True},
        {"pitch": 65, "duration": "half", "is_downbeat": False},
        {"pitch": 62, "duration": "half", "is_downbeat": True},
        {"pitch": 67, "duration": "half", "is_downbeat": False},
    ]
    res = h.harmonize(melody, key="C Major", max_plans=50)
    assert res.is_success is True
    assert len(res.solutions) == 3
    costs = [s.cost for s in res.solutions]
    assert costs[0] == -6.0
    assert costs[1] == -1.0
    assert costs[2] == 4.0
