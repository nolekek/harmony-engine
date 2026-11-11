# -*- coding: utf-8 -*-
"""Lead verification of hostile-input fixes."""
import sys

sys.path.insert(0, r"D:\aitraining")

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def show(name, resp):
    ctype = resp.headers.get("content-type", "")
    body = resp.text[:100] if ctype.startswith("application/json") else "<file>"
    print(f"{name}: status={resp.status_code} {body}")


base = {
    "melody": [{"pitch": 60, "duration": "half"}, {"pitch": 62, "duration": "half"}],
    "key": {"tonic": "C", "mode": "Major"},
}

for ts in ("0/4", "4/0", "abc", "7/8"):
    body = dict(base, time_signature=ts)
    show(f"ts={ts}", client.post("/api/harmonize", json=body))

body = dict(base)
body["melody"] = [{"pitch": 60, "duration": "banana"}, {"pitch": 62, "duration": "half"}]
show("duration=banana", client.post("/api/harmonize", json=body))

show("export empty midi", client.post("/api/export/midi", json={"voicings": []}))
show(
    "export bad chord",
    client.post(
        "/api/export/musicxml",
        json={"voicings": [{"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}], "chords": ["XYZ"]},
    ),
)

health = client.get("/api/health")
print("X-Request-ID present:", "x-request-id" in {k.lower() for k in health.headers})

big = {"text": "C4 " * 200000}
show("oversize body", client.post("/api/parse-text", json=big))

# Rules: VII6 -> T must not demand a doubled tonic third
from src.harmony.core.types import Chord, Key, Voicing
from src.harmony.rules.doubling import check_doubling

k = Key("C", "Major")
t_voicing = Voicing(64, 55, 52, 48)  # T: E G E C (root doubled)
viol = check_doubling(t_voicing, Chord("T"), key=k, prev_chord=Chord("VII6"))
print("VII6->T doubling violations:", [v.rule_id for v in viol])

# K64 must never be the final chord
from src.harmony.rules.engine import RuleEngine

eng = RuleEngine()
res = eng.validate(None, Voicing(64, 60, 55, 43), prev_chord=None, curr_chord=Chord("K64"), key=k, is_final_chord=True)
print("K64 final violations:", [v.rule_id for v in res.hard_violations])
