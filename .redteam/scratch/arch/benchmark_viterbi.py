import time
import statistics
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.syntax.grammar import HarmonicGrammar

harmonizer = Harmonizer()
key = Key("C", "Major")

# Melody 1: Default UI melody (6 notes)
melody_6 = [
    {"pitch": 64, "duration": "half", "is_downbeat": True},   # E4
    {"pitch": 65, "duration": "half", "is_downbeat": False},  # F4
    {"pitch": 67, "duration": "half", "is_downbeat": True},   # G4
    {"pitch": 64, "duration": "half", "is_downbeat": False},  # E4
    {"pitch": 62, "duration": "half", "is_downbeat": True},   # D4
    {"pitch": 60, "duration": "whole", "is_downbeat": False}, # C4
]

# Benchmark grammar + plans
grammar = HarmonicGrammar(key=key)
t0 = time.perf_counter()
plans = grammar.generate_plans(melody=melody_6, key=key, max_plans=50)
t_grammar = (time.perf_counter() - t0) * 1000

print(f"Grammar plans generated: {len(plans)} in {t_grammar:.2f} ms")

solver = ViterbiSolver()
viterbi_times = []
for p in plans:
    t_v0 = time.perf_counter()
    res = solver.solve(melody=melody_6, chords=p, key=key)
    viterbi_times.append((time.perf_counter() - t_v0) * 1000)

print(f"Single Viterbi solve: min={min(viterbi_times):.2f} ms, median={statistics.median(viterbi_times):.2f} ms, max={max(viterbi_times):.2f} ms, mean={statistics.mean(viterbi_times):.2f} ms")
print(f"Total time for all {len(plans)} plans: {sum(viterbi_times):.2f} ms")

# Longer melody (16 notes)
melody_16 = melody_6 + melody_6 + melody_6[:4]
t0 = time.perf_counter()
plans_16 = grammar.generate_plans(melody=melody_16, key=key, max_plans=50)
t_grammar_16 = (time.perf_counter() - t0) * 1000
print(f"\n16-note melody: {len(plans_16)} plans generated in {t_grammar_16:.2f} ms")

viterbi_times_16 = []
for p in plans_16[:10]:
    t_v0 = time.perf_counter()
    res = solver.solve(melody=melody_16, chords=p, key=key)
    viterbi_times_16.append((time.perf_counter() - t_v0) * 1000)

if viterbi_times_16:
    print(f"16-note Viterbi solve (10 plans): min={min(viterbi_times_16):.2f} ms, median={statistics.median(viterbi_times_16):.2f} ms, max={max(viterbi_times_16):.2f} ms")
