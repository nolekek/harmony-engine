"""
Red-Team Fuzzing Script: Comprehensive category testing on src.harmony core.
Covers:
1. Control (Default melody)
2. 24 canonical keys (12 major, 12 harmonic minor) with scales, arpeggios, figures
3. Random diatonic melodies (seed=42) across 4/4, 3/4, 2/4, 6/8
4. Non-Chord Tones (NCT) melodies (passing, neighbor tones)
5. Chromatic / Altered notes

Collects granular diagnostics for every rejection:
- grammar plans count
- solver failure step
- solver failure message
- failure classification
"""

import json
import random
import sys
import time
from pathlib import Path
from typing import Any

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path("D:/aitraining")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, Chord, calculate_metric_structure, TimeSignature
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver


def run_single_test(
    harmonizer: Harmonizer,
    melody: list[dict[str, Any]],
    key_str: str,
    time_signature: str = "4/4",
    max_plans: int = 30,
    allow_extended_ranges: bool = False,
) -> dict[str, Any]:
    parsed_key = Key.parse(key_str)
    parsed_ts = TimeSignature.parse(time_signature)
    metric_info = calculate_metric_structure(melody, default_time_signature=parsed_ts)
    processed_melody = [
        {"pitch": m["pitch"], "duration": m["duration"], "is_downbeat": m["is_downbeat"]}
        for m in metric_info
    ]

    t0 = time.perf_counter()

    # 1. Grammar plans
    grammar = HarmonicGrammar(key=parsed_key)
    plans = grammar.generate_plans(processed_melody, key=parsed_key, max_plans=max_plans)
    t_grammar = round((time.perf_counter() - t0) * 1000, 2)

    # 2. Pipeline harmonize
    t1 = time.perf_counter()
    res = harmonizer.harmonize(
        melody=processed_melody,
        key=parsed_key,
        time_signature=parsed_ts,
        max_plans=max_plans,
        allow_extended_ranges=allow_extended_ranges,
    )
    t_total = round((time.perf_counter() - t0) * 1000, 2)
    t_solver = round((time.perf_counter() - t1) * 1000, 2)

    # Detailed solver diagnostics if rejected
    solver_diagnostics: list[dict[str, Any]] = []
    failure_type = "SUCCESS"
    detailed_reason = ""

    if not res.is_success:
        if len(plans) == 0:
            failure_type = "NO_PLANS"
            detailed_reason = "HarmonicGrammar generated 0 candidate functional plans."
        else:
            # Test individual plans with ViterbiSolver directly to extract step failure
            solver = ViterbiSolver()
            plan_failures = []
            for p_idx, plan in enumerate(plans):
                s_res = solver.solve(
                    melody=processed_melody,
                    chords=plan,
                    key=parsed_key,
                    allow_extended_ranges=allow_extended_ranges,
                )
                plan_failures.append({
                    "plan_idx": p_idx,
                    "plan": [c.function for c in plan],
                    "message": s_res.message,
                    "diagnostics": [
                        {
                            "step": d.step_index,
                            "chord": d.chord,
                            "pitch": d.soprano_pitch,
                            "candidates": d.candidates_count,
                            "reachable": d.reachable_candidates_count,
                        }
                        for d in s_res.diagnostics
                    ],
                })
            solver_diagnostics = plan_failures

            first_msg = plan_failures[0]["message"] if plan_failures else "Unknown"
            if "no candidate voicings found" in first_msg:
                failure_type = "NO_CANDIDATES_AT_STEP"
                detailed_reason = first_msg
            elif "blocked by hard-rule violations" in first_msg:
                failure_type = "LATTICE_BLOCKED_BY_HARD_RULES"
                detailed_reason = first_msg
            elif "Initial step 0 has no valid voicings" in first_msg:
                failure_type = "STEP_0_BLOCKED"
                detailed_reason = first_msg
            else:
                failure_type = "SOLVER_REJECTED"
                detailed_reason = first_msg

    return {
        "is_success": res.is_success,
        "solutions_count": len(res.solutions),
        "best_cost": res.best_solution.cost if res.best_solution else None,
        "plans_generated": len(plans),
        "first_plan": [c.function for c in plans[0]] if plans else [],
        "pipeline_message": res.message,
        "failure_type": failure_type,
        "detailed_reason": detailed_reason,
        "solver_diagnostics": solver_diagnostics[:3],  # keep top 3 plans diagnostics
        "timing_ms": {
            "grammar": t_grammar,
            "solver": t_solver,
            "total": t_total,
        },
    }


