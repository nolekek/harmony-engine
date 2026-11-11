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


def _all_success_costs(melody_dicts, key="C Major", max_plans=50):
    """Enumerate every generated plan and collect costs of all successful solutions."""
    from src.harmony.core.types import Key as HarmonyKey, TimeSignature, calculate_metric_structure

    h = Harmonizer()
    metric = calculate_metric_structure(
        melody_dicts, default_time_signature=TimeSignature.parse("4/4")
    )
    processed = [
        {"pitch": m["pitch"], "duration": m["duration"], "is_downbeat": m["is_downbeat"]}
        for m in metric
    ]
    parsed_key = HarmonyKey.parse(key)
    plans = h.grammar.generate_plans(melody=processed, key=parsed_key, max_plans=max_plans)
    costs = []
    for plan in plans:
        res = h.solver.solve(melody=processed, chords=plan, key=parsed_key)
        if res.is_success:
            costs.append(round(res.total_cost, 2))
    return sorted(costs)


def test_api_harmonize_honest_top3():
    # Melody [64, 65, 62, 67] (E F D G, half, C-dur, max_plans=50).
    # Honest top-3 must return the three globally cheapest successful plans,
    # not the first three plans that happen to solve.
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
    expected = _all_success_costs(payload["melody"], max_plans=50)[:3]
    assert costs == expected, f"API returned {costs}, global top-3 is {expected}"
    assert costs == sorted(costs)
    assert all(c >= 0 for c in costs), f"costs must be non-negative, got {costs}"


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
    costs = [round(s.cost, 2) for s in res.solutions]
    expected = _all_success_costs(melody, max_plans=50)[:3]
    assert costs == expected, f"pipeline returned {costs}, global top-3 is {expected}"
    assert costs == sorted(costs)
    assert all(c >= 0 for c in costs), f"costs must be non-negative, got {costs}"
