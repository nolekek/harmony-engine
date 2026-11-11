"""
Opt-in escape-hatch flags: adjacent unisons and relaxed hard gates.

Semantics under test:
1. Strict defaults are untouched (no unisons, no relaxed violations).
2. `allow_adjacent_unisons=True` unlocks unisons that the strict lattice forbids.
3. `relax_hard_gates=True` is a LAST RESORT: when a strictly legal plan exists it
   must win over a plan carrying 10000-point penalties.
4. The flags are accepted by the solver, the pipeline and the HTTP API.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from src.harmony.core.types import Chord, Key
from src.harmony.pipeline import Harmonizer
from src.harmony.solver.viterbi import ViterbiSolver

client = TestClient(app, raise_server_exceptions=False)

MELODY = [64, 65, 67, 64, 62, 60]  # C4 D4 E4 C4 B3 C4
KEY = "C Major"
API_MELODY = [{"pitch": p, "duration": "half"} for p in MELODY]


def _voicings(result):
    return [(v.s, v.a, v.t, v.b) for v in result.best_solution.voicings]


def _has_unison(voicings):
    return any(len(set(v)) < 4 for v in voicings)


def test_strict_defaults_have_no_unisons_and_no_relaxation():
    result = Harmonizer().harmonize(MELODY, KEY)
    assert result.is_success
    assert not _has_unison(_voicings(result))
    assert result.best_solution.relaxed_rule_ids == []


def test_allow_adjacent_unisons_unlocks_unison_voicing():
    result = Harmonizer().harmonize(MELODY, KEY, allow_adjacent_unisons=True)
    assert result.is_success
    assert _has_unison(_voicings(result)), "flag must actually reach the lattice generator"


def test_relax_hard_gates_prefers_strictly_legal_plan():
    melody = [60, 62, 64, 65, 67]
    strict = Harmonizer().harmonize(melody, KEY)
    relaxed = Harmonizer().harmonize(melody, KEY, relax_hard_gates=True)

    assert strict.is_success and relaxed.is_success
    # The clean plan must win; no 10000-point penalties may leak into the result.
    assert relaxed.best_solution.relaxed_rule_ids == []
    assert relaxed.best_solution.cost == pytest.approx(strict.best_solution.cost)
    assert [c.function for c in relaxed.best_solution.chords] == [
        c.function for c in strict.best_solution.chords
    ]


def test_solver_exposes_relaxation_metadata():
    solver = ViterbiSolver()
    chords = [Chord(function=f) for f in ("T", "II6", "K64", "D7", "T")]
    result = solver.solve(
        melody=[60, 62, 64, 65, 67],
        chords=chords,
        key=Key("C", "Major"),
        relax_hard_gates=True,
    )
    assert result.is_success
    assert hasattr(result, "had_relaxed_violations")
    assert isinstance(result.relaxed_rule_ids, list)


def test_api_accepts_relaxed_flags():
    payload = {
        "melody": API_MELODY,
        "key": {"tonic": "C", "mode": "Major"},
        "allow_adjacent_unisons": True,
        "relax_hard_gates": True,
    }
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data.get("is_success") is True
    assert data.get("candidates")


def test_api_default_response_has_no_relaxed_metadata():
    payload = {"melody": API_MELODY, "key": {"tonic": "C", "mode": "Major"}}
    res = client.post("/api/harmonize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data.get("is_success") is True
    for cand in data.get("candidates", []):
        assert "relaxed_violations" not in cand


def test_api_relax_hard_gates_still_prefers_strict_plan():
    strict_melody = [{"pitch": p, "duration": "half"} for p in (60, 62, 64, 65, 67)]
    key = {"tonic": "C", "mode": "Major"}

    strict = client.post("/api/harmonize", json={"melody": strict_melody, "key": key})
    relaxed = client.post(
        "/api/harmonize",
        json={"melody": strict_melody, "key": key, "relax_hard_gates": True},
    )
    assert strict.status_code == relaxed.status_code == 200
    strict_data, relaxed_data = strict.json(), relaxed.json()

    assert relaxed_data["is_success"] is True
    # A clean plan exists, so the HTTP layer must return it instead of a
    # 10000-point-penalty compromise.
    assert relaxed_data["best_candidate"]["cost"] < 1000
    assert relaxed_data["best_candidate"]["cost"] == pytest.approx(
        strict_data["best_candidate"]["cost"]
    )
    assert "relaxed_violations" not in relaxed_data["best_candidate"]

