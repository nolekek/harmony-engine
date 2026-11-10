import sys
from collections import Counter
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.engine import RuleEngine

key = Key("C", "Major")
eng = RuleEngine()
s_v = generate_candidate_voicings(65, Chord("S"), key)   # soprano F4 over IV (F-A-C)
d_v = generate_candidate_voicings(67, Chord("D"), key)   # soprano G4 over V (G-B-D)
print("S candidates", len(s_v), [(v.s,v.a,v.t,v.b) for v in s_v])
print("D candidates", len(d_v), [(v.s,v.a,v.t,v.b) for v in d_v])

rules = Counter()
examples = {}
valid = 0
for pv in s_v:
    for cv in d_v:
        res = eng.validate(prev_voicing=pv, curr_voicing=cv, prev_chord=Chord("S"), curr_chord=Chord("D"), key=key, is_downbeat=True)
        if res.is_valid:
            valid += 1
        else:
            for v in res.violations:
                if v.is_hard:
                    rules[v.rule_id] += 1
                    examples.setdefault(v.rule_id, (pv, cv, v.description))
print("valid pairs", valid, "of", len(s_v)*len(d_v))
print("hard rules:", rules)
for rid, (pv, cv, desc) in examples.items():
    print("\n", rid, desc)
    print("  prev", (pv.s,pv.a,pv.t,pv.b), "curr", (cv.s,cv.a,cv.t,cv.b))