def build_scale_melodies(key_obj: Key) -> list[tuple[str, list[dict[str, Any]]]]:
    """Builds scale, arpeggio, and figure melodies strictly within Soprano compass (60..81)."""
    scale_pcs = key_obj.scale_pcs
    tonic_pc = key_obj.tonic_pc

    # Find base octave for tonic in soprano range [60, 81]
    # Options for tonic MIDI pitch
    tonic_pitches = [p for p in range(60, 82) if p % 12 == tonic_pc]
    base_tonic = tonic_pitches[0] if tonic_pitches else 60

    # 1. Ascending scale 8 notes
    # Generate 8 scale pitches starting from base_tonic
    asc_pitches = [base_tonic]
    curr = base_tonic
    deg_idx = 0
    # Map scale pcs
    for step in range(1, 8):
        # next scale pitch class
        next_pc = scale_pcs[step % 7]
        # find lowest pitch > curr with pc == next_pc
        curr = next((p for p in range(curr + 1, curr + 4) if p % 12 == next_pc), curr + 1)
        asc_pitches.append(curr)

    # If asc_pitches exceeds 81, shift down octave if possible
    if max(asc_pitches) > 81:
        if min(asc_pitches) - 12 >= 60:
            asc_pitches = [p - 12 for p in asc_pitches]

    # 2. Descending scale 8 notes
    desc_pitches = list(reversed(asc_pitches))

    # 3. Tonic triad arpeggio: 1 - 3 - 5 - 8 - 5 - 3 - 1
    deg1 = asc_pitches[0]
    deg3 = asc_pitches[2]
    deg5 = asc_pitches[4]
    deg8 = asc_pitches[7]
    triad_pitches = [deg1, deg3, deg5, deg8, deg5, deg3, deg1]

    # 4. Simple melodic figure: 1 - 2 - 3 - 2 - 1
    deg2 = asc_pitches[1]
    figure_pitches = [deg1, deg2, deg3, deg2, deg1]

    def to_notes(pitches: list[int], duration: str = "half") -> list[dict[str, Any]]:
        return [{"pitch": p, "duration": duration, "is_downbeat": (i % 2 == 0)} for i, p in enumerate(pitches)]

    results = []
    if all(60 <= p <= 81 for p in asc_pitches):
        results.append(("scale_ascending_8", to_notes(asc_pitches)))
    if all(60 <= p <= 81 for p in desc_pitches):
        results.append(("scale_descending_8", to_notes(desc_pitches)))
    if all(60 <= p <= 81 for p in triad_pitches):
        results.append(("triad_arpeggio_7", to_notes(triad_pitches)))
    if all(60 <= p <= 81 for p in figure_pitches):
        results.append(("melodic_figure_5", to_notes(figure_pitches)))

    return results


