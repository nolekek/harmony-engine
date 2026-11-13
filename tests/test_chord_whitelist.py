"""
Tests for the grammar-derived chord whitelist (audit: VALID_CHORD_FUNCTIONS drift).
The whitelist must be a superset of grammar.ALL_FUNCTIONS (no false 422 on anything
the grammar can generate) while legacy aliases keep working.
"""

from fastapi.testclient import TestClient

from backend.api import VALID_CHORD_FUNCTIONS
from backend.main import app
from src.harmony.syntax.grammar import ALL_FUNCTIONS

client = TestClient(app)

_VOICING = {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48}


def test_whitelist_is_superset_of_grammar_functions():
    missing = set(ALL_FUNCTIONS) - set(VALID_CHORD_FUNCTIONS)
    assert not missing, f"Whitelist must accept everything the grammar generates; missing: {sorted(missing)}"


def test_whitelist_preserves_legacy_aliases():
    legacy = {"K6/4", "D6/5", "D65", "t", "bii6", "DD7", "VII65", "Cad64", "d7/v"}
    missing = legacy - set(VALID_CHORD_FUNCTIONS)
    assert not missing, f"Legacy aliases lost from whitelist: {sorted(missing)}"


def test_grade_smoke_for_every_grammar_function():
    for fn in ALL_FUNCTIONS:
        res = client.post(
            "/api/grade",
            json={
                "voicings": [_VOICING],
                "chords": [fn],
                "key": {"tonic": "C", "mode": "Major"},
            },
        )
        assert res.status_code == 200, (
            f"grade rejected grammar function {fn!r}: {res.status_code} {res.text[:200]}"
        )
        assert "report" in res.json()


def test_grade_rejects_unknown_function():
    res = client.post("/api/grade", json={"voicings": [_VOICING], "chords": ["XYZ"]})
    assert res.status_code == 422


def test_export_musicxml_rejects_unknown_function():
    res = client.post("/api/export/musicxml", json={"voicings": [_VOICING], "chords": ["XYZ"]})
    assert res.status_code == 422
