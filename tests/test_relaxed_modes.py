"""
Tests for optional relaxed modes in SATB harmonization:
1. allow_adjacent_unisons: enables adjacent voice unisons (S==A, A==T, T==B).
2. relax_hard_gates: soft-penalizes hard gates (+10000.0) instead of pruning.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.harmony.core.types import Voicing, Chord, Key
from src.harmony.rules.spacing import validate_spacing, check_voice_unison
from src.harmony.solver.state_generator import generate_candidate_voicings, clear_candidate_cache
from src.harmony.solver.viterbi import ViterbiSolver, clear_solver_cache
from src.harmony.pipeline import Harmonizer
from backend.service import HarmonizationService, clear_service_cache
from backend.api import router


@pytest.fixture(autouse=True)
def flush_all_caches():
    clear_candidate_cache()
    clear_solver_cache()
    clear_service_cache()
    yield
    clear_candidate_cache()
    clear_solver_cache()
    clear_service_cache()


@pytest.fixture
def api_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_spacing_allow_unisons_parameter():
    """validate_spacing with allow_unisons=True suppresses only VOICE_UNISON."""
    unison_voicing = Voicing(soprano=67, alto=64, tenor=60, bass=60)  # T==B == 60
    viols_strict = validate_spacing(unison_voicing, allow_unisons=False)
    assert any(v.rule_id == "VOICE_UNISON" for v in viols_strict)

    viols_relaxed = validate_spacing(unison_voicing, allow_unisons=True)
    assert not any(v.rule_id == "VOICE_UNISON" for v in viols_relaxed)

    # Other violations (e.g. crossing S < A) must still be detected
    crossing_voicing = Voicing(soprano=60, alto=64, tenor=55, bass=48)
    viols_crossing = validate_spacing(crossing_voicing, allow_unisons=True)
    assert any(v.rule_id == "VOICE_CROSSING" for v in viols_crossing)


def test_state_generator_allow_adjacent_unisons():
    """generate_candidate_voicings produces adjacent unisons only when enabled."""
    chord = Chord("T6")
    key = Key("C", "Major")
    # For soprano pitch 64 (E4), T6 has 0 strict candidates because T==B would be required
    cands_strict = generate_candidate_voicings(64, chord, key=key, allow_adjacent_unisons=False)
    assert len(cands_strict) == 0

    cands_unison = generate_candidate_voicings(64, chord, key=key, allow_adjacent_unisons=True)
    assert len(cands_unison) > 0
    assert any(v.alto == v.tenor or v.tenor == v.bass or v.soprano == v.alto for v in cands_unison)


def test_default_control_melody_identical():
    """Default harmonization of control melody [64,65,67,64,62,60] must match baseline exactly."""
    melody = [64, 65, 67, 64, 62, 60]
    h = Harmonizer()
    res = h.harmonize(melody, key="C Major")
    assert res.is_success is True
    best = res.best_solution
    assert best is not None

    expected_chords = ["T", "S6", "D6", "T", "D", "T"]
    expected_cost = 23.4
    chords = [c.function for c in best.chords]
    assert chords == expected_chords
    assert round(best.cost, 2) == expected_cost
    assert best.had_relaxed_violations is False
    assert best.relaxed_rule_ids == []


def test_allow_adjacent_unisons_rescues_melody():
    """
    allow_adjacent_unisons=True rescues a melody where strict mode fails,
    and the resulting solution contains at least one adjacent voice unison.
    """
    h = Harmonizer()
    melody = [67, 74]

    # Strict mode fails
    res_strict = h.harmonize(melody, key="C Major", allow_adjacent_unisons=False)
    assert res_strict.is_success is False

    # Relaxed unisons mode succeeds
    res_unison = h.harmonize(melody, key="C Major", allow_adjacent_unisons=True)
    assert res_unison.is_success is True
    best = res_unison.best_solution
    assert best is not None

    # Must contain at least one adjacent unison (S==A or A==T or T==B)
    has_unison = any(
        (v.soprano == v.alto) or (v.alto == v.tenor) or (v.tenor == v.bass)
        for v in best.voicings
    )
    assert has_unison is True


def test_viterbi_unisons_with_chords():
    """ViterbiSolver with allow_adjacent_unisons produces valid SATB trajectory for T6 -> D."""
    solver = ViterbiSolver()
    res_strict = solver.solve([64, 62], ["T6", "D"], key="C Major", allow_adjacent_unisons=False)
    assert res_strict.is_success is False

    res_unison = solver.solve([64, 62], ["T6", "D"], key="C Major", allow_adjacent_unisons=True)
    assert res_unison.is_success is True
    assert any((v.a == v.t or v.t == v.b or v.s == v.a) for v in res_unison.voicings)


def test_relax_hard_gates_mode():
    """
    relax_hard_gates=True finds a solution for melodies blocked by hard voice-leading rules,
    applying >= 10000.0 penalty and recording relaxed violation rule IDs.
    """
    solver = ViterbiSolver()
    melody = [71, 67]
    chords = ["D", "T"]

    # Strict mode rejects leading tone dropping:
    res_strict = solver.solve(melody, chords, key="C Major", relax_hard_gates=False)
    assert res_strict.is_success is False

    # Relax mode finds solution with penalty:
    res_relax = solver.solve(melody, chords, key="C Major", relax_hard_gates=True)
    assert res_relax.is_success is True
    assert res_relax.total_cost >= 10000.0
    assert res_relax.had_relaxed_violations is True
    assert len(res_relax.relaxed_rule_ids) > 0
    assert "RESOLUTION_LEADING_TONE_UP" in res_relax.relaxed_rule_ids


def test_pipeline_relax_hard_gates_e2e():
    """Harmonizer end-to-end supports relax_hard_gates for melodies without viable strict paths."""
    h = Harmonizer()
    melody = [60, 71]  # Strict rejects octave leaps / contrary motion

    res_strict = h.harmonize(melody, key="C Major", relax_hard_gates=False)
    assert res_strict.is_success is False

    res_relax = h.harmonize(melody, key="C Major", relax_hard_gates=True)
    assert res_relax.is_success is True
    best = res_relax.best_solution
    assert best is not None
    assert best.cost >= 10000.0
    assert best.had_relaxed_violations is True
    assert len(best.relaxed_rule_ids) > 0


def test_api_harmonize_default_response_contract(api_client):
    """Default API response must not contain relaxed fields or change baseline results."""
    payload = {
        "melody": [{"pitch": p} for p in [64, 65, 67, 64, 62, 60]],
        "key": {"tonic": "C", "mode": "Major"},
    }
    resp = api_client.post("/api/harmonize", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_success"] is True
    assert "relaxed" not in data
    top1 = data["candidates"][0]
    assert "relaxed_violations" not in top1
    assert top1["chords"] == ["T", "S6", "D6", "T", "D", "T"]
    assert top1["cost"] == 23.4


def test_api_harmonize_with_relaxed_flags(api_client):
    """API passes through allow_adjacent_unisons and relax_hard_gates."""
    # 1. Unison flag
    resp_unison = api_client.post(
        "/api/harmonize",
        json={
            "melody": [{"pitch": 67}, {"pitch": 74}],
            "key": {"tonic": "C", "mode": "Major"},
            "allow_adjacent_unisons": True,
        },
    )
    assert resp_unison.status_code == 200
    data_unison = resp_unison.json()
    assert data_unison["is_success"] is True

    # 2. Relax hard gates flag
    resp_relax = api_client.post(
        "/api/harmonize",
        json={
            "melody": [{"pitch": 60}, {"pitch": 71}],
            "key": {"tonic": "C", "mode": "Major"},
            "relax_hard_gates": True,
        },
    )
    assert resp_relax.status_code == 200
    data_relax = resp_relax.json()
    assert data_relax["is_success"] is True
    assert data_relax.get("relaxed") is True
    cand = data_relax["candidates"][0]
    assert cand["cost"] >= 10000.0
    assert isinstance(cand.get("relaxed_violations"), list)
    assert len(cand["relaxed_violations"]) > 0
