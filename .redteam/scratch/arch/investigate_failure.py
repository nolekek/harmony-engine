from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver

key = Key("C", "Major")
melody_default = [
    {"pitch": 64, "duration": "half", "is_downbeat": True},   # E4
    {"pitch": 65, "duration": "half", "is_downbeat": False},  # F4
    {"pitch": 67, "duration": "half", "is_downbeat": True},   # G4
    {"pitch": 64, "duration": "half", "is_downbeat": False},  # E4
    {"pitch": 62, "duration": "half", "is_downbeat": True},   # D4
    {"pitch": 60, "duration": "whole", "is_downbeat": False}, # C4
]

grammar = HarmonicGrammar(key=key)
plans = grammar.generate_plans(melody=melody_default, key=key, max_plans=30)
print(f"Plans generated: {len(plans)}")
for idx, p in enumerate(plans[:5]):
    print(f"  Plan {idx}: {[c.function for c in p]}")

solver = ViterbiSolver()
for idx, p in enumerate(plans[:10]):
    res = solver.solve(melody=melody_default, chords=p, key=key)
    print(f"Plan {idx} ({[c.function for c in p]}): success={res.is_success}, message={res.message}")
    if not res.is_success:
        for d in res.diagnostics:
            print(f"    Step {d.step_index} ({d.chord}, soprano {d.soprano_pitch}): candidates={d.candidates_count}, reachable={d.reachable_candidates_count}")