def main():
    print("=== STARTING COMPREHENSIVE RED-TEAM FUZZING ===")
    harmonizer = Harmonizer()

    all_records: list[dict[str, Any]] = []
    category_summary: dict[str, dict[str, Any]] = {}

    def record_test(category: str, name: str, key_str: str, melody: list[dict[str, Any]], ts: str = "4/4"):
        res = run_single_test(harmonizer, melody, key_str, time_signature=ts)
        rec = {
            "category": category,
            "name": name,
            "key": key_str,
            "time_signature": ts,
            "length": len(melody),
            "pitches": [m["pitch"] for m in melody],
            "durations": [m.get("duration", "half") for m in melody],
            "result": res,
        }
        all_records.append(rec)

        if category not in category_summary:
            category_summary[category] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "failure_types": {},
                "reasons": {},
            }
        cs = category_summary[category]
        cs["total"] += 1
        if res["is_success"]:
            cs["passed"] += 1
        else:
            cs["failed"] += 1
            ft = res["failure_type"]
            cs["failure_types"][ft] = cs["failure_types"].get(ft, 0) + 1
            reason = res["detailed_reason"]
            cs["reasons"][reason] = cs["reasons"].get(reason, 0) + 1

        print(f"[{category}] {name} ({key_str}): {'PASS' if res['is_success'] else 'FAIL (' + res['failure_type'] + ')'}")

    # ==========================================
    # 1. CONTROL TEST
    # ==========================================
    ctrl_melody = [
        {"pitch": 64, "duration": "half", "is_downbeat": True},
        {"pitch": 65, "duration": "half", "is_downbeat": False},
        {"pitch": 67, "duration": "half", "is_downbeat": True},
        {"pitch": 64, "duration": "half", "is_downbeat": False},
        {"pitch": 62, "duration": "half", "is_downbeat": True},
        {"pitch": 60, "duration": "whole", "is_downbeat": False},
    ]
    record_test("1_control", "default_melody_E4_F4_G4_E4_D4_C4", "C Major", ctrl_melody, "4/4")

    # ==========================================
    # 2. 24 CANONICAL KEYS (12 Major, 12 Harmonic Minor)
    # ==========================================
    majors = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
    minors = ["A", "E", "B", "F#", "C#", "G#", "D#", "Bb", "F", "C", "G", "D"]

    for m_tonic in majors:
        key_str = f"{m_tonic} Major"
        k_obj = Key(m_tonic, "Major")
        mels = build_scale_melodies(k_obj)
        for subname, mel in mels:
            record_test("2_canonical_majors", f"{m_tonic}_major_{subname}", key_str, mel, "4/4")

    for min_tonic in minors:
        key_str = f"{min_tonic} MinorHarmonic"
        k_obj = Key(min_tonic, "MinorHarmonic")
        mels = build_scale_melodies(k_obj)
        for subname, mel in mels:
            record_test("2_canonical_minors", f"{min_tonic}_minor_{subname}", key_str, mel, "4/4")

    # ==========================================
    # 3. RANDOM DIATONIC MELODIES (Seed 42)
    # ==========================================
    random.seed(42)
    time_signatures = ["4/4", "3/4", "2/4", "6/8"]
    dur_choices = ["half", "whole", "quarter"]

    for idx in range(120):
        ts = random.choice(time_signatures)
        k_tonic = random.choice(["C", "G", "F", "D", "A"])
        k_mode = random.choice(["Major", "MinorHarmonic"])
        k_str = f"{k_tonic} {k_mode}"
        k_obj = Key(k_tonic, k_mode)
        scale_pcs = set(k_obj.scale_pcs)
        tonic_pc = k_obj.tonic_pc

        length = random.choice([4, 6, 8, 10, 12])
        # Start on tonic triad tone
        start_candidates = [p for p in range(60, 82) if (p % 12) in {tonic_pc, (tonic_pc + (3 if 'Minor' in k_mode else 4)) % 12, (tonic_pc + 7) % 12}]
        curr_p = random.choice(start_candidates) if start_candidates else 60

        mel_pitches = [curr_p]
        for step_i in range(1, length - 1):
            # predominantly steps (1, 2) or thirds (3, 4)
            step_size = random.choices([1, 2, -1, -2, 3, 4, -3, -4], weights=[25, 25, 25, 25, 10, 10, 10, 10])[0]
            cand = curr_p + step_size
            if 60 <= cand <= 81 and (cand % 12) in scale_pcs:
                curr_p = cand
            else:
                # find closest valid diatonic pitch
                valid_neighbors = [p for p in range(max(60, curr_p - 4), min(82, curr_p + 5)) if (p % 12) in scale_pcs]
                if valid_neighbors:
                    curr_p = min(valid_neighbors, key=lambda p: abs(p - cand))
            mel_pitches.append(curr_p)

        # Final note: tonic or scale tone
        final_tonics = [p for p in range(60, 82) if p % 12 == tonic_pc]
        final_p = min(final_tonics, key=lambda p: abs(p - curr_p)) if final_tonics else 60
        mel_pitches.append(final_p)

        mel_dicts = []
        for s_idx, p in enumerate(mel_pitches):
            dur = random.choice(dur_choices) if s_idx < length - 1 else ("whole" if ts == "4/4" else "half")
            mel_dicts.append({"pitch": p, "duration": dur, "is_downbeat": (s_idx % 2 == 0)})

        record_test("3_random_diatonic", f"random_{idx+1:03d}_len{length}", k_str, mel_dicts, ts)

    # ==========================================
    # 4. NON-CHORD TONES (NCT) MELODIES
    # ==========================================
    nct_melodies = [
        # Passing note D between C and E (T triad C-E-G)
        ("passing_C_D_E", "C Major", [60, 62, 64], ["half", "half", "whole"]),
        # Passing D and F in C-D-E-F-G
        ("passing_C_D_E_F_G", "C Major", [60, 62, 64, 65, 67], ["quarter", "quarter", "quarter", "quarter", "whole"]),
        # Neighbor tone D in C-D-C
        ("neighbor_C_D_C", "C Major", [60, 62, 60], ["half", "half", "whole"]),
        # Upper neighbor F in E-F-E
        ("neighbor_E_F_E", "C Major", [64, 65, 64], ["half", "half", "whole"]),
        # Neighbor tone A in G-A-G
        ("neighbor_G_A_G", "C Major", [67, 69, 67], ["half", "half", "whole"]),
        # Downward passing F in G-F-E
        ("passing_down_G_F_E", "C Major", [67, 65, 64], ["half", "half", "whole"]),
        # Complete passing phrase C-D-E-F-G-F-E-D-C
        ("passing_full_phrase", "C Major", [60, 62, 64, 65, 67, 65, 64, 62, 60], ["quarter"] * 8 + ["whole"]),
        # Passing in G Major: G-A-B-C-D
        ("passing_G_A_B_C_D", "G Major", [67, 69, 71, 72, 74], ["quarter", "quarter", "quarter", "quarter", "whole"]),
    ]

    for name, k_str, pitches, durs in nct_melodies:
        mel = [{"pitch": p, "duration": d, "is_downbeat": (i % 2 == 0)} for i, (p, d) in enumerate(zip(pitches, durs))]
        record_test("4_non_chord_tones", name, k_str, mel, "4/4")

    # ==========================================
    # 5. CHROMATIC / ALTERED NOTES
    # ==========================================
    chromatic_melodies = [
        ("chromatic_F_sharp_in_C", "C Major", [60, 62, 64, 66, 67], ["half", "half", "half", "half", "whole"]),
        ("chromatic_B_flat_in_C", "C Major", [60, 64, 67, 70, 69], ["half", "half", "half", "half", "whole"]),
        ("chromatic_G_sharp_in_C", "C Major", [64, 65, 68, 69], ["half", "half", "half", "whole"]),
        ("chromatic_D_sharp_in_C", "C Major", [60, 63, 64, 62, 60], ["half", "half", "half", "half", "whole"]),
        ("chromatic_C_sharp_in_G", "G Major", [67, 69, 71, 73, 74], ["half", "half", "half", "half", "whole"]),
    ]

    for name, k_str, pitches, durs in chromatic_melodies:
        mel = [{"pitch": p, "duration": d, "is_downbeat": (i % 2 == 0)} for i, (p, d) in enumerate(zip(pitches, durs))]
        record_test("5_chromatic_altered", name, k_str, mel, "4/4")

    # Save evidence
    evidence_dir = Path("D:/aitraining/.redteam/evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    results_file = evidence_dir / "core_fuzz_results.json"
    results_file.write_text(json.dumps(all_records, indent=2, ensure_ascii=False), encoding="utf-8")

    stats_file = evidence_dir / "category_stats.json"
    stats_file.write_text(json.dumps(category_summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved raw results to: {results_file}")
    print(f"Saved stats to: {stats_file}")

    print("\n=== SUMMARY TABLE ===")
    print(f"{'Category':<25} | {'Total':<6} | {'Passed':<6} | {'Failed':<6} | {'Fail %':<7}")
    print("-" * 60)
    for cat, stats in category_summary.items():
        pct = (stats['failed'] / stats['total']) * 100 if stats['total'] else 0
        print(f"{cat:<25} | {stats['total']:<6} | {stats['passed']:<6} | {stats['failed']:<6} | {pct:>6.1f}%")


if __name__ == "__main__":
    main()
