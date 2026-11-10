import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
cases={
 "C5 B4 A4 G4": [72,71,69,67],
 "G4 F4 E4 D4": [67,65,64,62],
 "E4 D4 C4 B3?": [64,62,60,59],
 "C5 B4 C5": [72,71,72],
 "G4 F4 G4": [67,65,67],
 "C5 A4 G4 E4": [72,69,67,64],
 "C5 G4 E4 C4": [72,67,64,60],
 "E5 D5 C5 G4": [76,74,72,67],
}
for name,p in cases.items():
    n=len(p); mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    r=h.harmonize(mel,Key("C","Major"),time_signature="4/4",max_plans=50)
    print(f"{name:22s} {'OK ' if r.is_success else 'FAIL'} {([c.function for c in r.best_solution.chords] if r.is_success else r.message[:70])}")
