"""
Unit and integration tests for chromatic harmony layer (Neapolitan chord N and chromatic submediant bVI).
Tests Brigade rules, triad tones, solver integration, and FastAPI /api/grade validation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from src.harmony.core.chord import ChordFunction, ChordDefinition, Inversion
from src.harmony.core.key import Key as CoreKey, Mode
from src.harmony.core.pitch import PitchClass, ScaleDegree
from src.harmony.rules.doubling import get_triad_tones, check_doubling
from src.harmony.pipeline import Harmonizer


client = TestClient(app)


class TestChromaticTriadTonesAndDefinitions:
    """Verifies Requirement (в): get_triad_tones and ChordFunction/Definition for N and bVI."""

    def test_get_triad_tones_neapolitan_and_bvi(self):
        # (в) get_triad_tones("N",0,"Major") == (1,5,8), ("bVI") == (8,0,3)
        assert get_triad_tones("N", 0, "Major") == (1, 5, 8)
        assert get_triad_tones("bVI", 0, "Major") == (8, 0, 3)

        # Inversions must return same pitch classes
        assert get_triad_tones("N6", 0, "Major") == (1, 5, 8)
        assert get_triad_tones("bVI6", 0, "Major") == (8, 0, 3)

        # Other keys (e.g. G-dur: tonic=7 -> N is (8, 0, 3); bVI is (3, 7, 10))
        assert get_triad_tones("N", 7, "Major") == (8, 0, 3)
        assert get_triad_tones("bVI", 7, "Major") == (3, 7, 10)

    def test_chord_function_enum_and_from_str(self):
        assert ChordFunction.N == "N"
        assert ChordFunction.BVI == "bVI"
        assert ChordFunction.from_str("N") == ChordFunction.N
        assert ChordFunction.from_str("n") == ChordFunction.N
        assert ChordFunction.from_str("bVI") == ChordFunction.BVI
        assert ChordFunction.from_str("bvi") == ChordFunction.BVI
        assert ChordFunction.from_str("BVI") == ChordFunction.BVI
        assert ChordFunction.N.root_scale_degree == ScaleDegree(2, -1)
        assert ChordFunction.BVI.root_scale_degree == ScaleDegree(6, -1)

    def test_chord_definition_from_string(self):
        k = CoreKey(tonic=PitchClass.C, mode=Mode.MAJOR)
        cd_n = ChordDefinition.from_string("N", k)
        assert cd_n.function == ChordFunction.N
        assert cd_n.inversion == Inversion.ROOT
        assert cd_n.root == PitchClass(1)
        assert cd_n.third == PitchClass(5)
        assert cd_n.fifth == PitchClass(8)

        cd_n6 = ChordDefinition.from_string("N6", k)
        assert cd_n6.function == ChordFunction.N
        assert cd_n6.inversion == Inversion.SEXTA
        assert cd_n6.bass_pitch_class == PitchClass(5)  # Third in bass for 6th chord

        cd_bvi = ChordDefinition.from_string("bVI", k)
        assert cd_bvi.function == ChordFunction.BVI
        assert cd_bvi.inversion == Inversion.ROOT
        assert cd_bvi.root == PitchClass(8)
        assert cd_bvi.third == PitchClass(0)
        assert cd_bvi.fifth == PitchClass(3)

        cd_bvi6 = ChordDefinition.from_string("bVI6", k)
        assert cd_bvi6.function == ChordFunction.BVI
        assert cd_bvi6.inversion == Inversion.SEXTA
        assert cd_bvi6.bass_pitch_class == PitchClass(0)  # Third (tonic) in bass


class TestChromaticHarmonization:
    """Verifies Requirements (а) and (б): 3-4 chromatic melodies harmonize, top-1 cadence via D/K64 ending on T."""

    def test_neapolitan_melody_harmonization(self):
        # [60,61,64,67,60] (C, Db, E, G, C) — Db as N or N6
        h = Harmonizer()
        res = h.harmonize([60, 61, 64, 67, 60], key="C Major")
        assert res.is_success is True, f"Failed: {res.message}"
        assert res.best_solution is not None

        chords = [c.function for c in res.best_solution.chords]
        # (a) Harmonizes
        assert len(chords) == 5
        # Contains Neapolitan chord for note Db
        assert any(ch in ("N", "N6") for ch in chords)
        # (b) In top-1: final is T, cadence via dominant group (D, D6, D7, K64)
        assert chords[-1] in ("T", "T53")
        assert chords[-2] in ("D", "D6", "D7", "D65", "D43", "D2", "K64")
        assert res.best_solution.cost >= 0

    def test_chromatic_submediant_melody_harmonization(self):
        # [60,64,68,69,72,60] (C, E, Ab, A, C5, C) — Ab as bVI
        h = Harmonizer()
        res = h.harmonize([60, 64, 68, 69, 72, 60], key="C Major")
        assert res.is_success is True, f"Failed: {res.message}"
        assert res.best_solution is not None

        chords = [c.function for c in res.best_solution.chords]
        assert len(chords) == 6
        assert any(ch in ("bVI", "bVI6") for ch in chords)
        assert chords[-1] in ("T", "T53")
        assert res.best_solution.cost >= 0

    def test_chromatic_cadence_melody_harmonization(self):
        # [64,65,68,69] (E, F, Ab, A) — bVI/N in cadence
        h = Harmonizer()
        res = h.harmonize([64, 65, 68, 69], key="C Major")
        assert res.is_success is True, f"Failed: {res.message}"
        assert res.best_solution is not None

        chords = [c.function for c in res.best_solution.chords]
        assert len(chords) == 4
        assert any(ch in ("N", "N6", "bVI", "bVI6") for ch in chords)
        assert res.best_solution.cost >= 0

    def test_chromatic_dominant_cadence_melody(self):
        # [64, 68, 67, 62, 60] (E, Ab, G, D, C) — Ab resolving to dominant cadence
        h = Harmonizer()
        res = h.harmonize([64, 68, 67, 62, 60], key="C Major")
        assert res.is_success is True, f"Failed: {res.message}"
        assert res.best_solution is not None

        chords = [c.function for c in res.best_solution.chords]
        assert chords[-1] in ("T", "t")
        assert chords[-2] in ("D", "D6", "D7", "D65", "D43", "D2", "K64")
        assert res.best_solution.cost >= 0


class TestBackendGradeEndpointWithChromaticChords:
    """Verifies Requirement (г): /api/grade accepts ['N6', 'K64', 'D7', 'T'] without 422."""

    def test_grade_accepts_n6_k64_d7_t(self):
        # Submit valid SATB voicing sequence with ['N6', 'K64', 'D7', 'T']
        payload = {
            "voicings": [
                {"soprano": 65, "alto": 61, "tenor": 56, "bass": 41},  # N6 (F, Db, Ab, F)
                {"soprano": 64, "alto": 60, "tenor": 55, "bass": 43},  # K64 (E, C, G, G)
                {"soprano": 62, "alto": 59, "tenor": 53, "bass": 43},  # D7 (D, B, F, G)
                {"soprano": 60, "alto": 60, "tenor": 52, "bass": 36},  # T (C, C, E, C)
            ],
            "chords": ["N6", "K64", "D7", "T"],
            "key": {"tonic": "C", "mode": "Major"},
        }
        res = client.post("/api/grade", json=payload)
        # Must not return 422 Unprocessable Entity
        assert res.status_code != 422, f"Got 422 error: {res.text}"
        assert res.status_code == 200
        data = res.json()
        assert "report" in data
        assert isinstance(data["report"]["is_valid"], bool)

    def test_grade_accepts_bvi_and_bvi6(self):
        # Test bVI and bVI6 in /api/grade
        payload = {
            "voicings": [
                {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48},  # T
                {"soprano": 68, "alto": 60, "tenor": 51, "bass": 44},  # bVI
                {"soprano": 69, "alto": 60, "tenor": 53, "bass": 41},  # S
                {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48},  # T
            ],
            "chords": ["T", "bVI", "S", "T"],
            "key": {"tonic": "C", "mode": "Major"},
        }
        res = client.post("/api/grade", json=payload)
        assert res.status_code != 422, f"Got 422 error: {res.text}"
        assert res.status_code == 200
