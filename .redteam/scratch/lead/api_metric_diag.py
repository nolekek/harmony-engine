import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, calculate_metric_structure
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver

raw=[{"pitch":60,"duration":"half","is_downbeat":True},
     {"pitch":64,"duration":"half","is_downbeat":False},
     {"pitch":67,"duration":"half","is_downbeat":True},
     {"pitch":72,"duration":"whole","is_downbeat":False}]
# emulate backend/api.py conversion: false -> None
conv=[{"pitch":m["pitch"],"duration":m["duration"],"is_downbeat":(m["is_downbeat"] if m["is_downbeat"] else None)} for m in raw]
mi=calculate_metric_structure(conv, default_time_signature="4/4")
print("metric:")
for x in mi: print(" ", x["pitch"], x["duration"], "db=",x["is_downbeat"], "meas",x["measure"],"off",x["offset_in_measure"], "q",x["duration_quarters"])
mel=[{"pitch":i["pitch"],"duration":i["duration"],"is_downbeat":i["is_downbeat"]} for i in mi]
key=Key("C","Major"); g=HarmonicGrammar(key); s=ViterbiSolver()
plans=g.generate_plans(mel,key,max_plans=50)
print("plans",len(plans),[[c.function for c in p] for p in plans[:10]])
from collections import Counter
cnt=Counter(); ok=0
for p in plans:
    r=s.solve(mel,p,key)
    if r.is_success: ok+=1; print("OK",[c.function for c in p],r.total_cost)
    else: cnt[r.message]+=1
print("ok",ok)
for m,c in cnt.most_common(5): print(c,m)
