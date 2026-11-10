import sys
sys.path.insert(0, ".")
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Key, Chord
from src.harmony.rules.engine import RuleEngine

key = Key("C", "Major")
engine = RuleEngine()
solver = ViterbiSolver()

melody = [60, 62, 64, 65, 67, 72]
plan = [Chord("T"), Chord("D"), Chord("T"), Chord("S"), Chord("D"), Chord("T")]

# Get reachable candidates at step 3
res = solver.solve(melody[:4], plan[:4], key=key)
reachable_v3 = res.voicings[-1] # or find all reachable

# Let's inspect step 3 -> step 4
cands_3 = generate_candidate_voicings(65, Chord("S"), key=key)
cands_4 = generate_candidate_voicings(67, Chord("D"), key=key)

violations_summary = {}
for i, v3 in enumerate(cands_3):
    for j, v4 in enumerate(cands_4):
        val = engine.validate(
            prev_voicing=v3,
            curr_voicing=v4,
            prev_chord=Chord("S"),
            curr_chord=Chord("D"),
            key=key,
        )
        if val.has_hard_violations:
            for viol in val.hard_violations:
                violations_summary[viol.rule_id] = violations_summary.get(viol.rule_id, 0) + 1

print("Total candidate pairs between S (S=65) and D (S=67):", len(cands_3) * len(cands_4))
print("Hard violation frequencies across all pairs:")
for r_id, count in sorted(violations_summary.items(), key=lambda x: -x[1]):
    print(f"  {r_id:30s}: {count}")

# Check if ANY pair has 0 hard violations
valid_pairs = []
for i, v3 in enumerate(cands_3):
    for j, v4 in enumerate(cands_4):
        val = engine.validate(v3, v4, Chord("S"), Chord("D"), key=key)
        if not val.has_hard_violations:
            valid_pairs.append((v3, v4))

print(f"\nNumber of valid pairs between S (65) and D (67): {len(valid_pairs)}")
if valid_pairs:
    print("Example valid pair:")
    print("  v3:", valid_pairs[0][0])
    print("  v4:", valid_pairs[0][1])
