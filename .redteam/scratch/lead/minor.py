import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
cases={
 "A natural minor": ([69,71,72,74,76,77,79,81], Key("A","Minor")),
 "A harmonic minor": ([69,71,72,74,76,77,80,81], Key("A","Minor")),
 "A minor descending": ([81,79,77,76,74,72,71,69], Key("A","Minor")),
}
for name,(p,k) in cases.items():
    n=len(p); mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    r=h.harmonize(mel,k,time_signature="4/4",max_plans=50)
    print(f"{name:20s} {'OK ' if r.is_success else 'FAIL'} {([c.function for c in r.best_solution.chords] if r.is_success else r.message[:70])}")
