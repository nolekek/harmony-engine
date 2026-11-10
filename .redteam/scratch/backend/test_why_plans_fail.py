import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver

melody = [
    {"pitch": 64, "duration": "half"},
    {"pitch": 65, "duration": "half"},
    {"pitch": 67, "duration": "half"},
    {"pitch": 64, "duration": "half"},
    {"pitch": 62, "duration": "half"},
    {"pitch": 60, "duration": "whole"},
]
key = Key("C", "Major")
grammar = HarmonicGrammar(key)
plans = grammar.generate_plans(melody, key=key, max_plans=50)

solver = ViterbiSolver()
for idx, p in enumerate(plans[:10]):
    res = solver.solve(melody, p, key=key)
    chords_str = " -> ".join(c.function for c in p)
    print(f"Plan #{idx}: {chords_str}")
    print(f"  Success: {res.is_success}, Message: {res.message}")
    for d in res.diagnostics:
        print(f"    Step {d.step_index} ({d.chord}): cands={d.candidates_count}, reachable={d.reachable_candidates_count}")
