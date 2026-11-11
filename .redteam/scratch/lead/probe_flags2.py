from src.harmony.pipeline import Harmonizer
h = Harmonizer()
mel=[60,62,64,65,67]
for kw in (dict(), dict(relax_hard_gates=True)):
    r = h.harmonize(mel, "C Major", **kw)
    print(kw, "success", r.is_success, "msg", r.message[:60])
    for s in r.solutions:
        print("  ", [c.function for c in s.chords], round(s.cost,1), getattr(s,"relaxed_rule_ids",[]))
