import sys
sys.path.insert(0, ".")
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.rules.engine import RuleEngine

# 1. Check default melody: [64, 65, 67, 64, 62, 60] with chords T, S6, D, T, D, T
melody = [64, 65, 67, 64, 62, 60]
chords = ["T", "S6", "D", "T", "D", "T"]
key = Key("C", "Major")

solver = ViterbiSolver()
res = solver.solve(melody, chords, key=key)
print("Solver success:", res.is_success)
print("Total cost:", res.total_cost)
for idx, v in enumerate(res.voicings):
    print(f"Chord {idx} ({chords[idx]}): S={v.soprano}, A={v.alto}, T={v.tenor}, B={v.bass} | SATB pitch classes: {v.pitch_classes()}")
    if v.tenor == v.bass:
        print(f"  -> BUG: Tenor == Bass unison ({v.tenor})!")
    if v.soprano == v.alto:
        print(f"  -> BUG: Soprano == Alto unison ({v.soprano})!")

# Check if G (pitch class 7) is in first chord
v0 = res.voicings[0]
print("v0 pitch classes:", v0.pitch_classes())
print("Fifth (G=7) in v0?", 7 in v0.pitch_classes())
print("Root (C=0) count in v0:", v0.pitch_classes().count(0))

# Validate v0 standalone through RuleEngine
engine = RuleEngine()
val = engine.validate_voicing(v0, chord=Chord("T"), key=key)
print("v0 validation is_valid:", val.is_valid, "violations:", [v.rule_id for v in val.violations])

# Check candidate generation for Soprano=64, Chord('T')
candidates = generate_candidate_voicings(64, Chord("T"), key=key)
print(f"Total candidates for T with S=64: {len(candidates)}")
unison_tb = [v for v in candidates if v.tenor == v.bass]
unison_sa = [v for v in candidates if v.soprano == v.alto]
incomplete_triads = [v for v in candidates if len(set(v.pitch_classes())) < 3]
print(f"Candidates with T==B: {len(unison_tb)}")
print(f"Candidates with S==A: {len(unison_sa)}")
print(f"Candidates incomplete (< 3 pitch classes): {len(incomplete_triads)}")
