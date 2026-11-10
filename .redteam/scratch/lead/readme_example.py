import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
for p in ([64,65,67,62,60],[64,65,67,64,62,60]):
    for mp in (30,50):
        r=Harmonizer().harmonize(p, key="C Major", max_plans=mp)
        print(p,mp,"OK" if r.is_success else "FAIL", ([c.function for c in r.best_solution.chords] if r.is_success else ""))
