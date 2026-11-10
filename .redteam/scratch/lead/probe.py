import sys, json
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.engine import RuleEngine

key = Key("C", "Major")
g = HarmonicGrammar(key)
solver = ViterbiSolver()

def melody(pitches, durs=None, dbs=None):
    n = len(pitches)
    durs = durs or (["half"] * (n - 1) + ["whole"])
    dbs = dbs or [i % 2 == 0 for i in range(n)]
    return [{"pitch": p, "duration": d, "is_downbeat": b} for p, d, b in zip(pitches, durs, dbs)]

default = melody([64, 65, 67, 64, 62, 60])
plans = g.generate_plans(default, key, max_plans=50)
print("Plans:", len(plans))
for i, p in enumerate(plans[:12]):
    print(i, [c.function for c in p])

print("\n=== Solve each plan ===")
ok = 0
for i, p in enumerate(plans):
    r = solver.solve(default, p, key)
    print(i, [c.function for c in p], "OK" if r.is_success else "FAIL", r.message[:110], "cost", round(r.total_cost, 2) if r.is_success else None)
    ok += r.is_success
print("successful plans:", ok)

print("\n=== candidate voicings for T, soprano E4 ===")
cs = generate_candidate_voicings(64, Chord("T"), key)
print("count", len(cs))
bad = [v for v in cs if v.t == v.b or v.s == v.a]
print("T=B or S=A unisons:", len(bad))
print("sample:", [(v.s, v.a, v.t, v.b) for v in bad[:10]])

print("\n=== NCT melody: C D E F G A G F E (C major) ===")
nct = melody([60, 62, 64, 67, 69, 71, 67, 65, 64])
nplans = g.generate_plans(nct, key, max_plans=50)
print("plans", len(nplans))
for i, p in enumerate(nplans[:5]):
    r = solver.solve(nct, p, key)
    print(i, [c.function for c in p], "OK" if r.is_success else "FAIL", r.message[:100])

print("\n=== simple scale C D E F G (passing tones) ===")
sc = melody([60, 62, 64, 65, 67])
splans = g.generate_plans(sc, key, max_plans=50)
print("plans", len(splans), [[c.function for c in p] for p in splans[:5]])
for i, p in enumerate(splans[:5]):
    r = solver.solve(sc, p, key)
    print(i, [c.function for c in p], "OK" if r.is_success else "FAIL", r.message[:100])

print("\n=== D -> VI deceptive ===")
dvi = [Chord("T"), Chord("D"), Chord("VI"), Chord("T")]
r = solver.solve([60, 60, 57, 60], dvi, key)
print("D->VI:", r.is_success, r.message)
