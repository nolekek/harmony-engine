"""
Red-team API & Reliability Hunt Script - Sections 4 through 7 (Resilient)
Target: http://127.0.0.1:8000
"""

import sys
import time
import json
import base64
import httpx

BASE_URL = "http://127.0.0.1:8000"

def print_section(title: str):
    print(f"\n{'='*30}\n>>> {title}\n{'='*30}", flush=True)

sample_v = [
    {"soprano": 60, "alto": 55, "tenor": 52, "bass": 48},
    {"soprano": 62, "alto": 59, "tenor": 55, "bass": 43},
]
sample_c = ["T", "D"]

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

def safe_request(client, method, url, **kwargs):
    for attempt in range(2):
        try:
            return client.request(method, url, **kwargs)
        except (httpx.ReadError, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            if attempt == 1:
                raise
            time.sleep(0.5)

def run():
    results = {}
    with httpx.Client(timeout=30.0) as client:
        # Check health
        h = safe_request(client, "GET", f"{BASE_URL}/api/health")
        print(f"Server health check: {h.status_code}", flush=True)

        # ---------------------------------------------------------
        # 4) /api/export/* TESTS
        # ---------------------------------------------------------
        print_section("4) /api/export/* TESTS")
        export_tests = {}

        # 4.1 Empty voicings
        r_mid_empty = safe_request(client, "POST", f"{BASE_URL}/api/export/midi", json={"voicings": []})
        export_tests["midi_empty_voicings"] = {
            "status": r_mid_empty.status_code,
            "bytes": len(r_mid_empty.content),
            "media_type": r_mid_empty.headers.get("content-type")
        }
        print(f"export/midi empty voicings -> {r_mid_empty.status_code}, {len(r_mid_empty.content)} bytes", flush=True)

        r_xml_empty = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": []})
        export_tests["xml_empty_voicings"] = {
            "status": r_xml_empty.status_code,
            "bytes": len(r_xml_empty.content),
            "media_type": r_xml_empty.headers.get("content-type")
        }
        print(f"export/musicxml empty voicings -> {r_xml_empty.status_code}, {len(r_xml_empty.content)} bytes", flush=True)

        # 4.2 durations shorter / longer
        r = safe_request(client, "POST", f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "durations": ["half"]})
        export_tests["midi_durations_shorter"] = {"status": r.status_code, "bytes": len(r.content)}
        print(f"export/midi durations shorter -> {r.status_code}, {len(r.content)} bytes", flush=True)

        r = safe_request(client, "POST", f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "durations": ["half", "half", "quarter", "quarter"]})
        export_tests["midi_durations_longer"] = {"status": r.status_code, "bytes": len(r.content)}
        print(f"export/midi durations longer -> {r.status_code}, {len(r.content)} bytes", flush=True)

        r = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "durations": ["half"]})
        export_tests["xml_durations_shorter"] = {"status": r.status_code, "bytes": len(r.content)}
        print(f"export/musicxml durations shorter -> {r.status_code}, {len(r.content)} bytes", flush=True)

        r = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "durations": ["half", "half", "quarter", "quarter"]})
        export_tests["xml_durations_longer"] = {"status": r.status_code, "bytes": len(r.content)}
        print(f"export/musicxml durations longer -> {r.status_code}, {len(r.content)} bytes", flush=True)

        # 4.3 Unknown / foreign chords in export
        r = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "chords": ["UNKNOWN_CHORD", "XYZ"]})
        export_tests["xml_foreign_chords"] = {"status": r.status_code, "bytes": len(r.content), "contains_chord": "UNKNOWN_CHORD" in r.text}
        print(f"export/musicxml foreign chords -> {r.status_code}, {len(r.content)} bytes, in_xml={'UNKNOWN_CHORD' in r.text}", flush=True)

        # 4.4 Invalid time_signature in export: "4/0", "abc"
        r_mid_ts_abc = safe_request(client, "POST", f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "time_signature": "abc"})
        export_tests["midi_ts_abc"] = {"status": r_mid_ts_abc.status_code, "bytes": len(r_mid_ts_abc.content)}
        print(f"export/midi time_signature='abc' -> {r_mid_ts_abc.status_code}", flush=True)

        r_xml_ts_abc = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "time_signature": "abc"})
        export_tests["xml_ts_abc"] = {"status": r_xml_ts_abc.status_code, "bytes": len(r_xml_ts_abc.content)}
        print(f"export/musicxml time_signature='abc' -> {r_xml_ts_abc.status_code}", flush=True)

        try:
            r_mid_ts_40 = safe_request(client, "POST", f"{BASE_URL}/api/export/midi", json={"voicings": sample_v, "time_signature": "4/0"})
            export_tests["midi_ts_4_0"] = {"status": r_mid_ts_40.status_code, "body": r_mid_ts_40.text[:150]}
            print(f"export/midi time_signature='4/0' -> {r_mid_ts_40.status_code}", flush=True)
        except Exception as e:
            export_tests["midi_ts_4_0"] = {"status": "500_OR_RESET", "error": str(e)}
            print(f"export/midi time_signature='4/0' -> EXCEPTION: {e}", flush=True)

        try:
            r_xml_ts_40 = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "time_signature": "4/0"})
            export_tests["xml_ts_4_0"] = {"status": r_xml_ts_40.status_code, "body": r_xml_ts_40.text[:150]}
            print(f"export/musicxml time_signature='4/0' -> {r_xml_ts_40.status_code}", flush=True)
        except Exception as e:
            export_tests["xml_ts_4_0"] = {"status": "500_OR_RESET", "error": str(e)}
            print(f"export/musicxml time_signature='4/0' -> EXCEPTION: {e}", flush=True)

        # 4.5 File validity: MusicXML schema/parse and MIDI format check
        r_mid_std = safe_request(client, "POST", f"{BASE_URL}/api/export/midi", json={"voicings": sample_v})
        is_midi_valid = r_mid_std.content.startswith(b"MThd") and len(r_mid_std.content) > 20
        export_tests["midi_valid_file"] = {"valid": is_midi_valid, "size": len(r_mid_std.content)}
        print(f"MIDI valid format (starts with MThd): {is_midi_valid}", flush=True)

        r_xml_std = safe_request(client, "POST", f"{BASE_URL}/api/export/musicxml", json={"voicings": sample_v, "chords": sample_c})
        import xml.etree.ElementTree as ET
        xml_parse_ok = False
        try:
            ET.fromstring(r_xml_std.content)
            xml_parse_ok = True
        except Exception as e:
            xml_parse_ok = False
        export_tests["musicxml_valid_xml"] = {"valid": xml_parse_ok, "has_score_partwise": "<score-partwise" in r_xml_std.text}
        print(f"MusicXML valid XML parse: {xml_parse_ok}", flush=True)

        results["4_export"] = export_tests

        # ---------------------------------------------------------
        # 5) ERROR HANDLING & INFRASTRUCTURE
        # ---------------------------------------------------------
        print_section("5) ERROR HANDLING & INFRASTRUCTURE")
        infra_tests = {}

        # 5.1 404 JSON on unknown /api/*
        for path in ["/api/nonexistent", "/api/v1/invalid", "/api/test/123"]:
            r_404 = safe_request(client, "GET", f"{BASE_URL}{path}")
            is_json = r_404.headers.get("content-type", "").startswith("application/json")
            infra_tests[f"404_{path}"] = {"status": r_404.status_code, "is_json": is_json, "body": r_404.text}
            print(f"404 check {path} -> Status {r_404.status_code}, is_json={is_json}: {r_404.text.strip()}", flush=True)

        # 5.2 500 handler & stack trace leak check
        # Check an endpoint with 500
        try:
            r_500 = safe_request(client, "POST", f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_8[:4], "time_signature": "4/0"})
            has_trace = any(term in r_500.text.lower() for term in ["traceback", "file \"", "line ", "zerodivisionerror"])
            has_error_id = "error_id" in r_500.json() if r_500.headers.get("content-type", "").startswith("application/json") else False
            infra_tests["500_handler"] = {
                "status": r_500.status_code,
                "has_traceback_leak": has_trace,
                "has_error_id": has_error_id,
                "body": r_500.text[:200]
            }
            print(f"500 handler check -> Status {r_500.status_code}, traceback leaked: {has_trace}, has error_id: {has_error_id}, body: {r_500.text.strip()}", flush=True)
        except Exception as e:
            infra_tests["500_handler"] = {"status": "ERR", "error": str(e)}
            print(f"500 handler check -> EXCEPTION: {e}", flush=True)

        # 5.3 request_id in headers or response
        req_id_results = {}
        endpoints_to_check = [
            ("health_200", "GET", "/api/health", None),
            ("harmonize_400", "POST", "/api/harmonize", {"melody": []}),
            ("unknown_404", "GET", "/api/unknown_endpoint", None),
        ]
        for name, m, p, pl in endpoints_to_check:
            resp = safe_request(client, m, f"{BASE_URL}{p}", json=pl if pl else None)
            h_rid = resp.headers.get("x-request-id") or resp.headers.get("request-id")
            body_json = resp.json() if resp.headers.get("content-type", "").startswith("application/json") and isinstance(resp.json(), dict) else {}
            b_rid = body_json.get("request_id") or body_json.get("x-request-id")
            req_id_results[name] = {"header_request_id": h_rid, "body_request_id": b_rid, "body_error_id": body_json.get("error_id")}
            print(f"request_id on {name} -> Header: {h_rid}, Body request_id: {b_rid}, Body error_id: {body_json.get('error_id')}", flush=True)
        infra_tests["request_id_audit"] = req_id_results

        results["5_infrastructure"] = infra_tests

        # ---------------------------------------------------------
        # 6) SECURITY: CORS, BODY SIZE, PATH TRAVERSAL
        # ---------------------------------------------------------
        print_section("6) SECURITY: CORS, BODY SIZE, PATH TRAVERSAL")
        sec_tests = {}

        # 6.1 CORS check with evil.com
        r_cors_evil = safe_request(
            client,
            "OPTIONS",
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
        }
        print(f"CORS OPTIONS with Origin: evil.com -> Status {r_cors_evil.status_code}, Access-Control-Allow-Origin: {r_cors_evil.headers.get('access-control-allow-origin')}", flush=True)

        r_cors_evil_post = safe_request(
            client,
            "POST",
            f"{BASE_URL}/api/harmonize",
            json={"melody": SAMPLE_MELODY_8[:4]},
            headers={"Origin": "http://evil.com"}
        )
        sec_tests["cors_evil_post"] = {
            "status": r_cors_evil_post.status_code,
            "allow_origin": r_cors_evil_post.headers.get("access-control-allow-origin"),
        }
        print(f"CORS POST with Origin: evil.com -> Status {r_cors_evil_post.status_code}, Access-Control-Allow-Origin: {r_cors_evil_post.headers.get('access-control-allow-origin')}", flush=True)

        # Valid Origin check
        r_cors_good = safe_request(
            client,
            "POST",
            f"{BASE_URL}/api/harmonize",
            json={"melody": SAMPLE_MELODY_8[:4]},
            headers={"Origin": "http://localhost:5173"}
        )
        sec_tests["cors_localhost_5173"] = {
            "status": r_cors_good.status_code,
            "allow_origin": r_cors_good.headers.get("access-control-allow-origin"),
        }
        print(f"CORS POST with Origin: http://localhost:5173 -> Access-Control-Allow-Origin: {r_cors_good.headers.get('access-control-allow-origin')}", flush=True)

        # 6.2 Body size limit
        for size_mb in [1, 5, 20]:
            large_text = "C4 " * (size_mb * 200000)
            try:
                t0 = time.perf_counter()
                r_bs = safe_request(client, "POST", f"{BASE_URL}/api/parse-text", json={"text": large_text})
                sec_tests[f"body_size_{size_mb}mb"] = {"status": r_bs.status_code, "time_ms": round((time.perf_counter() - t0) * 1000, 2)}
                print(f"Body size {size_mb}MB -> Status {r_bs.status_code} in {round((time.perf_counter() - t0) * 1000, 2)}ms", flush=True)
            except Exception as e:
                sec_tests[f"body_size_{size_mb}mb"] = {"status": "ERR", "error": str(e)}
                print(f"Body size {size_mb}MB -> EXCEPTION: {e}", flush=True)

        # 6.3 Path traversal in /api/import-file (filename)
        traversal_payloads = [
            ("../../../../etc/passwd", "UNIX traversal"),
            ("..\\..\\..\\windows\\win.ini", "Windows traversal"),
            ("C:\\Windows\\System32\\drivers\\etc\\hosts", "Absolute Windows path"),
            ("safe_name.xml\0evil.exe", "Null-byte injection"),
        ]
        trav_results = {}
        for fn, desc in traversal_payloads:
            r_trav = safe_request(
                client,
                "POST",
                f"{BASE_URL}/api/import-file",
                json={
                    "filename": fn,
                    "xml_content": "<score-partwise version=\"3.1\"><part-list><score-part id=\"P1\"><part-name>Music</part-name></score-part></part-list><part id=\"P1\"><measure number=\"1\"><note><pitch><step>C</step><octave>4</octave></pitch><duration>2</duration><voice>1</voice><staff>1</staff></note></measure></part></score-partwise>"
                }
            )
            trav_results[fn] = {
                "status": r_trav.status_code,
                "returned_filename": r_trav.json().get("filename") if r_trav.status_code == 200 else None,
                "body": r_trav.text[:150]
            }
            print(f"Path traversal check '{fn}' ({desc}) -> Status {r_trav.status_code}, Returned filename: {r_trav.json().get('filename') if r_trav.status_code == 200 else r_trav.text[:80]}", flush=True)
        sec_tests["path_traversal"] = trav_results

        results["6_security"] = sec_tests

        # ---------------------------------------------------------
        # 7) PERFORMANCE & DoS
        # ---------------------------------------------------------
        print_section("7) PERFORMANCE & DoS")
        perf_tests = {}

        # 8 notes latency
        lat_8 = []
        for _ in range(3):
            t0 = time.perf_counter()
            r8 = safe_request(client, "POST", f"{BASE_URL}/api/harmonize", json={"melody": SAMPLE_MELODY_8, "max_plans": 20})
            lat_8.append((time.perf_counter() - t0) * 1000)
        avg_8 = round(sum(lat_8) / len(lat_8), 2)
        server_lat_8 = r8.json().get("latency_ms") if r8.status_code == 200 else None
        perf_tests["notes_8"] = {"http_avg_ms": avg_8, "server_latency_ms": server_lat_8}
        print(f"Latency 8 notes: HTTP roundtrip {avg_8}ms, server reported {server_lat_8}ms", flush=True)

        # 32 notes latency
        melody_32 = [{"pitch": 60 + (i % 7), "duration": "half"} for i in range(32)]
        lat_32 = []
        for _ in range(3):
            t0 = time.perf_counter()
            r32 = safe_request(client, "POST", f"{BASE_URL}/api/harmonize", json={"melody": melody_32, "max_plans": 10})
            lat_32.append((time.perf_counter() - t0) * 1000)
        avg_32 = round(sum(lat_32) / len(lat_32), 2)
        server_lat_32 = r32.json().get("latency_ms") if r32.status_code == 200 else None
        perf_tests["notes_32"] = {"http_avg_ms": avg_32, "server_latency_ms": server_lat_32}
        print(f"Latency 32 notes: HTTP roundtrip {avg_32}ms, server reported {server_lat_32}ms", flush=True)

        # 128 notes latency
        melody_128 = [{"pitch": 60 + (i % 7), "duration": "half"} for i in range(128)]
        t0 = time.perf_counter()
        r128 = safe_request(client, "POST", f"{BASE_URL}/api/harmonize", json={"melody": melody_128, "max_plans": 5})
        http_128 = round((time.perf_counter() - t0) * 1000, 2)
        server_lat_128 = r128.json().get("latency_ms") if r128.status_code == 200 else None
        perf_tests["notes_128"] = {
            "http_roundtrip_ms": http_128,
            "server_latency_ms": server_lat_128,
            "status": r128.status_code,
            "is_success": r128.json().get("is_success") if r128.status_code == 200 else False
        }
        print(f"Latency 128 notes: HTTP roundtrip {http_128}ms, server reported {server_lat_128}ms, is_success={r128.json().get('is_success') if r128.status_code == 200 else False}", flush=True)

        # Verify server healthy after 128 notes
        h_end = safe_request(client, "GET", f"{BASE_URL}/api/health")
        perf_tests["server_healthy_after_128"] = (h_end.status_code == 200)
        print(f"Server health check after 128 notes: Status {h_end.status_code}", flush=True)

        results["7_performance"] = perf_tests

    # Save to json
    with open("D:/aitraining/.redteam/scratch/hunt/api/sections_4_7_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nSections 4-7 tests finished successfully!", flush=True)

if __name__ == "__main__":
    run()
