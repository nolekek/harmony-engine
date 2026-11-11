import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import time
from src.harmony.pipeline import Harmonizer

h = Harmonizer()
mel = [67, 65, 64, 62, 60, 71, 69, 67, 65, 64]

orig_solve = h.solver.solve
solve_count = 0
replan_solve_count = 0
in_replan = False

def monitored_solve(*args, **kwargs):
    global solve_count, replan_solve_count
    solve_count += 1
    if in_replan:
        replan_solve_count += 1
    return orig_solve(*args, **kwargs)

h.solver.solve = monitored_solve

orig_replan = h._replan
def monitored_replan(*args, **kwargs):
    global in_replan
    in_replan = True
    t0 = time.perf_counter()
    res = orig_replan(*args, **kwargs)
    el = time.perf_counter() - t0
    in_replan = False
    return res, el

h._replan = lambda *a, **kw: monitored_replan(*a, **kw)[0]

t0 = time.perf_counter()
res = h.harmonize(mel, "C Major", allow_replanning=True)
el = time.perf_counter() - t0

print(f"Total time: {el:.3f}s, Total solves: {solve_count}, Replan solves: {replan_solve_count}")
