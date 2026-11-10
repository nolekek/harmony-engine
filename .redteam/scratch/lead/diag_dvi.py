import sys
from collections import Counter
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.engine import RuleEngine

key=Key("C","Major"); eng=RuleEngine()
# descending scale: C5, B4, A4 -> T, D, VI
d_v = generate_candidate_voicings(71, Chord("D"), key)
vi_v = generate_candidate_voicings(69, Chord("VI"), key, prev_chord=Chord("D"))
print("D candidates", len(d_v), [(v.s,v.a,v.t,v.b) for v in d_v])
print("VI candidates", len(vi_v), [(v.s,v.a,v.t,v.b) for v in vi_v])
rules=Counter(); examples={}; valid=0; checks=0
for pv in d_v:
    for cv in vi_v:
        checks+=1
        res=eng.validate(prev_voicing=pv, curr_voicing=cv, prev_chord=Chord("D"), curr_chord=Chord("VI"), key=key, is_downbeat=True)
        if res.is_valid: valid+=1
        for v in res.violations:
            if v.is_hard:
                rules[v.rule_id]+=1; examples.setdefault(v.rule_id,(pv,cv,v.description))
print("valid",valid,"of",checks,"rules",rules)
for rid,(pv,cv,d) in examples.items():
    print("\n",rid,d); print(" prev",(pv.s,pv.a,pv.t,pv.b)," curr",(cv.s,cv.a,cv.t,cv.b))
