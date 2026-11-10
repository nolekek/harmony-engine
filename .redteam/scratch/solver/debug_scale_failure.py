import sys
sys.path.insert(0, ".")
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.core.types import Key

key = Key("C", "Major")
g = HarmonicGrammar(key)
solver = ViterbiSolver()

melody = [60, 62, 64, 65, 67, 72]
plans = g.generate_plans(melody, key)

print(f"Generated {len(plans)} plans for [60, 62, 64, 65, 67, 72]:")
for idx, plan in enumerate(plans):
    fns = [c.function for c in plan]
    res = solver.solve(melody, plan, key=key)
    print(f"\nPlan {idx + 1}: {' -> '.join(fns)}")
    print(f"  Result success: {res.is_success}")
    print(f"  Solver message: {res.message}")
    for d in res.diagnostics:
        print(f"    Step {d.step_index} ({d.chord}, S={d.soprano_pitch}): {d.candidates_count} cands, {d.reachable_candidates_count} reachable")
