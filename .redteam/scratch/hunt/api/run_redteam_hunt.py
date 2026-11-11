"""
Red-team API & Reliability Hunt Script for Brigade Harmony Engine
Target: http://127.0.0.1:8000
"""

import sys
import time
import json
import base64
import asyncio
import httpx
from typing import Any

BASE_URL = "http://127.0.0.1:8000"

# Standard test melody for baseline
SAMPLE_MELODY_4 = [
    {"pitch": 60, "duration": "half"},
    {"pitch": 62, "duration": "half"},
    {"pitch": 64, "duration": "half"},
    {"pitch": 60, "duration": "half"},
]

SAMPLE_MELODY_8 = [
    {"pitch": 60, "duration": "half"},
    {"pitch": 62, "duration": "half"},
    {"pitch": 64, "duration": "half"},
    {"pitch": 60, "duration": "half"},
    {"pitch": 64, "duration": "half"},
    {"pitch": 65, "duration": "half"},
    {"pitch": 67, "duration": "half"},
    {"pitch": 60, "duration": "half"},
]

def print_section(title: str):
    print(f"\n{'='*30}\n>>> {title}\n{'='*30}")

def test_endpoint(client: httpx.Client, method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{BASE_URL}{path}"
    try:
        t0 = time.perf_counter()
        resp = client.request(method, url, timeout=15.0, **kwargs)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        print(f"[{method}] {path} -> Status {resp.status_code} ({elapsed}ms)")
        return resp
    except Exception as e:
        print(f"[{method}] {path} -> EXCEPTION: {type(e).__name__}: {e}")
        raise

def run_all_tests():
    results = {}
    with httpx.Client(timeout=15.0) as client:
        # Check health
        h = test_endpoint(client, "GET", "/api/health")
        print("Health body:", h.text)

        # ---------------------------------------------------------
        # 1) VALIDATION TESTS
        # ---------------------------------------------------------
        print_section("1) VALIDATION TESTS")
        val_tests = {}

        # 1.1 max_plans: 0, -1, 101, 1e6
        for mp in [0, -1, 101, 1000000]:
            r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "max_plans": mp})
            val_tests[f"max_plans_{mp}"] = {"status": r.status_code, "body": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text}
            print(f"max_plans={mp} -> {r.status_code}: {r.text[:120]}")

        # 1.2 melody: 0 notes, 129 notes
        r_empty = client.post(f"{BASE_URL}/api/harmonize", json={"melody": []})
        val_tests["melody_0"] = {"status": r_empty.status_code, "body": r_empty.json()}
        print(f"melody_0 -> {r_empty.status_code}: {r_empty.text[:120]}")

        m_129 = [{"pitch": 60, "duration": "half"}] * 129
        r_129 = client.post(f"{BASE_URL}/api/harmonize", json={"melody": m_129})
        val_tests["melody_129"] = {"status": r_129.status_code, "body": r_129.json()}
        print(f"melody_129 -> {r_129.status_code}: {r_129.text[:120]}")

        # 1.3 pitch: -1, 128, 999
        for p in [-1, 128, 999]:
            r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": [{"pitch": p, "duration": "half"}]})
            val_tests[f"pitch_{p}"] = {"status": r.status_code, "body": r.json()}
            print(f"pitch={p} -> {r.status_code}: {r.text[:120]}")

        # 1.4 duration: "banana"
        r_dur = client.post(f"{BASE_URL}/api/harmonize", json={"melody": [{"pitch": 60, "duration": "banana"}]})
        val_tests["duration_banana"] = {"status": r_dur.status_code, "body": r_dur.json()}
        print(f"duration=banana -> {r_dur.status_code}: {r_dur.text[:120]}")

        # 1.5 time_signature: "7/8", "0/4", "4/0", "abc"
        # Note: "0/4" might hang the server if not careful, so test with small timeout
        for ts in ["7/8", "abc", "4/0"]:
            try:
                r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "time_signature": ts}, timeout=5.0)
                val_tests[f"time_sig_{ts}"] = {"status": r.status_code, "body": r.text[:200]}
                print(f"time_signature={ts} -> {r.status_code}: {r.text[:120]}")
            except Exception as e:
                val_tests[f"time_sig_{ts}"] = {"status": "TIMEOUT_OR_ERR", "error": str(e)}
                print(f"time_signature={ts} -> EXCEPTION: {e}")

        # Test 0/4 with separate try/except and 2s timeout
        try:
            r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "time_signature": "0/4"}, timeout=2.0)
            val_tests["time_sig_0_4"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"time_signature=0/4 -> {r.status_code}: {r.text[:120]}")
        except httpx.TimeoutException:
            val_tests["time_sig_0_4"] = {"status": "TIMEOUT", "error": "Hangs server thread in infinite loop"}
            print("time_signature=0/4 -> TIMEOUT (Infinite Loop DoS!)")
        except Exception as e:
            val_tests["time_sig_0_4"] = {"status": "ERR", "error": str(e)}
            print(f"time_signature=0/4 -> EXCEPTION: {e}")

        # 1.6 key tonic: "Z#", "Cb", "H"
        for ton in ["Z#", "Cb", "H"]:
            r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "key": {"tonic": ton, "mode": "Major"}})
            val_tests[f"tonic_{ton}"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"key.tonic={ton} -> {r.status_code}: {r.text[:120]}")

        # 1.7 mode: "MinorMelodic", "Alien", ""
        for m in ["MinorMelodic", "Alien", ""]:
            r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "key": {"tonic": "C", "mode": m}})
            val_tests[f"mode_{m}"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"key.mode='{m}' -> {r.status_code}: {r.text[:120]}")

        # 1.8 is_downbeat: string "false", "banana"
        r_db_str = client.post(f"{BASE_URL}/api/harmonize", json={"melody": [{"pitch": 60, "is_downbeat": "false"}]})
        val_tests["is_downbeat_false"] = {"status": r_db_str.status_code, "body": r_db_str.text[:200]}
        print(f"is_downbeat='false' -> {r_db_str.status_code}: {r_db_str.text[:120]}")

        r_db_banana = client.post(f"{BASE_URL}/api/harmonize", json={"melody": [{"pitch": 60, "is_downbeat": "banana"}]})
        val_tests["is_downbeat_banana"] = {"status": r_db_banana.status_code, "body": r_db_banana.text[:200]}
        print(f"is_downbeat='banana' -> {r_db_banana.status_code}: {r_db_banana.text[:120]}")

        # 1.9 extra fields
        r_extra = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "unexpected_payload_key": 99999})
        val_tests["extra_fields"] = {"status": r_extra.status_code, "body": r_extra.text[:200]}
        print(f"extra_fields -> {r_extra.status_code}: {r_extra.text[:120]}")

        # 1.10 null values
        r_null_melody = client.post(f"{BASE_URL}/api/harmonize", json={"melody": None})
        val_tests["null_melody"] = {"status": r_null_melody.status_code, "body": r_null_melody.text[:200]}
        print(f"null_melody -> {r_null_melody.status_code}: {r_null_melody.text[:120]}")

        r_null_pitch = client.post(f"{BASE_URL}/api/harmonize", json={"melody": [{"pitch": None}]})
        val_tests["null_pitch"] = {"status": r_null_pitch.status_code, "body": r_null_pitch.text[:200]}
        print(f"null_pitch -> {r_null_pitch.status_code}: {r_null_pitch.text[:120]}")

        r_null_key = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_4, "key": None})
        val_tests["null_key"] = {"status": r_null_key.status_code, "body": r_null_key.text[:200]}
        print(f"null_key -> {r_null_key.status_code}: {r_null_key.text[:120]}")

        results["1_validation"] = val_tests

        # ---------------------------------------------------------
        # 2) /api/grade TESTS
        # ---------------------------------------------------------
        print_section("2) /api/grade TESTS")
        grade_tests = {}

        sample_v = [
            {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48},
            {"soprano": 62, "alto": 59, "tenor": 55, "bass": 43},
        ]
        sample_c = ["T", "D"]

        # 2.1 chords missing, empty, longer, shorter
        # Missing
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": sample_v})
        grade_tests["chords_missing"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"chords missing -> {r.status_code}: {r.text[:120]}")

        # Empty
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": sample_v, "chords": []})
        grade_tests["chords_empty"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"chords empty -> {r.status_code}: {r.text[:120]}")

        # Longer
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": sample_v, "chords": ["T", "D", "T"]})
        grade_tests["chords_longer"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"chords longer -> {r.status_code}: {r.text[:120]}")

        # Shorter
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": sample_v, "chords": ["T"]})
        grade_tests["chords_shorter"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"chords shorter -> {r.status_code}: {r.text[:120]}")

        # 2.2 chord symbols: "V", "I", "IV", "Q", "T7"
        for sym in ["V", "I", "IV", "Q", "T7"]:
            r = client.post(f"{BASE_URL}/api/grade", json={"voicings": [sample_v[0]], "chords": [sym]})
            grade_tests[f"chord_symbol_{sym}"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"chord symbol '{sym}' -> {r.status_code}: {r.text[:120]}")

        # 2.3 voicings 0 / 1 / 5+ elements
        # 0
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": [], "chords": []})
        grade_tests["voicings_0"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"voicings 0 -> {r.status_code}: {r.text[:120]}")

        # 1
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": [sample_v[0]], "chords": ["T"]})
        grade_tests["voicings_1"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
        print(f"voicings 1 -> {r.status_code}: grade={(r.json().get('report', {}).get('grade') if r.status_code == 200 else 'N/A')}")

        # 5+ elements
        v_5 = [
            {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48},
            {"soprano": 62, "alto": 55, "tenor": 50, "bass": 43},
            {"soprano": 64, "alto": 55, "tenor": 52, "bass": 48},
            {"soprano": 65, "alto": 57, "tenor": 53, "bass": 45},
            {"soprano": 67, "alto": 59, "tenor": 55, "bass": 43},
            {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48},
        ]
        c_5 = ["T", "D", "T", "S", "D", "T"]
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": v_5, "chords": c_5})
        grade_tests["voicings_5_plus"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
        print(f"voicings 5+ -> {r.status_code}: grade={(r.json().get('report', {}).get('grade') if r.status_code == 200 else 'N/A')}")

        # 2.4 soprano < alto (voice crossing)
        v_cross = [
            {"soprano": 50, "alto": 65, "tenor": 55, "bass": 40},
            {"soprano": 52, "alto": 67, "tenor": 55, "bass": 43},
        ]
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": v_cross, "chords": ["T", "D"]})
        grade_tests["soprano_below_alto"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
        if r.status_code == 200:
            rep = r.json().get("report", {})
            print(f"soprano < alto -> {r.status_code}: grade={rep.get('grade')}, hard={rep.get('hard_violations_count')}, rules={[v['rule_id'] for v in rep.get('violations', [])]}")
        else:
            print(f"soprano < alto -> {r.status_code}: {r.text[:120]}")

        # 2.5 durations mismatched length (voicings=2, durations=1 or 4)
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": sample_v, "chords": sample_c, "durations": ["half"]})
        grade_tests["durations_shorter"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
        print(f"durations shorter -> {r.status_code}: {(r.text[:120] if r.status_code != 200 else 'grade=' + r.json().get('report', {}).get('grade'))}")

        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": sample_v, "chords": sample_c, "durations": ["half", "half", "quarter", "whole"]})
        grade_tests["durations_longer"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
        print(f"durations longer -> {r.status_code}: {(r.text[:120] if r.status_code != 200 else 'grade=' + r.json().get('report', {}).get('grade'))}")

        # 2.6 Bad solutions: Can we get 5 on bad solution?
        # A) Unison between adjacent voices (soprano == alto == 60)
        v_unison = [
            {"soprano": 60, "alto": 60, "tenor": 52, "bass": 48},
            {"soprano": 62, "alto": 62, "tenor": 55, "bass": 43},
        ]
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": v_unison, "chords": ["T", "D"]})
        if r.status_code == 200:
            rep = r.json().get("report", {})
            grade_tests["bad_unison"] = {"grade": rep.get("grade"), "violations": [v["rule_id"] for v in rep.get("violations", [])]}
            print(f"bad solution (unison) -> grade: {rep.get('grade')}, rules: {[v['rule_id'] for v in rep.get('violations', [])]}")
        else:
            grade_tests["bad_unison"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"bad solution (unison) -> {r.status_code}: {r.text[:120]}")

        # B) Missing third in tonic (C Major: C, E, G; voicing: C, G, C, C - notes: 60, 55, 48, 36; missing E)
        v_no_third = [
            {"soprano": 60, "alto": 55, "tenor": 48, "bass": 36},
            {"soprano": 62, "alto": 59, "tenor": 50, "bass": 43},
        ]
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": v_no_third, "chords": ["T", "D"]})
        if r.status_code == 200:
            rep = r.json().get("report", {})
            grade_tests["bad_no_third"] = {"grade": rep.get("grade"), "violations": [v["rule_id"] for v in rep.get("violations", [])]}
            print(f"bad solution (no third) -> grade: {rep.get('grade')}, rules: {[v['rule_id'] for v in rep.get('violations', [])]}")
        else:
            grade_tests["bad_no_third"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"bad solution (no third) -> {r.status_code}: {r.text[:120]}")

        # C) Parallel fifths: soprano and bass move by parallel fifths
        # V1: S=67(G4), A=64(E4), T=60(C4), B=60(C3) -> Wait, 67-60 is a fifth (G4-C4: tenor 60, soprano 67)
        # V2: S=69(A4), A=65(F4), T=62(D4), B=50(D3) -> S(69)-T(62) is a fifth (A4-D4). Parallel fifths between Soprano and Tenor!
        v_par_5 = [
            {"soprano": 67, "alto": 64, "tenor": 60, "bass": 48},
            {"soprano": 69, "alto": 65, "tenor": 62, "bass": 50},
        ]
        r = client.post(f"{BASE_URL}/api/grade", json={"voicings": v_par_5, "chords": ["T", "II"]})
        if r.status_code == 200:
            rep = r.json().get("report", {})
            grade_tests["bad_parallel_fifths"] = {"grade": rep.get("grade"), "violations": [v["rule_id"] for v in rep.get("violations", [])]}
            print(f"bad solution (parallel 5ths) -> grade: {rep.get('grade')}, rules: {[v['rule_id'] for v in rep.get('violations', [])]}")
        else:
            grade_tests["bad_parallel_fifths"] = {"status": r.status_code, "body": r.text[:200]}
            print(f"bad solution (parallel 5ths) -> {r.status_code}: {r.text[:120]}")

        results["2_grade"] = grade_tests

        # ---------------------------------------------------------
        # 3) /api/harmonize TESTS
        # ---------------------------------------------------------
        print_section("3) /api/harmonize TESTS")
        harm_tests = {}

        # 3.1 allow_secondary_dominants=false where plans only have DD
        # In C Major, a melody note F# (pitch 66) is an altered chromatic pitch belonging to DD (D-F#-A-C)
        melody_dd = [
            {"pitch": 60, "duration": "half"},
            {"pitch": 66, "duration": "half"}, # F#4 -> DD
            {"pitch": 67, "duration": "half"}, # G4 -> D / K64
            {"pitch": 60, "duration": "half"},
        ]
        r = client.post(f"{BASE_URL}/api/harmonize", json={
            "melody": melody_dd,
            "key": {"tonic": "C", "mode": "Major"},
            "allow_secondary_dominants": False
        })
        harm_tests["dd_disallowed"] = {"status": r.status_code, "body": r.json() if r.status_code == 200 else r.text[:200]}
        print(f"DD disallowed -> {r.status_code}: is_success={r.json().get('is_success')}, error={r.json().get('error')}")

        # 3.2 max_plans=1
        r = client.post(f"{BASE_URL}/api/harmonize", json={
            "melody": SAMPLE_MELODY_4,
            "max_plans": 1
        })
        harm_tests["max_plans_1"] = {"status": r.status_code, "candidates_count": len(r.json().get("candidates", [])) if r.status_code == 200 else 0}
        print(f"max_plans=1 -> {r.status_code}: candidates={len(r.json().get('candidates', []))}")

        # 3.3 128 notes: time, timeout
        melody_128 = [{"pitch": 60 + (i % 8), "duration": "quarter"} for i in range(128)]
        t0 = time.perf_counter()
        r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": melody_128, "max_plans": 5}, timeout=60.0)
        t_128 = round((time.perf_counter() - t0) * 1000, 2)
        harm_tests["128_notes"] = {"status": r.status_code, "latency_ms": t_128, "is_success": r.json().get("is_success") if r.status_code == 200 else False}
        print(f"128 notes -> {r.status_code} in {t_128}ms, is_success={r.json().get('is_success') if r.status_code == 200 else False}")

        # 3.4 empty melody
        r = client.post(f"{BASE_URL}/api/harmonize", json={"melody": []})
        harm_tests["empty_melody"] = {"status": r.status_code, "body": r.json() if r.status_code == 400 else r.text[:200]}
        print(f"empty melody -> {r.status_code}: {r.text[:120]}")

        # 3.5 determinism: two consecutive requests with identical parameters
        r1 = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_8, "max_plans": 20})
        r2 = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_8, "max_plans": 20})
        det1 = r1.json().get("candidates", [])
        det2 = r2.json().get("candidates", [])
        is_deterministic = (json.dumps(det1, sort_keys=True) == json.dumps(det2, sort_keys=True))
        harm_tests["determinism"] = {"is_deterministic": is_deterministic, "cand_count_1": len(det1), "cand_count_2": len(det2)}
        print(f"determinism -> matches: {is_deterministic}")

        results["3_harmonize"] = harm_tests

        # ---------------------------------------------------------
        # 3.6 Parallel requests concurrency check
        # ---------------------------------------------------------
        print("Testing parallel requests concurrency...")
        async def run_parallel():
            async with httpx.AsyncClient(timeout=30.0) as aclient:
                req1 = {"melody": SAMPLE_MELODY_4, "key": {"tonic": "C", "mode": "Major"}}
                req2 = {"melody": [{"pitch": 67, "duration": "half"}, {"pitch": 65, "duration": "half"}, {"pitch": 64, "duration": "half"}, {"pitch": 62, "duration": "half"}], "key": {"tonic": "G", "mode": "Major"}}
                t_p0 = time.perf_counter()
                res1, res2 = await asyncio.gather(
                    aclient.post(f"{BASE_URL}/api/harmonize", json=req1),
                    aclient.post(f"{BASE_URL}/api/harmonize", json=req2)
                )
                t_par = round((time.perf_counter() - t_p0) * 1000, 2)
                return res1, res2, t_par

        res1, res2, t_par = asyncio.run(run_parallel())
        p1_ok = (res1.status_code == 200 and res1.json().get("is_success"))
        p2_ok = (res2.status_code == 200 and res2.json().get("is_success"))
        harm_tests["concurrency"] = {"p1_ok": p1_ok, "p2_ok": p2_ok, "elapsed_ms": t_par}
        print(f"parallel requests -> P1 ok: {p1_ok}, P2 ok: {p2_ok} in {t_par}ms")

        # ---------------------------------------------------------
        # 4) /api/export/* TESTS
        # ---------------------------------------------------------
        print_section("4) /api/export/* TESTS")
        export_tests = {}

        # 4.1 Empty voicings
        r = client.post(f"{BASE_URL}/api/export/midi", json={"voicings": []})
        export_tests["midi_empty_voicings"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"export/midi empty voicings -> {r.status_code}: {r.text[:120]}")

        r = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": []})
        export_tests["xml_empty_voicings"] = {"status": r.status_code, "body": r.text[:200]}
        print(f"export/musicxml empty voicings -> {r.status_code}: {r.text[:120]}")

        # 4.2 durations shorter/longer
        r = client.post(f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "durations": ["half"]})
        export_tests["midi_durations_shorter"] = {"status": r.status_code, "size": len(r.content)}
        print(f"export/midi durations shorter -> {r.status_code}: {len(r.content)} bytes")

        r = client.post(f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "durations": ["half", "half", "quarter", "quarter"]})
        export_tests["midi_durations_longer"] = {"status": r.status_code, "size": len(r.content)}
        print(f"export/midi durations longer -> {r.status_code}: {len(r.content)} bytes")

        r = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "durations": ["half"]})
        export_tests["xml_durations_shorter"] = {"status": r.status_code, "size": len(r.content)}
        print(f"export/musicxml durations shorter -> {r.status_code}: {len(r.content)} bytes")

        r = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "durations": ["half", "half", "quarter", "quarter"]})
        export_tests["xml_durations_longer"] = {"status": r.status_code, "size": len(r.content)}
        print(f"export/musicxml durations longer -> {r.status_code}: {len(r.content)} bytes")

        # 4.3 Unknown chords
        r = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "chords": ["UNKNOWN_CHORD", "XYZ"]})
        export_tests["xml_unknown_chords"] = {"status": r.status_code, "size": len(r.content)}
        print(f"export/musicxml unknown chords -> {r.status_code}: {len(r.content)} bytes")

        # 4.4 Invalid time_signature: "0/4", "4/0", "abc"
        for ts in ["0/4", "4/0", "abc"]:
            try:
                r = client.post(f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "time_signature": ts}, timeout=2.0)
                export_tests[f"midi_ts_{ts}"] = {"status": r.status_code, "size": len(r.content), "body": r.text[:200]}
                print(f"export/midi ts={ts} -> {r.status_code}")
            except Exception as e:
                export_tests[f"midi_ts_{ts}"] = {"status": "ERR", "error": str(e)}
                print(f"export/midi ts={ts} -> EXCEPTION: {e}")

            try:
                r = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "time_signature": ts}, timeout=2.0)
                export_tests[f"xml_ts_{ts}"] = {"status": r.status_code, "size": len(r.content), "body": r.text[:200]}
                print(f"export/musicxml ts={ts} -> {r.status_code}")
            except Exception as e:
                export_tests[f"xml_ts_{ts}"] = {"status": "ERR", "error": str(e)}
                print(f"export/musicxml ts={ts} -> EXCEPTION: {e}")

        # 4.5 Validity of output files: Valid MIDI header, Valid MusicXML XML
        r_mid = client.post(f"{BASE_URL}/api/export/midi", json={"voicings": sample_v})
        is_midi_valid = r_mid.content.startswith(b"MThd")
        export_tests["midi_header_valid"] = is_midi_valid
        print(f"export/midi header valid (starts with MThd): {is_midi_valid}")

        r_xml = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "chords": sample_c})
        is_xml_valid = ("<score-partwise" in r_xml.text and "</score-partwise>" in r_xml.text)
        export_tests["xml_content_valid"] = is_xml_valid
        print(f"export/musicxml content valid (<score-partwise>): {is_xml_valid}")

        results["4_export"] = export_tests

        # ---------------------------------------------------------
        # 5) ERROR HANDLING & INFRASTRUCTURE
        # ---------------------------------------------------------
        print_section("5) ERROR HANDLING & INFRASTRUCTURE")
        infra_tests = {}

        # 5.1 404 JSON on unknown /api/*
        for path in ["/api/nonexistent", "/api/foo/bar/baz"]:
            r = client.get(f"{BASE_URL}{path}")
            is_json = r.headers.get("content-type", "").startswith("application/json")
            infra_tests[f"404_{path}"] = {"status": r.status_code, "is_json": is_json, "body": r.text}
            print(f"404 check {path} -> {r.status_code}, is_json={is_json}: {r.text[:120]}")

        # Non-api 404 check
        r_root_404 = client.get(f"{BASE_URL}/nonexistent-page-not-api")
        print(f"non-api 404 check -> {r_root_404.status_code}, type={r_root_404.headers.get('content-type')}")

        # 5.2 500 handler & stack trace leak check
        # Let's trigger a 500 via time_signature="4/0" on /api/export/musicxml or /api/harmonize
        r_500 = client.post(f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "time_signature": "4/0"})
        has_trace = ("Traceback" in r_500.text or "File \"" in r_500.text)
        infra_tests["500_handler"] = {
            "status": r_500.status_code,
            "has_traceback": has_trace,
            "body": r_500.json() if r_500.headers.get("content-type", "").startswith("application/json") else r_500.text,
            "headers": dict(r_500.headers)
        }
        print(f"500 handler check -> {r_500.status_code}, has_traceback={has_trace}: {r_500.text[:120]}")

        # 5.3 request_id in headers or response
        # Check standard 200, 400, 404, 500
        req_id_headers = {}
        for r_obj, label in [(h, "health_200"), (r_empty, "val_400"), (r, "404"), (r_500, "500")]:
            rid = r_obj.headers.get("x-request-id") or r_obj.headers.get("request-id")
            body_id = r_obj.json().get("request_id") if r_obj.headers.get("content-type", "").startswith("application/json") and isinstance(r_obj.json(), dict) else None
            req_id_headers[label] = {"header_rid": rid, "body_id": body_id}
            print(f"request_id check {label} -> Header: {rid}, Body: {body_id}")
        infra_tests["request_id"] = req_id_headers

        results["5_infrastructure"] = infra_tests

        # ---------------------------------------------------------
        # 6) SECURITY: CORS, BODY SIZE, PATH TRAVERSAL
        # ---------------------------------------------------------
        print_section("6) SECURITY: CORS, BODY SIZE, PATH TRAVERSAL")
        sec_tests = {}

        # 6.1 CORS check with evil.com
        r_cors_evil = client.options(
            f"{BASE_URL}/api/harmonize",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            }
        )
        sec_tests["cors_evil_options"] = {
            "status": r_cors_evil.status_code,
            "allow_origin": r_cors_evil.headers.get("access-control-allow-origin"),
            "headers": dict(r_cors_evil.headers)
        }
        print(f"CORS evil.com OPTIONS -> Status {r_cors_evil.status_code}, allow-origin: {r_cors_evil.headers.get('access-control-allow-origin')}")

        r_cors_evil_post = client.post(
            f"{BASE_URL}/api/harmonize",
            json={"melody": SAMPLE_MELODY_4},
            headers={"Origin": "http://evil.com"}
        )
        sec_tests["cors_evil_post"] = {
            "status": r_cors_evil_post.status_code,
            "allow_origin": r_cors_evil_post.headers.get("access-control-allow-origin"),
        }
        print(f"CORS evil.com POST -> Status {r_cors_evil_post.status_code}, allow-origin: {r_cors_evil_post.headers.get('access-control-allow-origin')}")

        # CORS check with valid localhost origin
        r_cors_good = client.post(
            f"{BASE_URL}/api/harmonize",
            json={"melody": SAMPLE_MELODY_4},
            headers={"Origin": "http://localhost:5173"}
        )
        sec_tests["cors_good_post"] = {
            "status": r_cors_good.status_code,
            "allow_origin": r_cors_good.headers.get("access-control-allow-origin"),
        }
        print(f"CORS localhost:5173 POST -> Status {r_cors_good.status_code}, allow-origin: {r_cors_good.headers.get('access-control-allow-origin')}")

        # 6.2 Body size limit
        # Try sending large body: 1MB, 5MB, 15MB
        for size_mb in [1, 5, 15]:
            large_str = "x" * (size_mb * 1024 * 1024)
            try:
                t0 = time.perf_counter()
                r_large = client.post(f"{BASE_URL}/api/parse-text", json={"text": large_str}, timeout=10.0)
                sec_tests[f"body_size_{size_mb}mb"] = {"status": r_large.status_code, "time_ms": round((time.perf_counter() - t0) * 1000, 2)}
                print(f"body size {size_mb}MB -> Status {r_large.status_code}")
            except Exception as e:
                sec_tests[f"body_size_{size_mb}mb"] = {"status": "ERR", "error": str(e)}
                print(f"body size {size_mb}MB -> EXCEPTION: {e}")

        # 6.3 Path traversal in /api/import-file
        for trav_filename in [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "../../../secret.xml",
            "test.xml\0evil.exe"
        ]:
            r_trav = client.post(
                f"{BASE_URL}/api/import-file",
                json={
                    "filename": trav_filename,
                    "xml_content": "<score-partwise version=\"3.1\"><part-list><score-part id=\"P1\"><part-name>Music</part-name></score-part></part-list><part id=\"P1\"><measure number=\"1\"><note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><voice>1</voice><staff>1</staff></note></measure></part></score-partwise>"
                }
            )
            sec_tests[f"traversal_{trav_filename}"] = {
                "status": r_trav.status_code,
                "resp_filename": r_trav.json().get("filename") if r_trav.status_code == 200 else None,
                "body": r_trav.text[:200]
            }
            print(f"path traversal '{trav_filename}' -> Status {r_trav.status_code}, returned filename: {r_trav.json().get('filename') if r_trav.status_code == 200 else r_trav.text[:120]}")

        results["6_security"] = sec_tests

        # ---------------------------------------------------------
        # 7) PERFORMANCE & DoS
        # ---------------------------------------------------------
        print_section("7) PERFORMANCE & DoS")
        perf_tests = {}

        # 8 notes
        t_list_8 = []
        for _ in range(3):
            t0 = time.perf_counter()
            r8 = client.post(f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_8, "max_plans": 20})
            t_list_8.append((time.perf_counter() - t0) * 1000)
        avg_8 = round(sum(t_list_8) / len(t_list_8), 2)
        perf_tests["latency_8_notes_ms"] = avg_8
        print(f"Latency 8 notes (avg of 3): {avg_8}ms")

        # 32 notes
        melody_32 = [{"pitch": 60 + (i % 7), "duration": "half"} for i in range(32)]
        t_list_32 = []
        for _ in range(3):
            t0 = time.perf_counter()
            r32 = client.post(f"{BASE_URL}/api/harmonize", json={"melody": melody_32, "max_plans": 10})
            t_list_32.append((time.perf_counter() - t0) * 1000)
        avg_32 = round(sum(t_list_32) / len(t_list_32), 2)
        perf_tests["latency_32_notes_ms"] = avg_32
        print(f"Latency 32 notes (avg of 3): {avg_32}ms")

        # 128 notes
        t_list_128 = []
        t0 = time.perf_counter()
        r128 = client.post(f"{BASE_URL}/api/harmonize", json={"melody": melody_128, "max_plans": 5}, timeout=60.0)
        t_128_total = round((time.perf_counter() - t0) * 1000, 2)
        perf_tests["latency_128_notes_ms"] = t_128_total
        print(f"Latency 128 notes: {t_128_total}ms, status: {r128.status_code}")

        # Check server health after 128 notes
        h_post = client.get(f"{BASE_URL}/api/health")
        perf_tests["server_healthy_after_128"] = (h_post.status_code == 200)
        print(f"Server health after 128 notes: {h_post.status_code}")

        results["7_performance"] = perf_tests

    # Save results to json
    with open("D:/aitraining/.redteam/scratch/hunt/api/raw_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nAll tests completed. Raw results saved to .redteam/scratch/hunt/api/raw_results.json")

if __name__ == "__main__":
    run_all_tests()
