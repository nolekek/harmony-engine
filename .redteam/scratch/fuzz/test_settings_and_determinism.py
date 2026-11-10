"""
Test Settings, Edge Cases, and Determinism:
1. allow_secondary_dominants True vs False:
   - Tests fallback bug: api.py:165 (filtered_plans or all_plans)
   - Checks whether DD chords are actually blocked or leak into solutions
2. allow_extended_ranges True vs False:
   - Extreme pitch limits (Soprano 59/83, Bass 36)
3. max_plans: [1, 5, 10, 30, 50, 100, 200]
4. time_signature: ["4/4", "3/4", "2/4", "6/8", "3/8"]
5. Determinism:
   - 10 repeated queries with identical parameters
"""

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path("D:/aitraining")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, TimeSignature, calculate_metric_structure

API_URL = "http://127.0.0.1:8000/api/harmonize"


def post_api(payload: dict) -> dict:
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_secondary_dominants_setting():
    print("\n--- Testing allow_secondary_dominants (True vs False) ---")
    # Melody in G Major with C# (pitch 73) which forces Double Dominant (DD = A major / A7)
    # G Major: G4=67, A4=69, B4=71, C#5=73, D5=74
    mel_dd = [
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 69, "duration": "half", "is_downbeat": False},
        {"pitch": 71, "duration": "half", "is_downbeat": True},
        {"pitch": 73, "duration": "half", "is_downbeat": False},  # C#5
        {"pitch": 74, "duration": "whole", "is_downbeat": True},  # D5
    ]

    # Test False
    res_false = post_api({
        "melody": mel_dd,
        "key": {"tonic": "G", "mode": "Major"},
        "time_signature": "4/4",
        "allow_secondary_dominants": False,
        "allow_extended_ranges": False,
        "max_plans": 50,
    })

    # Test True
    res_true = post_api({
        "melody": mel_dd,
        "key": {"tonic": "G", "mode": "Major"},
        "time_signature": "4/4",
        "allow_secondary_dominants": True,
        "allow_extended_ranges": False,
        "max_plans": 50,
    })

    cands_false = res_false.get("candidates", [])
    cands_true = res_true.get("candidates", [])

    has_dd_in_false = any(any("DD" in c for c in cand["chords"]) for cand in cands_false)
    has_dd_in_true = any(any("DD" in c for c in cand["chords"]) for cand in cands_true)

    print(f"allow_secondary_dominants=False: success={res_false['is_success']}, candidates={len(cands_false)}, contains_DD={has_dd_in_false}")
    if cands_false:
        print(f"  Sample chords (False): {cands_false[0]['chords']}")
    print(f"allow_secondary_dominants=True: success={res_true['is_success']}, candidates={len(cands_true)}, contains_DD={has_dd_in_true}")
    if cands_true:
        print(f"  Sample chords (True): {cands_true[0]['chords']}")

    return {
        "mel_with_chromatic": [67, 69, 71, 73, 74],
        "false_setting": {
            "success": res_false["is_success"],
            "candidates_count": len(cands_false),
            "leaked_DD_chords": has_dd_in_false,
            "sample_chords": cands_false[0]["chords"] if cands_false else [],
        },
        "true_setting": {
            "success": res_true["is_success"],
            "candidates_count": len(cands_true),
            "contains_DD": has_dd_in_true,
            "sample_chords": cands_true[0]["chords"] if cands_true else [],
        },
    }


def test_extended_ranges_setting():
    print("\n--- Testing allow_extended_ranges (True vs False) ---")
    # Soprano B5 (pitch 83) is beyond STANDARD (max 81), but within EXTENDED (max 83)
    mel_high_s = [
        {"pitch": 72, "duration": "half", "is_downbeat": True},   # C5
        {"pitch": 83, "duration": "half", "is_downbeat": False},  # B5 (standard limit is 81)
        {"pitch": 72, "duration": "whole", "is_downbeat": True},  # C5
    ]

    res_std = post_api({
        "melody": mel_high_s,
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "allow_secondary_dominants": True,
        "allow_extended_ranges": False,
        "max_plans": 50,
    })

    res_ext = post_api({
        "melody": mel_high_s,
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "allow_secondary_dominants": True,
        "allow_extended_ranges": True,
        "max_plans": 50,
    })

    print(f"allow_extended_ranges=False: success={res_std['is_success']}, msg={res_std.get('message')}")
    print(f"allow_extended_ranges=True:  success={res_ext['is_success']}, msg={res_ext.get('message')}")

    return {
        "false_setting": {"success": res_std["is_success"], "message": res_std.get("message")},
        "true_setting": {"success": res_ext["is_success"], "message": res_ext.get("message")},
    }


