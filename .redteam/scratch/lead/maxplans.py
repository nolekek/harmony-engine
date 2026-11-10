import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
for mp in (10,20,30,40,50):
    r=Harmonizer().harmonize([64,65,67,64,62,60], key="C Major", max_plans=mp)
    print("max_plans",mp,"OK" if r.is_success else "FAIL", ([c.function for c in r.best_solution.chords] if r.is_success else r.message[:60]))
