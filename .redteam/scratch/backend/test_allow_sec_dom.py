import json
import urllib.request

# Melody with F# (pitch 66) in C Major: E4(64), F#4(66), G4(67), E4(64), D4(62), C4(60)
payload = {
    "melody": [
        {"pitch": 64, "duration": "half"},
        {"pitch": 66, "duration": "half"},
        {"pitch": 67, "duration": "half"},
        {"pitch": 64, "duration": "half"},
        {"pitch": 62, "duration": "half"},
        {"pitch": 60, "duration": "whole"}
    ],
    "key": {"tonic": "C", "mode": "Major"},
    "time_signature": "4/4",
    "allow_extended_ranges": False,
    "allow_secondary_dominants": False,
    "max_plans": 50
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/harmonize",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print("is_success:", data.get("is_success"))
    print("Candidates count:", len(data.get("candidates", [])))
    for c in data.get("candidates", []):
        print("Candidate chords:", c.get("chords"))
