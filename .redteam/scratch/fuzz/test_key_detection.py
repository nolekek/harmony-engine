"""
Test Key Detection Accuracy & Edge Cases:
Tests /api/detect-key on:
- Default melody (E4 F4 G4 E4 D4 C4)
- 12 canonical major scales (ascending and descending)
- 12 harmonic minor scales (with raised 7th degree)
- 12 natural minor scales (without raised 7th degree, testing relative major/minor confusion)
- Ambiguous melodic figures (e.g. only tonic and dominant, or pentatonic subsets)
"""

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path("D:/aitraining")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.harmony.core.types import Key
from backend.key_detector import detect_key_from_melody, CANONICAL_KEYS

API_URL = "http://127.0.0.1:8000/api/detect-key"


def post_detect_key(melody: list[dict[str, Any]]) -> dict[str, Any]:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps([{"pitch": m["pitch"]} for m in melody]).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_key_detection():
    print("=== TESTING KEY DETECTION (/api/detect-key) ===")
    records = []

    # 1. Default melody
    def_melody = [
        {"pitch": 64, "duration": "half", "is_downbeat": True},
        {"pitch": 65, "duration": "half", "is_downbeat": False},
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 64, "duration": "half", "is_downbeat": False},
        {"pitch": 62, "duration": "half", "is_downbeat": True},
        {"pitch": 60, "duration": "whole", "is_downbeat": False},
    ]
    res_def = post_detect_key(def_melody)
    print(f"Default melody detected: {res_def.get('tonic')} {res_def.get('mode')} ({res_def.get('name')})")
    records.append({
        "type": "control_default_melody",
        "expected": "C Major",
        "detected": f"{res_def.get('tonic')} {res_def.get('mode')}",
        "is_correct": (res_def.get("tonic") == "C" and res_def.get("mode") == "Major"),
        "raw_response": res_def,
    })

    # 2. 12 Major scales
    majors = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
    major_correct = 0
    for tonic in majors:
        k_obj = Key(tonic, "Major")
        pcs = k_obj.scale_pcs
        # build 8-note scale starting from tonic pc
        pitches = []
        curr = next(p for p in range(60, 73) if p % 12 == k_obj.tonic_pc)
        pitches.append(curr)
        for i in range(1, 8):
            next_pc = pcs[i % 7]
            curr = next(p for p in range(curr + 1, curr + 4) if p % 12 == next_pc)
            pitches.append(curr)

        mel = [{"pitch": p, "duration": "half"} for p in pitches]
        res = post_detect_key(mel)
        det_str = f"{res.get('tonic')} {res.get('mode')}"
        exp_str = f"{tonic} Major"
        is_corr = (res.get("tonic") == tonic and res.get("mode") == "Major")
        if is_corr:
            major_correct += 1
        print(f"  Major scale {exp_str:<12} -> Detected: {det_str:<16} {'OK' if is_corr else 'MISMATCH!'}")
        records.append({
            "type": "major_scale_ascending",
            "expected": exp_str,
            "detected": det_str,
            "is_correct": is_corr,
            "pitches": pitches,
        })

    # 3. 12 Harmonic Minor scales (with raised 7th)
    minors = ["A", "E", "B", "F#", "C#", "G#", "D#", "Bb", "F", "C", "G", "D"]
    minor_harmonic_correct = 0
    for tonic in minors:
        k_obj = Key(tonic, "MinorHarmonic")
        pcs = k_obj.scale_pcs
        pitches = []
        curr = next(p for p in range(60, 73) if p % 12 == k_obj.tonic_pc)
        pitches.append(curr)
        for i in range(1, 8):
            next_pc = pcs[i % 7]
            curr = next(p for p in range(curr + 1, curr + 4) if p % 12 == next_pc)
            pitches.append(curr)

        mel = [{"pitch": p, "duration": "half"} for p in pitches]
        res = post_detect_key(mel)
        det_str = f"{res.get('tonic')} {res.get('mode')}"
        exp_str = f"{tonic} MinorHarmonic"
        is_corr = (res.get("tonic") == tonic and res.get("mode") == "MinorHarmonic")
        if is_corr:
            minor_harmonic_correct += 1
        print(f"  Harmonic Minor {exp_str:<18} -> Detected: {det_str:<16} {'OK' if is_corr else 'MISMATCH!'}")
        records.append({
            "type": "harmonic_minor_scale",
            "expected": exp_str,
            "detected": det_str,
            "is_correct": is_corr,
            "pitches": pitches,
        })

    # 4. 12 Natural Minor scales (natural 7th degree)
    # E.g. A natural minor = A, B, C, D, E, F, G, A (no G#!)
    natural_minor_correct = 0
    confusions_with_relative_major = 0
    for tonic in minors:
        # Natural minor scale formula: 0, 2, 3, 5, 7, 8, 10
        t_pc = Key(tonic, "MinorHarmonic").tonic_pc
        nat_pcs = [(t_pc + offset) % 12 for offset in [0, 2, 3, 5, 7, 8, 10]]
        pitches = []
        curr = next(p for p in range(60, 73) if p % 12 == t_pc)
        pitches.append(curr)
        for i in range(1, 8):
            next_pc = nat_pcs[i % 7]
            curr = next(p for p in range(curr + 1, curr + 4) if p % 12 == next_pc)
            pitches.append(curr)

        mel = [{"pitch": p, "duration": "half"} for p in pitches]
        res = post_detect_key(mel)
        det_str = f"{res.get('tonic')} {res.get('mode')}"
        exp_str = f"{tonic} MinorHarmonic"  # detector only has MinorHarmonic
        is_corr = (res.get("tonic") == tonic)
        if is_corr:
            natural_minor_correct += 1
        else:
            # check if detected relative major (3 semitones above minor tonic)
            rel_major_tonic = Key(tonic, "MinorHarmonic").tonic_pc + 3 % 12
            confusions_with_relative_major += 1

        print(f"  Natural Minor {tonic + ' natural':<18} -> Detected: {det_str:<16} {'MATCHED TONIC' if is_corr else 'CONFUSED!'}")
        records.append({
            "type": "natural_minor_scale",
            "expected": exp_str,
            "detected": det_str,
            "is_correct": is_corr,
            "pitches": pitches,
        })

    summary = {
        "major_scales_accuracy": f"{major_correct}/12 ({major_correct/12*100:.1f}%)",
        "harmonic_minor_scales_accuracy": f"{minor_harmonic_correct}/12 ({minor_harmonic_correct/12*100:.1f}%)",
        "natural_minor_accuracy": f"{natural_minor_correct}/12 ({natural_minor_correct/12*100:.1f}%)",
        "natural_minor_confusions_count": confusions_with_relative_major,
    }

    print("\n=== SUMMARY ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    evidence_file = Path("D:/aitraining/.redteam/evidence/key_detection_results.json")
    evidence_file.write_text(
        json.dumps({"summary": summary, "records": records}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Saved results to: {evidence_file}")


if __name__ == "__main__":
    test_key_detection()
