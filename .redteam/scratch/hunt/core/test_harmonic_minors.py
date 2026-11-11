import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

h = Harmonizer()

MINOR_KEYS = [
    ("A", "MinorHarmonic", 57),  # A3 (57) -> A4 (69)
    ("E", "MinorHarmonic", 64),  # E4 (64) -> E5 (76)
    ("B", "MinorHarmonic", 59),  # B3 (59) -> B4 (71)
    ("F#", "MinorHarmonic", 66), # F#4 (66) -> F#5 (78)
    ("C#", "MinorHarmonic", 61), # C#4 (61) -> C#5 (73)
    ("G#", "MinorHarmonic", 68), # G#4 (68) -> G#5 (80)
    ("D", "MinorHarmonic", 62),  # D4 (62) -> D5 (74)
    ("G", "MinorHarmonic", 67),  # G4 (67) -> G5 (79)
    ("C", "MinorHarmonic", 60),  # C4 (60) -> C5 (72)
    ("F", "MinorHarmonic", 65),  # F4 (65) -> F5 (77)
    ("Bb", "MinorHarmonic", 70), # Bb4 (70) -> Bb5 (82 - out of soprano standard 81? Let's check Bb3=58)
    ("Eb", "MinorHarmonic", 63), # Eb4 (63) -> Eb5 (75)
]

# Harmonic minor intervals: 0, 2, 3, 5, 7, 8, 11, 12
intervals_asc = [0, 2, 3, 5, 7, 8, 11, 12]
intervals_desc = [12, 11, 8, 7, 5, 3, 2, 0]

print("=== TESTING 12 HARMONIC MINOR SCALES (ASCENDING & DESCENDING) ===", flush=True)

results = []

for tonic, mode, base_pitch in MINOR_KEYS:
    # Ensure pitches are comfortably within Soprano range 60..81
    # If base_pitch < 60, bump octave if base_pitch + 12 <= 81
    if base_pitch < 60:
        if base_pitch + 12 + 12 <= 81:
            base_pitch += 12
    # If base_pitch + 12 > 81, lower octave
    if base_pitch + 12 > 81:
        if base_pitch - 12 >= 60:
            base_pitch -= 12

    scale_asc = [base_pitch + iv for iv in intervals_asc]
    scale_desc = [base_pitch + iv for iv in intervals_desc]

    key_str = f"{tonic} {mode}"

    # Ascending
    res_asc = h.harmonize(scale_asc, key_str)
    # Descending
    res_desc = h.harmonize(scale_desc, key_str)

    results.append({
        "key": key_str,
        "base_pitch": base_pitch,
        "asc_success": res_asc.is_success,
        "asc_msg": res_asc.message,
        "asc_plans": [c.function for c in res_asc.best_solution.chords] if res_asc.is_success else [],
        "desc_success": res_desc.is_success,
        "desc_msg": res_desc.message,
        "desc_plans": [c.function for c in res_desc.best_solution.chords] if res_desc.is_success else [],
    })

    print(f"Key: {key_str:18} | ASC: {'PASS' if res_asc.is_success else 'FAIL'} ({res_asc.message[:40]}) | DESC: {'PASS' if res_desc.is_success else 'FAIL'} ({res_desc.message[:40]})", flush=True)

fail_count = sum(1 for r in results if not r["asc_success"] or not r["desc_success"])
print(f"\nTotal failures: {fail_count} out of {len(results)*2} tests", flush=True)
