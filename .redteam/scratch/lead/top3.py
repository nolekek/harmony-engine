import sys, random
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
key=Key("C","Major"); g=HarmonicGrammar(key); s=ViterbiSolver()
scale=[60,62,64,65,67,69,71,72]
random.seed(7)
found=0
for trial in range(400):
    n=random.choice([4,5,6])
    p=[random.choice(scale) for _ in range(n)]
    if p[-1] not in (60,64,67): continue
    mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    plans=g.generate_plans(mel,key,max_plans=50)
    succ=[]
    for pl in plans:
        r=s.solve(mel,pl,key)
        if r.is_success: succ.append((r.total_cost,[c.function for c in pl]))
    if len(succ)>3:
        first3=succ[:3]; allmin=min(succ,key=lambda x:x[0])
        if allmin[0] < min(c for c,_ in first3)-1e-9:
            print("FOUND",p,"first3",first3,"allmin",allmin,"n_succ",len(succ))
            found+=1
            if found>=5: break
print("found",found)
