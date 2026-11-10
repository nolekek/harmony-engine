import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
key=Key("A","Minor"); g=HarmonicGrammar(key); s=ViterbiSolver()
p=[69,71,72,74,76,77,80,81]
mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
plans=g.generate_plans(mel,key,max_plans=50)
print("plans",len(plans))
for i,pl in enumerate(plans[:15]): print(i,[c.function for c in pl])
from collections import Counter
cnt=Counter(); ok=0
for pl in plans:
    r=s.solve(mel,pl,key)
    if r.is_success: ok+=1; print("OK",[c.function for c in pl],r.total_cost)
    else: cnt[r.message]+=1
print("ok",ok)
for m,c in cnt.most_common(10): print(c,m[:160])