def test_max_plans_sweep():
    print("\n--- Testing max_plans sweep on default melody ---")
    def_melody = [
        {"pitch": 64, "duration": "half", "is_downbeat": True},
        {"pitch": 65, "duration": "half", "is_downbeat": False},
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 64, "duration": "half", "is_downbeat": False},
        {"pitch": 62, "duration": "half", "is_downbeat": True},
        {"pitch": 60, "duration": "whole", "is_downbeat": False},
    ]

    plan_values = [1, 5, 10, 20, 30, 40, 50, 100, 200]
    results = {}

    for mp in plan_values:
        res = post_api({
            "melody": def_melody,
            "key": {"tonic": "C", "mode": "Major"},
            "time_signature": "4/4",
            "allow_secondary_dominants": True,
            "allow_extended_ranges": False,
            "max_plans": mp,
        })
        cands = len(res.get("candidates", []))
        best_cost = res.get("best_candidate", {}).get("cost") if res.get("best_candidate") else None
        results[mp] = {
            "success": res["is_success"],
            "candidates_count": cands,
            "best_cost": best_cost,
            "latency_ms": res.get("latency_ms"),
        }
        print(f"  max_plans={mp:>3} -> success={res['is_success']!s:<5}, candidates={cands}, best_cost={best_cost}, latency={res.get('latency_ms')} ms")

    return results


def test_time_signatures():
    print("\n--- Testing time signatures (3/4, 2/4, 6/8, 3/8, 4/4) ---")
    # 6 quarter notes: C4, D4, E4, F4, G4, C4
    pitches = [60, 62, 64, 65, 67, 60]
    time_sigs = ["4/4", "3/4", "2/4", "6/8", "3/8"]
    res_ts = {}

    for ts in time_sigs:
        mel = [{"pitch": p, "duration": "quarter"} for p in pitches]
        # Check metric structure computation
        ts_obj = TimeSignature.parse(ts)
        metric = calculate_metric_structure(mel, default_time_signature=ts_obj)
        downbeats = [m["is_downbeat"] for m in metric]

        res = post_api({
            "melody": mel,
            "key": {"tonic": "C", "mode": "Major"},
            "time_signature": ts,
            "allow_secondary_dominants": True,
            "allow_extended_ranges": False,
            "max_plans": 50,
        })

        cands = len(res.get("candidates", []))
        res_ts[ts] = {
            "downbeats": downbeats,
            "success": res["is_success"],
            "candidates_count": cands,
            "message": res.get("message"),
        }
        print(f"  ts={ts:<4} -> downbeats={downbeats}, success={res['is_success']}, candidates={cands}")

    return res_ts


def test_determinism():
    print("\n--- Testing determinism (10 repeated queries) ---")
    def_melody = [
        {"pitch": 64, "duration": "half", "is_downbeat": True},
        {"pitch": 65, "duration": "half", "is_downbeat": False},
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 64, "duration": "half", "is_downbeat": False},
        {"pitch": 62, "duration": "half", "is_downbeat": True},
        {"pitch": 60, "duration": "whole", "is_downbeat": False},
    ]

    fingerprints = []
    for run_i in range(10):
        res = post_api({
            "melody": def_melody,
            "key": {"tonic": "C", "mode": "Major"},
            "time_signature": "4/4",
            "allow_secondary_dominants": True,
            "allow_extended_ranges": False,
            "max_plans": 50,
        })
        cands = res.get("candidates", [])
        # Create structural fingerprint: (rank, cost, chords, voicings)
        fp = []
        for c in cands:
            fp.append((
                c["rank"],
                c["cost"],
                tuple(c["chords"]),
                tuple(tuple(v.values()) for v in c["voicings"]),
            ))
        fingerprints.append(fp)

    is_deterministic = all(fp == fingerprints[0] for fp in fingerprints)
    print(f"Determinism check across 10 identical runs: {'100% DETERMINISTIC' if is_deterministic else 'NON-DETERMINISTIC JITTER DETECTED'}")

    return {
        "is_deterministic": is_deterministic,
        "runs_count": len(fingerprints),
        "unique_fingerprints_count": len(set(tuple(tuple(x) for x in fp) for fp in fingerprints)),
    }


def main():
    print("=== STARTING SETTINGS, METRICS & DETERMINISM VERIFICATION ===")
    evidence_dir = Path("D:/aitraining/.redteam/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    sec_res = test_secondary_dominants_setting()
    ext_res = test_extended_ranges_setting()
    mp_res = test_max_plans_sweep()
    ts_res = test_time_signatures()
    det_res = test_determinism()

    full_output = {
        "secondary_dominants_setting": sec_res,
        "extended_ranges_setting": ext_res,
        "max_plans_sweep": mp_res,
        "time_signatures": ts_res,
        "determinism": det_res,
    }

    out_file = evidence_dir / "settings_and_determinism.json"
    out_file.write_text(json.dumps(full_output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAll tests complete! Saved to: {out_file}")


if __name__ == "__main__":
    main()
