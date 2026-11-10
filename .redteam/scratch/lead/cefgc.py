import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
for p in ([60,62,64,65,67,72],[60,64,65,67,72]):
    r=Harmonizer().harmonize(p,key="C Major",max_plans=50)
    print(p,"OK" if r.is_success else "FAIL",([c.function for c in r.best_solution.chords] if r.is_success else r.message[:60]))
