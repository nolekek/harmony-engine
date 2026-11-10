import json, urllib.request, sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

mel = [
 {"pitch":60,"duration":"half","is_downbeat":True},
 {"pitch":64,"duration":"half","is_downbeat":False},
 {"pitch":67,"duration":"half","is_downbeat":True},
 {"pitch":72,"duration":"whole","is_downbeat":False},
]
h=Harmonizer()
r=h.harmonize(mel, Key("C","Major"), time_signature="4/4", max_plans=50)
print("pipeline:", r.is_success, [c.function for c in r.best_solution.chords] if r.is_success else r.message)
req=urllib.request.Request("http://127.0.0.1:8000/api/harmonize", data=json.dumps({"melody":mel,"key":{"tonic":"C","mode":"Major"},"time_signature":"4/4","allow_extended_ranges":False,"allow_secondary_dominants":True,"max_plans":50}).encode(), headers={"Content-Type":"application/json"})
resp=json.loads(urllib.request.urlopen(req).read())
print("api:", resp["is_success"], [c["chords"] for c in resp["candidates"]], resp["message"])
print("api durations:", resp["candidates"][0]["durations"] if resp["candidates"] else None)
