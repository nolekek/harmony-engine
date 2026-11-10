import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.rules.engine import RuleEngine
from src.harmony.solver.state_generator import generate_candidate_voicings

engine = RuleEngine()
key = Key("C", "Major")

# Step 0: T, soprano=64 (E4)
cands_0 = generate_candidate_voicings(64, Chord("T"), key)
# Filter step 0
valid_0 = [v for v in cands_0 if not engine.validate(None, v, None, Chord("T"), key, is_downbeat=True).has_hard_violations]

# Step 1: S, soprano=65 (F4)
cands_1 = generate_candidate_voicings(65, Chord("S"), key, prev_chord=Chord("T"))
# Filter step 1 reachable from step 0
valid_1 = []
for v1 in cands_1:
    can_reach = any(not engine.validate(v0, v1, Chord("T"), Chord("S"), key, is_downbeat=True).has_hard_violations for v0 in valid_0)
    if can_reach:
        valid_1.append(v1)

print(f"Valid voicings at Step 1 (S): {len(valid_1)}")

# Step 2: D, soprano=67 (G4)
cands_2 = generate_candidate_voicings(67, Chord("D"), key, prev_chord=Chord("S"))
print(f"Candidates at Step 2 (D): {len(cands_2)}")

violations_counter = {}
for v1 in valid_1:
    for v2 in cands_2:
        res = engine.validate(v1, v2, Chord("S"), Chord("D"), key, is_downbeat=True)
        for h in res.hard_violations:
            violations_counter[h.rule_id] = violations_counter.get(h.rule_id, 0) + 1

print("Violations between Step 1 (S) and Step 2 (D):")
for r_id, count in sorted(violations_counter.items(), key=lambda x: -x[1]):
    print(f"  {r_id}: {count}")
