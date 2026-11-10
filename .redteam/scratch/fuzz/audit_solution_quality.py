"""
Audit Solution Quality:
Examines all successful solutions from core and API for:
- Adjacent voice unisons (T=B, S=A, A=T)
- Voice overlapping
- Voice crossing
- Parallel 5ths/8ves/unisons
- Hidden 5ths/8ves
- Range violations
- Incomplete triads / missing chord factors
- Grader internal contradiction: calls POST /api/grade on the solver's solutions.
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
from src.harmony.core.types import Key, Voicing, to_satb, parse_key
from src.harmony.rules.doubling import get_triad_tones
from src.harmony.rules.voice_leading import (
    check_parallel_fifths_and_octaves,
    check_contrary_fifths_and_octaves,
    check_hidden_fifths_and_octaves,
    check_voice_overlapping,
    check_unisons,
    check_melodic_intervals,
)
from src.harmony.rules.spacing import check_voice_ranges, check_voice_crossing, check_texture_spacing

API_GRADE_URL = "http://127.0.0.1:8000/api/grade"
API_HARMONIZE_URL = "http://127.0.0.1:8000/api/harmonize"


def analyze_voicings_manually(voicings: list[dict[str, int]], chords: list[str], key_str: str) -> dict[str, Any]:
    n = len(voicings)
    parsed_key = Key.parse(key_str)
    tonic_pc, mode = parse_key(parsed_key)

    v_objects = [
        Voicing(soprano=v["soprano"], alto=v["alto"], tenor=v["tenor"], bass=v["bass"])
        for v in voicings
    ]

    unisons_tb = []
    unisons_sa = []
    unisons_at = []
    crossings = []
    overlappings = []
    parallel_5_8 = []
    contrary_5_8 = []
    hidden_5_8 = []
    range_violations = []
    incomplete_triads = []

    for t in range(n):
        v = v_objects[t]
        s, a, ten, b = v.s, v.a, v.t, v.b

        # Unisons
        if ten == b:
            unisons_tb.append({"step": t, "pitch": ten, "chord": chords[t] if t < len(chords) else ""})
        if s == a:
            unisons_sa.append({"step": t, "pitch": s, "chord": chords[t] if t < len(chords) else ""})
        if a == ten:
            unisons_at.append({"step": t, "pitch": a, "chord": chords[t] if t < len(chords) else ""})

        # Static range check
        rv = check_voice_ranges(v)
        if rv:
            range_violations.extend([{"step": t, "desc": r.description} for r in rv])

        # Voice crossing
        cv = check_voice_crossing(v)
        if cv:
            crossings.extend([{"step": t, "desc": r.description} for r in cv])

        # Triad factor completeness
        if t < len(chords):
            c_fn = chords[t]
            if c_fn in ("T", "S", "D", "t", "s", "d"):
                r, th, fi = get_triad_tones(c_fn, tonic_pc, mode)
                pcs = {s % 12, a % 12, ten % 12, b % 12}
                if fi not in pcs:
                    incomplete_triads.append({
                        "step": t,
                        "chord": c_fn,
                        "missing": "fifth",
                        "present_pcs": list(pcs),
                    })
                if th not in pcs:
                    incomplete_triads.append({
                        "step": t,
                        "chord": c_fn,
                        "missing": "third",
                        "present_pcs": list(pcs),
                    })

        # Transition checks
        if t > 0:
            prev_v = v_objects[t - 1]
            # Parallel 5/8
            pv = check_parallel_fifths_and_octaves(prev_v, v)
            if pv:
                parallel_5_8.extend([{"step": t, "desc": r.description} for r in pv])
            # Contrary 5/8
            cov = check_contrary_fifths_and_octaves(prev_v, v)
            if cov:
                contrary_5_8.extend([{"step": t, "desc": r.description} for r in cov])
            # Hidden 5/8
            hv = check_hidden_fifths_and_octaves(prev_v, v)
            if hv:
                hidden_5_8.extend([{"step": t, "desc": r.description} for r in hv])
            # Overlapping
            ov = check_voice_overlapping(prev_v, v)
            if ov:
                overlappings.extend([{"step": t, "desc": r.description} for r in ov])

    return {
        "unisons_tb_count": len(unisons_tb),
        "unisons_tb": unisons_tb,
        "unisons_sa_count": len(unisons_sa),
        "unisons_sa": unisons_sa,
        "unisons_at_count": len(unisons_at),
        "unisons_at": unisons_at,
        "total_unisons": len(unisons_tb) + len(unisons_sa) + len(unisons_at),
        "range_violations_count": len(range_violations),
        "range_violations": range_violations,
        "voice_crossings_count": len(crossings),
        "voice_crossings": crossings,
        "voice_overlappings_count": len(overlappings),
        "voice_overlappings": overlappings,
        "parallel_5_8_count": len(parallel_5_8),
        "parallel_5_8": parallel_5_8,
        "contrary_5_8_count": len(contrary_5_8),
        "contrary_5_8": contrary_5_8,
        "hidden_5_8_count": len(hidden_5_8),
        "hidden_5_8": hidden_5_8,
        "incomplete_triads_count": len(incomplete_triads),
        "incomplete_triads": incomplete_triads,
    }


def call_api_grade(voicings: list[dict[str, int]], key_str: str, time_signature: str = "4/4") -> dict[str, Any]:
    parsed_key = Key.parse(key_str)
    req_body = {
        "voicings": voicings,
        "key": {"tonic": parsed_key.tonic, "mode": parsed_key.mode},
        "time_signature": time_signature,
    }
    req = urllib.request.Request(
        API_GRADE_URL,
        data=json.dumps(req_body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def main():
    print("=== RUNNING SOLUTION QUALITY AUDIT & GRADER CONTRADICTION CHECK ===")

    # Load results from core fuzzing
    evidence_dir = Path("D:/aitraining/.redteam/evidence")
    fuzz_file = evidence_dir / "core_fuzz_results.json"
    if not fuzz_file.exists():
        print("Error: core_fuzz_results.json not found!")
        return

    fuzz_data = json.loads(fuzz_file.read_text(encoding="utf-8"))
    successful_cases = [r for r in fuzz_data if r["result"]["is_success"]]
    print(f"Loaded {len(fuzz_data)} fuzz tests, {len(successful_cases)} are successful.")

    # Also include the default melody with max_plans=50 (which passes!)
    default_req = {
        "melody": [
            {"pitch": 64, "duration": "half", "is_downbeat": True},
            {"pitch": 65, "duration": "half", "is_downbeat": False},
            {"pitch": 67, "duration": "half", "is_downbeat": True},
            {"pitch": 64, "duration": "half", "is_downbeat": False},
            {"pitch": 62, "duration": "half", "is_downbeat": True},
            {"pitch": 60, "duration": "whole", "is_downbeat": False},
        ],
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "allow_secondary_dominants": True,
        "allow_extended_ranges": False,
        "max_plans": 50,
    }
    req = urllib.request.Request(
        API_HARMONIZE_URL,
        data=json.dumps(default_req).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        def_res = json.loads(resp.read().decode("utf-8"))

    audit_records = []

    # Audit default melody top-3 candidates
    print("\nAuditing default melody candidates from API:")
    for cand in def_res.get("candidates", []):
        cand_id = cand["id"]
        voicings = cand["voicings"]
        chords = cand["chords"]
        analysis = analyze_voicings_manually(voicings, chords, "C Major")
        grade_res = call_api_grade(voicings, "C Major")

        rec = {
            "source": "api_default_melody",
            "name": f"default_melody_{cand_id}",
            "key": "C Major",
            "rank": cand["rank"],
            "cost": cand["cost"],
            "chords": chords,
            "voicings": voicings,
            "analysis": analysis,
            "grade_report": grade_res,
        }
        audit_records.append(rec)
        print(f"  [{cand_id}] cost={cand['cost']}, TB_unisons={analysis['unisons_tb_count']}, SA_unisons={analysis['unisons_sa_count']}, incomplete={analysis['incomplete_triads_count']}, grader={grade_res.get('grade')}, hard_viols={grade_res.get('hard_violations_count')}")

    # Now audit a sample of 30 successful cases from core fuzzing
    print("\nAuditing successful fuzz cases via API /api/harmonize:")
    for sc in successful_cases[:35]:
        mel_input = [
            {"pitch": p, "duration": d, "is_downbeat": (i % 2 == 0)}
            for i, (p, d) in enumerate(zip(sc["pitches"], sc["durations"]))
        ]
        k_str = sc["key"]
        parsed_k = Key.parse(k_str)

        api_payload = {
            "melody": mel_input,
            "key": {"tonic": parsed_k.tonic, "mode": parsed_k.mode},
            "time_signature": sc["time_signature"],
            "allow_secondary_dominants": True,
            "allow_extended_ranges": False,
            "max_plans": 50,
        }

        try:
            r = urllib.request.Request(
                API_HARMONIZE_URL,
                data=json.dumps(api_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(r) as res_p:
                api_out = json.loads(res_p.read().decode("utf-8"))

            for cand in api_out.get("candidates", []):
                v_list = cand["voicings"]
                c_list = cand["chords"]
                an = analyze_voicings_manually(v_list, c_list, k_str)
                gr = call_api_grade(v_list, k_str, sc["time_signature"])

                audit_records.append({
                    "source": "fuzz_api",
                    "name": sc["name"],
                    "key": k_str,
                    "rank": cand["rank"],
                    "cost": cand["cost"],
                    "chords": c_list,
                    "voicings": v_list,
                    "analysis": an,
                    "grade_report": gr,
                })
        except Exception as e:
            print(f"  Error on {sc['name']}: {e}")

    # Aggregate statistics
    total_solutions = len(audit_records)
    with_tb_unison = sum(1 for r in audit_records if r["analysis"]["unisons_tb_count"] > 0)
    with_sa_unison = sum(1 for r in audit_records if r["analysis"]["unisons_sa_count"] > 0)
    with_at_unison = sum(1 for r in audit_records if r["analysis"]["unisons_at_count"] > 0)
    with_incomplete = sum(1 for r in audit_records if r["analysis"]["incomplete_triads_count"] > 0)
    with_hidden_5_8 = sum(1 for r in audit_records if r["analysis"]["hidden_5_8_count"] > 0)
    with_overlapping = sum(1 for r in audit_records if r["analysis"]["voice_overlappings_count"] > 0)
    with_crossing = sum(1 for r in audit_records if r["analysis"]["voice_crossings_count"] > 0)
    with_parallel = sum(1 for r in audit_records if r["analysis"]["parallel_5_8_count"] > 0)

    # Grader contradiction statistics
    # Solver claims 0 hard violations. How many does grader find?
    grader_grades = {}
    grader_found_hard = 0
    hard_rules_flagged_by_grader = {}

    for r in audit_records:
        gr = r["grade_report"]
        rep = gr.get("report", gr) if isinstance(gr, dict) else {}
        grade_str = rep.get("grade", "Unknown")
        grader_grades[grade_str] = grader_grades.get(grade_str, 0) + 1

        hard_c = rep.get("hard_violations_count", 0)
        if hard_c > 0:
            grader_found_hard += 1

        for v in rep.get("violations", []):
            if v.get("severity") == "hard_gate":
                rid = v.get("rule_id", "UNKNOWN")
                hard_rules_flagged_by_grader[rid] = hard_rules_flagged_by_grader.get(rid, 0) + 1

    summary = {
        "total_audited_solutions": total_solutions,
        "defect_counts": {
            "unisons_tenor_bass": with_tb_unison,
            "unisons_soprano_alto": with_sa_unison,
            "unisons_alto_tenor": with_at_unison,
            "incomplete_triads": with_incomplete,
            "hidden_fifths_octaves": with_hidden_5_8,
            "voice_overlapping": with_overlapping,
            "voice_crossing": with_crossing,
            "parallel_fifths_octaves": with_parallel,
        },
        "defect_percentages": {
            "unisons_tenor_bass_pct": round(with_tb_unison / total_solutions * 100, 1) if total_solutions else 0,
            "unisons_soprano_alto_pct": round(with_sa_unison / total_solutions * 100, 1) if total_solutions else 0,
            "incomplete_triads_pct": round(with_incomplete / total_solutions * 100, 1) if total_solutions else 0,
            "hidden_5_8_pct": round(with_hidden_5_8 / total_solutions * 100, 1) if total_solutions else 0,
            "voice_overlapping_pct": round(with_overlapping / total_solutions * 100, 1) if total_solutions else 0,
        },
        "grader_verdicts": grader_grades,
        "grader_found_hard_violations_count": grader_found_hard,
        "grader_found_hard_pct": round(grader_found_hard / total_solutions * 100, 1) if total_solutions else 0,
        "grader_hard_rules_flagged": hard_rules_flagged_by_grader,
    }

    out_file = evidence_dir / "quality_audit.json"
    full_output = {
        "summary": summary,
        "solutions": audit_records,
    }
    out_file.write_text(json.dumps(full_output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAudit complete! Saved to: {out_file}")

    print("\n=== QUALITY AUDIT SUMMARY ===")
    print(f"Total Audited Solutions: {total_solutions}")
    print(f"Tenor=Bass Unisons:      {with_tb_unison} ({summary['defect_percentages']['unisons_tenor_bass_pct']}%)")
    print(f"Soprano=Alto Unisons:    {with_sa_unison} ({summary['defect_percentages']['unisons_soprano_alto_pct']}%)")
    print(f"Incomplete Triads:       {with_incomplete} ({summary['defect_percentages']['incomplete_triads_pct']}%)")
    print(f"Hidden 5ths/8ves:        {with_hidden_5_8} ({summary['defect_percentages']['hidden_5_8_pct']}%)")
    print(f"Voice Overlappings:      {with_overlapping} ({summary['defect_percentages']['voice_overlapping_pct']}%)")
    print(f"Voice Crossings:         {with_crossing}")
    print(f"Parallel 5ths/8ves:      {with_parallel}")
    print("\n=== GRADER VS SOLVER CONTRADICTION ===")
    print(f"Solutions Grader Failed (found HARD violations): {grader_found_hard} ({summary['grader_found_hard_pct']}%)")
    print("Grader Grade Distribution:", grader_grades)
    print("Hard rules flagged by Grader in Solver solutions:", hard_rules_flagged_by_grader)


if __name__ == "__main__":
    main()
