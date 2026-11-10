import sys, json
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h = Harmonizer()
mel = [
 {"pitch":64,"duration":"half","is_downbeat":True},
 {"pitch":65,"duration":"half","is_downbeat":False},
 {"pitch":67,"duration":"half","is_downbeat":True},
 {"pitch":64,"duration":"half","is_downbeat":False},
 {"pitch":62,"duration":"half","is_downbeat":True},
 {"pitch":60,"duration":"whole","is_downbeat":False},
]
for ts in ["4/4","3/4","2/4","6/8","3/8"]:
  for ext in [False, True]:
    r = h.harmonize(mel, Key("C","Major"), time_signature=ts, allow_extended_ranges=ext, max_plans=50)
    print(ts, "ext", ext, "OK" if r.is_success else "FAIL", len(r.solutions), r.message[:90])
    if r.is_success:
      print("   ", [c.function for c in r.best_solution.chords], r.best_solution.durations)
