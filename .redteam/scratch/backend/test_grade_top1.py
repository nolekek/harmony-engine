import json
import urllib.request

# 1. Harmonize default melody
payload = {
    "melody": [
        {"pitch": 64, "duration": "half"},
        {"pitch": 65, "duration": "half"},
        {"pitch": 67, "duration": "half"},
        {"pitch": 64, "duration": "half"},
        {"pitch": 62, "duration": "half"},
        {"pitch": 60, "duration": "whole"}
    ],
    "key": {"tonic": "C", "mode": "Major"},
    "time_signature": "4/4",
    "allow_extended_ranges": False,
    "allow_secondary_dominants": True,
    "max_plans": 50
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/harmonize",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

cand1 = data["candidates"][0]
print("Candidate 1 ID:", cand1["id"])
print("Chords:", cand1["chords"])
print("Voicings (SATB):")
for idx, v in enumerate(cand1["voicings"]):
    print(f"  Chord {idx} ({cand1['chords'][idx]}): S={v['soprano']}, A={v['alto']}, T={v['tenor']}, B={v['bass']}")

# 2. Grade Candidate 1 using /api/grade
grade_payload = {
    "voicings": cand1["voicings"],
    "key": {"tonic": "C", "mode": "Major"},
    "chords": cand1["chords"],
    "time_signature": "4/4",
    "durations": cand1["durations"],
    "allow_extended_ranges": False
}

req_grade = urllib.request.Request(
    "http://127.0.0.1:8000/api/grade",
    data=json.dumps(grade_payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req_grade) as resp_grade:
    grade_data = json.loads(resp_grade.read().decode("utf-8"))

rep = grade_data["report"]
print("\n--- GRADER REPORT FOR TOP-1 CANDIDATE ---")
print("Grade:", rep["grade"])
print("Verdict:", rep["summary_verdict"])
print("Is valid:", rep["is_valid"])
print("Hard violations:", rep["hard_violations_count"])
print("Soft violations:", rep["soft_violations_count"])
print("Violations detail:")
for v in rep["violations"]:
    print(f"  Measure {v['measure']}: [{v['severity']}] {v['rule_id']} - {v['message_ru']}")
