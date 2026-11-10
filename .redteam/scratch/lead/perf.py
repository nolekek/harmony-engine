import sys, time
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
scale=[60,62,64,65,67,69,71,72]
for n in [4,8,12,16]:
    p=[scale[i%8] for i in range(n)]
    mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    t=time.perf_counter(); r=h.harmonize(mel,Key("C","Major"),time_signature="4/4",max_plans=50); dt=(time.perf_counter()-t)*1000
    print(n, "notes", "OK" if r.is_success else "FAIL", f"{dt:.0f} ms", ([c.function for c in r.best_solution.chords] if r.is_success else r.message[:60]))
