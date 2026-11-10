import sys
sys.path.insert(0, ".")
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Key, Chord
from src.harmony.rules.engine import RuleEngine

key = Key("C", "Major")
engine = RuleEngine()

cands_3 = generate_candidate_voicings(65, Chord("S"), key=key)
cands_4 = generate_candidate_voicings(67, Chord("D6"), key=key)

valid_pairs = []
for v3 in cands_3:
    for v4 in cands_4:
        val = engine.validate(v3, v4, Chord("S"), Chord("D6"), key=key)
        if not val.has_hard_violations:
            valid_pairs.append((v3, v4))

print(f"Number of valid pairs between S (65) and D6 (67): {len(valid_pairs)}")
if not valid_pairs:
    violations_summary = {}
    for v3 in cands_3:
        for v4 in cands_4:
            val = engine.validate(v3, v4, Chord("S"), Chord("D6"), key=key)
            for viol in val.hard_violations:
                violations_summary[viol.rule_id] = violations_summary.get(viol.rule_id, 0) + 1
    for r_id, count in sorted(violations_summary.items(), key=lambda x: -x[1]):
        print(f"  {r_id:30s}: {count}")
