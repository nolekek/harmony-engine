"""
Audit script for chromatic melodies in Brigade Harmony Engine.
Evaluates 15 chromatic test melodies across C-dur, G-dur, and F-dur.
Tracks success rates and functional progressions.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.harmony.pipeline import Harmonizer

CHROMATIC_TEST_SUITE: list[dict] = [
    # C-dur: Db, Ab, G#, D#/Eb
    {"name": "C-dur: Db Neapolitan leap", "key": "C Major", "melody": [60, 61, 64, 67, 60]},
    {"name": "C-dur: Ab chromatic submediant", "key": "C Major", "melody": [60, 64, 68, 69, 72, 60]},
    {"name": "C-dur: F-Ab bVI/N in cadence", "key": "C Major", "melody": [64, 65, 68, 69]},
    {"name": "C-dur: Db N6 stepwise cadence", "key": "C Major", "melody": [60, 61, 65, 67, 60]},
    {"name": "C-dur: Db descending to D", "key": "C Major", "melody": [60, 64, 61, 62, 60]},
    {"name": "C-dur: Db in soprano with F", "key": "C Major", "melody": [64, 61, 65, 67, 60]},
    {"name": "C-dur: Ab descending to G", "key": "C Major", "melody": [60, 68, 67, 65, 60]},
    {"name": "C-dur: Eb/D# minor third/bVI", "key": "C Major", "melody": [60, 63, 65, 67, 60]},
    {"name": "C-dur: F to Ab chromatic motion", "key": "C Major", "melody": [60, 65, 68, 67, 60]},
    {"name": "C-dur: Ab resolving to dominant", "key": "C Major", "melody": [64, 68, 67, 62, 60]},

    # G-dur: Ab (bII), Eb (bVI)
    {"name": "G-dur: Ab Neapolitan leap", "key": "G Major", "melody": [67, 68, 71, 74, 67]},
    {"name": "G-dur: Eb chromatic submediant", "key": "G Major", "melody": [67, 71, 75, 76, 79, 67]},
    {"name": "G-dur: C-Eb bVI cadence", "key": "G Major", "melody": [71, 72, 75, 76]},

    # F-dur: Gb (bII), Db (bVI)
    {"name": "F-dur: Gb Neapolitan leap", "key": "F Major", "melody": [65, 66, 69, 72, 65]},
    {"name": "F-dur: Db chromatic submediant", "key": "F Major", "melody": [65, 69, 73, 74, 77, 65]},
]


def run_audit() -> dict:
    harmonizer = Harmonizer()
    total = len(CHROMATIC_TEST_SUITE)
    passed = 0
    results = []

    print("=" * 60)
    print("CHROMATIC MELODY AUDIT (15 MELODIES)")
    print("=" * 60)

    for item in CHROMATIC_TEST_SUITE:
        name = item["name"]
        key = item["key"]
        melody = item["melody"]

        res = harmonizer.harmonize(melody, key=key)
        success = res.is_success
        if success:
            passed += 1
            chords = [c.function for c in res.best_solution.chords]
            cost = res.best_solution.cost
            status = f"PASS (cost={cost:.1f}, chords={chords})"
        else:
            status = f"FAIL ({res.message})"

        results.append({
            "name": name,
            "key": key,
            "melody": melody,
            "success": success,
            "status": status,
        })
        print(f"[{'OK' if success else 'FAIL'}] {name} ({key}): {status}")

    pct = (passed / total) * 100.0
    print("=" * 60)
    print(f"AUDIT SUMMARY: {passed}/{total} passed ({pct:.1f}%)")
    print("BASELINE: ~40% (~6/15)")
    print("TARGET: >= 70% (>= 11/15)")
    print(f"RESULT: {'MET (>= 70%)' if pct >= 70.0 else 'UNMET (< 70%)'}")
    print("=" * 60)

    return {"total": total, "passed": passed, "percent": pct, "results": results}


if __name__ == "__main__":
    run_audit()
