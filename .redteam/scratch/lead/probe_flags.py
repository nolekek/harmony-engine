from src.harmony.pipeline import Harmonizer
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.core.types import Voicing
import itertools

melodies = [
    ([60,62,64,65,67], "C Major"),
    ([64,65,67,64,62,60], "C Major"),
    ([72,71,69], "C Major"),
    ([67,69,71,72,74,71,67], "G Major"),
    ([81,80,77,76,74,72,71,69], "A Minor"),
]
h = Harmonizer()
for mel, key in melodies:
    base = h.harmonize(mel, key)
    rel = h.harmonize(mel, key, relax_hard_gates=True)
    uni = h.harmonize(mel, key, allow_adjacent_unisons=True)
    def info(r):
        if not r.is_success or not r.best_solution: return "FAIL"
        sol = r.best_solution
        v = [(x.s,x.a,x.t,x.b) for x in sol.voicings]
        has_uni = any(len({x[0],x[1],x[2],x[3]})<4 for x in v)
        return f"ok cost={sol.cost:.1f} uni={has_uni} relaxed={getattr(sol,'relaxed_rule_ids',[])}"
    print(key, mel, "| strict:", info(base), "| relax:", info(rel), "| unisons:", info(uni))
