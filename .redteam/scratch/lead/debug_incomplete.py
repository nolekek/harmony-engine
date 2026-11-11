# -*- coding: utf-8 -*-
"""Debug: find candidates with incomplete chords (missing root/third/fifth)."""
import sys

sys.path.insert(0, r"D:\aitraining")

from fastapi.testclient import TestClient

from backend.main import app
from src.harmony.rules.doubling import get_triad_tones

client = TestClient(app)

CASES = [
    ("D", "Major", [67, 62, 64, 71, 69, 62]),
    ("D", "MinorHarmonic", [67, 62, 64, 71, 69, 62]),
    ("C#", "Major", [68, 63, 66, 61]),
    ("C", "Major", [69, 64, 62, 65, 64, 60]),
]
TONIC_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
            "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
SEVENTH = {"D7", "D65", "D43", "D2", "II7", "II65", "II43", "II2", "VII7", "VII65",
           "VII43", "VII2", "DD7", "DD65", "DD43", "DD2"}

for tonic, mode, pitches in CASES:
    body = {
        "melody": [{"pitch": p, "duration": "half"} for p in pitches],
        "key": {"tonic": tonic, "mode": mode},
        "time_signature": "4/4",
    }
    data = client.post("/api/harmonize", json=body).json()
    print(f"=== {tonic} {mode} cands={len(data.get('candidates') or [])}")
    for ci, cand in enumerate(data.get("candidates") or []):
        for i, (sym, v) in enumerate(zip(cand["chords"], cand["voicings"])):
            pcs = {v["soprano"] % 12, v["alto"] % 12, v["tenor"] % 12, v["bass"] % 12}
            root, third, fifth = get_triad_tones(sym, TONIC_PC[tonic],
                                                 "Minor" if "Minor" in mode else "Major")
            is_7 = sym.upper() in SEVENTH
            missing = [n for n, pc in (("root", root), ("third", third), ("fifth", fifth))
                       if pc not in pcs]
            if missing and (("third" in missing) or (not is_7 and i != len(cand["voicings"]) - 1 and "fifth" in missing)):
                print(f"  cand{ci} [{i} {sym}] {v['soprano'],v['alto'],v['tenor'],v['bass']} "
                      f"pcs={sorted(pcs)} missing={missing}")
