import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
majors=["C","G","D","A","E","B","F#","Db","Ab","Eb","Bb","F"]
minors=["A","E","B","F#","C#","G#","D#","Bb","F","C","G","D"]
PC={"C":0,"C#":1,"DB":1,"D":2,"D#":3,"EB":3,"E":4,"F":5,"F#":6,"GB":6,"G":7,"G#":8,"AB":8,"A":9,"A#":10,"BB":10,"B":11,"H":11}
def scale(tonic, intervals):
    root=60+PC[tonic.upper()]
    return [root+i for i in intervals]
I_MAJ=[0,2,4,5,7,9,11,12]
I_MIN=[0,2,3,5,7,8,11,12]
def run(p, key):
    n=len(p); mel=[{"pitch":x,"duration":"half","is_downbeat":(i%2==0)} for i,x in enumerate(p)]
    r=h.harmonize(mel,key,time_signature="4/4",max_plans=50)
    return r.is_success, ([c.function for c in r.best_solution.chords] if r.is_success else "")
print("MAJORS")
okm=0
for t in majors:
    s,ch=run(scale(t,I_MAJ),Key(t,"Major")); okm+=s
    print(f" {t:3s} {'OK ' if s else 'FAIL'} {' '.join(ch)}")
print("MINORS")
okn=0
for t in minors:
    s,ch=run(scale(t,I_MIN),Key(t,"Minor")); okn+=s
    print(f" {t:3s} {'OK ' if s else 'FAIL'} {' '.join(ch)}")
print("major",okm,"/12  minor",okn,"/12")
