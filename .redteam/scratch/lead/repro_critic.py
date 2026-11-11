from src.harmony.pipeline import Harmonizer
h=Harmonizer()
cases=[
 ("ends on IV",[60,64,62,65],"C Major"),
 ("scale to VI",[60,62,64,65,67,69],"C Major"),
 ("N6->D->T low B3",[65,61,59,60],"C Major"),
 ("simple",[64,65,67,64,62,60],"C Major"),
]
for name,mel,key in cases:
    r=h.harmonize(mel,key)
    plan=[c.function for c in r.best_solution.chords] if r.is_success and r.best_solution else None
    print(f"{name:20s} success={r.is_success} plan={plan} msg={r.message[:80]}")
