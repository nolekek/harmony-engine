"""
Tests for key detection algorithm (T19).
Verifies Krumhansl-Schmuckler profile scoring, half cadences, authentic cadences,
duration weighting, and determinism.
"""

import pytest
from backend.key_detector import CANONICAL_KEYS, detect_key_from_melody


class TestKeyDetection:
    def test_half_cadence_c_major(self):
        """
        (a) [60, 62, 64, 65, 67] (C D E F G, half cadence ending on dominant G).
        Old naive heuristic gave +60 for last note == tonic and incorrectly detected G Major.
        K-S profile scoring must identify this as C Major.
        """
        # Test with raw int pitches
        res_int = detect_key_from_melody([60, 62, 64, 65, 67])
        assert res_int["tonic"] == "C"
        assert res_int["mode"] == "Major"
        assert res_int["fifths"] == 0

        # Test with dict items
        melody_dicts = [{"pitch": p} for p in [60, 62, 64, 65, 67]]
        res_dict = detect_key_from_melody(melody_dicts)
        assert res_dict["tonic"] == "C"
        assert res_dict["mode"] == "Major"

    def test_half_cadence_a_minor(self):
        """
        (b) [57, 59, 60, 62, 64] (A B C D E, a-moll, half cadence ending on dominant E).
        Old naive heuristic gave +60 for last note == tonic and incorrectly detected E MinorHarmonic.
        K-S profile scoring must identify this as A minor.
        CANONICAL_KEYS catalogs classical minor as MinorHarmonic (Бригадный учебник).
        """
        res = detect_key_from_melody([57, 59, 60, 62, 64])
        assert res["tonic"] == "A"
        # The engine catalogs 12 harmonic minors in CANONICAL_KEYS: mode is MinorHarmonic
        assert res["mode"] in ("MinorHarmonic", "Minor")
        assert res["mode"] == "MinorHarmonic"
        assert res["fifths"] == 0

    def test_default_melody_c_major(self):
        """
        (c) Default melody [64, 65, 67, 64, 62, 60] (E F G E D C) -> C Major.
        """
        res = detect_key_from_melody([64, 65, 67, 64, 62, 60])
        assert res["tonic"] == "C"
        assert res["mode"] == "Major"

    def test_arpeggiated_tonic_c_major(self):
        """
        (d) [60, 64, 67, 60] (C E G C) -> C Major.
        Has tonic triad and V-I cadence (G4 -> C4).
        """
        res = detect_key_from_melody([60, 64, 67, 60])
        assert res["tonic"] == "C"
        assert res["mode"] == "Major"

    def test_determinism(self):
        """
        (e) Determinism: two successive calls with identical input return identical dicts.
        """
        melody = [60, 62, 64, 65, 67]
        res1 = detect_key_from_melody(melody)
        res2 = detect_key_from_melody(melody)
        assert res1 == res2
        assert res1["tonic"] == res2["tonic"]
        assert res1["mode"] == res2["mode"]
        assert res1["name"] == res2["name"]
        assert res1["fifths"] == res2["fifths"]

    def test_contract_canonical_keys_compatibility(self):
        """
        Verify return contract: dict contains tonic, mode, name, fifths,
        matching an entry in CANONICAL_KEYS.
        """
        # Empty melody fallback
        res_empty = detect_key_from_melody([])
        assert res_empty in CANONICAL_KEYS
        assert res_empty["tonic"] == "C"
        assert res_empty["mode"] == "Major"

        # Non-empty melody
        res = detect_key_from_melody([60, 64, 67])
        assert res in CANONICAL_KEYS
        for field in ("tonic", "mode", "name", "fifths"):
            assert field in res

    def test_half_cadence_other_keys(self):
        """
        Verify that half cadences in other keys are not hijacked by their dominant.
        G Major half cadence: [67, 69, 71, 72, 74] (G A B C D) -> G Major, NOT D Major.
        D Minor half cadence: [62, 64, 65, 67, 69] (D E F G A) -> D MinorHarmonic, NOT A.
        """
        # G Major: G4, A4, B4, C5, D5
        res_g = detect_key_from_melody([67, 69, 71, 72, 74])
        assert res_g["tonic"] == "G"
        assert res_g["mode"] == "Major"

        # D Minor: D4, E4, F4, G4, A4
        res_d = detect_key_from_melody([62, 64, 65, 67, 69])
        assert res_d["tonic"] == "D"
        assert res_d["mode"] == "MinorHarmonic"

    def test_duration_weighting(self):
        """
        Verify that duration weights influence pitch class distribution.
        Long tonic triad notes outweigh short passing chromatic notes.
        """
        melody = [
            {"pitch": 60, "duration": "whole"},      # C (4.0)
            {"pitch": 61, "duration": "sixteenth"},  # C# passing (0.25)
            {"pitch": 62, "duration": "sixteenth"},  # D passing (0.25)
            {"pitch": 64, "duration": "whole"},      # E (4.0)
            {"pitch": 67, "duration": "whole"},      # G (4.0)
            {"pitch": 60, "duration": "whole"},      # C (4.0)
        ]
        res = detect_key_from_melody(melody)
        assert res["tonic"] == "C"
        assert res["mode"] == "Major"

    def test_cadence_bonuses_v_i_and_v_vi(self):
        """
        Verify that cadence endings V-I (authentic) and V-VI (interrupted/deceptive)
        are properly detected.
        """
        # V-I cadence in F Major: C5 (72) -> F4 (65)
        f_melody = [65, 69, 72, 65]  # F A C F
        res_f = detect_key_from_melody(f_melody)
        assert res_f["tonic"] == "F"
        assert res_f["mode"] == "Major"

        # V-VI cadence in C Major: [C, D, E, F, G, A] (ends on G -> A)
        c_deceptive = [60, 62, 64, 65, 67, 69]
        res_c = detect_key_from_melody(c_deceptive)
        assert res_c["tonic"] == "C"
        assert res_c["mode"] == "Major"
