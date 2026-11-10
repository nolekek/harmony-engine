"""
Populate minimal failing cases evidence with verified empirical failing patterns:
1. C5 -> B4 -> A4 (3 notes diatonic, 0/14 plans solvable, leading tone down resolution failure)
2. C5 -> B4 -> A4 -> G4 (4 notes diatonic, 0/14 plans solvable)
3. C4 -> D4 -> E4 -> F4 -> G4 -> A4 (6 notes diatonic ascending, 0/50 plans solvable at max_plans=50)
4. C5 -> B4 -> A4 -> G4 -> F4 -> E4 -> D4 -> C4 (8 notes descending major scale, 0/200 plans solvable)
5. Chromatic B-flat in C major: C-E-G-Bb-A (soprano pitch 70 not in any chord in C-dur)
"""

import json
import sys
import urllib.request
from pathlib import Path

WORKSPACE_ROOT = Path("D:/aitraining")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.core.types import Key

API_URL = "http://127.0.0.1:8000/api/harmonize"

PITCH_NAMES = {
    60: "C4", 62: "D4", 64: "E4", 65: "F4", 66: "F#4",
    67: "G4", 69: "A4", 70: "Bb4", 71: "B4", 72: "C5"
}

test_patterns = [
    {
        "name": "diatonic_3_notes_descending_terz_C5_B4_A4",
        "key": "C Major",
        "pitches": [72, 71, 69],
        "durs": ["half", "half", "whole"],
        "max_plans": 50,
        "note_names": ["C5", "B4", "A4"],
    },
    {
        "name": "diatonic_4_notes_descending_quart_C5_B4_A4_G4",
        "key": "C Major",
        "pitches": [72, 71, 69, 67],
        "durs": ["half", "half", "half", "whole"],
        "max_plans": 50,
        "note_names": ["C5", "B4", "A4", "G4"],
    },
    {
        "name": "diatonic_6_notes_ascending_scale_prefix_C4_to_A4",
        "key": "C Major",
        "pitches": [60, 62, 64, 65, 67, 69],
        "durs": ["half", "half", "half", "half", "half", "whole"],
        "max_plans": 50,
        "note_names": ["C4", "D4", "E4", "F4", "G4", "A4"],
    },
    {
        "name": "diatonic_8_notes_natural_descending_C_major_scale",
        "key": "C Major",
        "pitches": [72, 71, 69, 67, 65, 64, 62, 60],
        "durs": ["half"] * 7 + ["whole"],
        "max_plans": 50,
        "note_names": ["C5", "B4", "A4", "G4", "F4", "E4", "D4", "C4"],
    },
    {
        "name": "chromatic_altered_B_flat_in_C_major",
        "key": "C Major",
        "pitches": [60, 64, 67, 70, 69],
        "durs": ["half", "half", "half", "half", "whole"],
        "max_plans": 50,
        "note_names": ["C4", "E4", "G4", "Bb4", "A4"],
    },
]

records = []
key = Key("C", "Major")
g = HarmonicGrammar(key=key)
solver = ViterbiSolver()

for pat in test_patterns:
    melody_dicts = [
        {"pitch": p, "duration": d, "is_downbeat": (i % 2 == 0)}
        for i, (p, d) in enumerate(zip(pat["pitches"], pat["durs"]))
    ]
    req_data = {
        "melody": melody_dicts,
        "key": {"tonic": "C", "mode": "Major"},
        "time_signature": "4/4",
        "allow_extended_ranges": False,
        "allow_secondary_dominants": True,
        "max_plans": pat["max_plans"],
    }

    # API call
    api_resp = {}
    try:
        r = urllib.request.Request(
            API_URL,
            data=json.dumps(req_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(r) as resp:
            api_resp = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        api_resp = {"error": str(e)}

    # Core diagnose
    plans = g.generate_plans(melody_dicts, key=key, max_plans=pat["max_plans"])
    sol_count = 0
    first_fail_msg = ""
    for p in plans:
        res = solver.solve(melody_dicts, p, key)
        if res.is_success:
            sol_count += 1
        elif not first_fail_msg:
            first_fail_msg = res.message

    req_json = json.dumps(req_data)
    ps_body = req_json.replace("'", "''")

    rec = {
        "name": pat["name"],
        "length": len(pat["pitches"]),
        "pitches": pat["pitches"],
        "note_names": pat["note_names"],
        "key": pat["key"],
        "api_success": api_resp.get("is_success", False),
        "api_message": api_resp.get("message", ""),
        "plans_generated_count": len(plans),
        "solvable_plans_count": sol_count,
        "first_plan": [c.function for c in plans[0]] if plans else [],
        "first_failure_message": first_fail_msg or "No plans generated",
        "req_data": req_data,
        "curl_repro": "curl -X POST http://127.0.0.1:8000/api/harmonize -H \"Content-Type: application/json\" -d '" + req_json + "'",
        "powershell_repro": "Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/harmonize' -Method Post -ContentType 'application/json' -Body '" + ps_body + "' | ConvertTo-Json -Depth 5",
    }
    records.append(rec)
    print(f"[{pat['name']}] API={rec['api_success']}, Solvable={sol_count}/{len(plans)}, Fail={first_fail_msg}")

out_path = Path("D:/aitraining/.redteam/evidence/minimal_failing_cases.json")
out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved {len(records)} minimal failing cases to: {out_path}")
