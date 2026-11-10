import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
for name,p in {"C5 B4 A4": [72,71,69], "C5 D5 E5 F5": [72,74,76,77], "C5 B4 A4 F4": [72,71,69,65], "A4 B4 C5": [69,71,72]}.items():
    n=len(p); mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    r=h.harmonize(mel,Key("C","Major"),time_signature="4/4",max_plans=50)
    print(f"{name:16s} {'OK' if r.is_success else 'FAIL'} {([c.function for c in r.best_solution.chords] if r.is_success else r.message[:80])}")
