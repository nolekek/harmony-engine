import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
for name,p in [("A melodic minor up",[69,71,72,74,76,78,80,81]),("A melodic minor down",[81,79,77,76,74,72,71,69]),("A nat minor up",[69,71,72,74,76,77,79,81])]:
    n=len(p); mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    r=h.harmonize(mel,Key("A","Minor"),time_signature="4/4",max_plans=50)
    print(f"{name:22s} {'OK ' if r.is_success else 'FAIL'} {([c.function for c in r.best_solution.chords] if r.is_success else r.message[:60])}")
