import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

h = Harmonizer()
def run(name, pitches, key=Key("C","Major"), ts="4/4"):
    n=len(pitches)
    mel=[{"pitch":p,"duration":("whole" if i==n-1 else "half"),"is_downbeat":(i%2==0)} for i,p in enumerate(pitches)]
    r=h.harmonize(mel,key,time_signature=ts,max_plans=50)
    print(f"{name:32s} {pitches} -> {'OK ' if r.is_success else 'FAIL'} {len(r.solutions)} {(' '.join(c.function for c in r.best_solution.chords)) if r.is_success else ''}")
    return r

run("scale up", [60,62,64,65,67,69,71,72])
run("scale down", [72,71,69,67,65,64,62,60])
run("twinkle", [60,60,67,67,69,69,67])
run("ode to joy", [64,64,65,67,67,65,64,62])
run("E F G E D C (default)", [64,65,67,64,62,60])
run("C D E F G", [60,62,64,65,67])
run("G A B C D", [67,69,71,72,74])
run("C E G C", [60,64,67,72])
run("C D E C", [60,62,64,60])
run("C F G C", [60,65,67,72])
run("C A D G", [60,69,62,67])
run("C D F G C", [60,62,65,67,72])
run("C E F G C", [60,64,65,67,72])
run("C D E F E D C", [60,62,64,65,64,62,60])
run("G F E D C", [67,65,64,62,60])
run("A B C D E", [69,71,72,74,76])
run("C B A G F E D C", [60,59,57,55,53,52,50,48])
