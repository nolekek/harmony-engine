"""
Wave 4, defect #8: failure diagnostics for the chromatic melody [60, 63, 64, 62, 60] (C Major).

Behaviour pinned by live probes:
- strict: is_success=False; blocking rule ids surface through solver / pipeline /
  service diagnostics, with FALSE_RELATION_PERECHENIE as a dominant blocker.
- relax_hard_gates=True: success; the first solution is T-bVI-K64-D-T and
  relaxed_rule_ids contains FALSE_RELATION_PERECHENIE (exact cost NOT pinned).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.service import clear_service_cache
from src.harmony.core.types import Chord, Key
from src.harmony.pipeline import Harmonizer
from src.harmony.solver.state_generator import clear_candidate_cache
from src.harmony.solver.viterbi import ViterbiSolver, clear_solver_cache

client = TestClient(app)

MELODY = [60, 63, 64, 62, 60]  # C4 - Eb4 - E4 - D4 - C4
KEY = "C Major"
API_MELODY = [{"pitch": p, "duration": "half"} for p in MELODY]
PLAN = ("T", "bVI", "K64", "D", "T")


@pytest.fixture(autouse=True)
def flush_all_caches():
    clear_candidate_cache()
    clear_solver_cache()
    clear_service_cache()
    yield
    clear_candidate_cache()
    clear_solver_cache()
    clear_service_cache()


def test_solver_diagnostics_contain_blocking_rules():
    """(4) Solver failure diagnostics carry blocking_rules while keeping legacy fields."""
    solver = ViterbiSolver()
    chords = [Chord(function=f) for f in PLAN]
    result = solver.solve(melody=MELODY, chords=chords, key=Key("C", "Major"))
    assert result.is_success is False
    assert result.diagnostics
    diag = result.diagnostics[0]
    # Additive contract: legacy keys must survive untouched.
    for legacy_field in ("step", "chord", "blocked", "message"):
        assert legacy_field in diag
    assert isinstance(diag.get("blocking_rules"), dict)
    assert diag["blocking_rules"], "pruned transitions must name their blocking rules"
    assert "FALSE_RELATION_PERECHENIE" in diag["blocking_rules"]


def test_strict_chromatic5_fails_with_false_relation_blocking_rules():
    """(1) Harmonizer strict -> failure, and pipeline diagnostics name the blockers."""
    result = Harmonizer().harmonize(MELODY, KEY)
    assert result.is_success is False
    assert result.diagnostics, "failure must expose pipeline diagnostics"
    blockers: dict[str, int] = {}
    for diag in result.diagnostics:
        assert {"step", "chord", "blocked", "message"} <= set(diag)
        blockers.update(diag.get("blocking_rules", {}))
    assert "FALSE_RELATION_PERECHENIE" in blockers


def test_relaxed_chromatic5_succeeds_with_expected_progression():
    """(2) Relaxed retry wins: T-bVI-K64-D-T with FALSE_RELATION_PERECHENIE relaxed."""
    result = Harmonizer().harmonize(MELODY, KEY, relax_hard_gates=True)
    assert result.is_success is True
    assert result.diagnostics == [], "success must leave diagnostics empty"
    assert result.had_relaxed_violations is True
    assert "FALSE_RELATION_PERECHENIE" in result.relaxed_rule_ids
    best = result.best_solution
    assert best is not None
    assert [c.function for c in best.chords] == ["T", "bVI", "K64", "D", "T"]
    # Relaxed penalty regime (>= 10000); the exact cost is deliberately not pinned.
    assert best.cost >= 10000.0


def test_service_strict_failure_exposes_dominant_blockers_and_relax_suggestion():
    """(3) Service error payload: dominant_blockers histogram + relax_suggestion."""
    res = client.post(
        "/api/harmonize",
        json={"melody": API_MELODY, "key": {"tonic": "C", "mode": "Major"}},
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["is_success"] is False
    err = data["error"]
    assert err["code"] == "NO_FEASIBLE_PLAN"

    dominant = err["dominant_blockers"]
    assert isinstance(dominant, dict)
    assert "FALSE_RELATION_PERECHENIE" in dominant
    counts = list(dominant.values())
    assert counts == sorted(counts, reverse=True), "histogram must be sorted descending"

    assert err["relax_suggestion"] is True
    assert any(
        isinstance(d.get("blocking_rules"), dict) for d in err["diagnostics"]
    ), "error.diagnostics must pass blocking_rules through"
