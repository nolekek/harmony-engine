import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver

key=Key("C","Major")
def mk(pitches):
    n=len(pitches); return [{"pitch":p,"duration":("whole" if i==n-1 else "half"),"is_downbeat":(i%2==0)} for i,p in enumerate(pitches)]
for name,pitches in [("desc",[72,71,69,67,65,64,62,60]),("CEFGC",[60,64,65,67,72])]:
    mel=mk(pitches)
    g=HarmonicGrammar(key); plans=g.generate_plans(mel,key,max_plans=50); s=ViterbiSolver()
    print("\n==",name,"plans",len(plans))
    from collections import Counter
    msgs=Counter(); ok=0
    for i,p in enumerate(plans):
        r=s.solve(mel,p,key)
        ok+=r.is_success
        if not r.is_success:
            msgs[r.message]+=1
        else:
            print("OK",i,[c.function for c in p],r.total_cost)
    print("ok",ok,"of",len(plans))
    for m,c in msgs.most_common(8): print(c,"x",m[:150])
    print("plan0",[c.function for c in plans[0]])
