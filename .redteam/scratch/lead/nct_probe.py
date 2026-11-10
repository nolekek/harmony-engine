import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key
h=Harmonizer()
cases=[
 ("passing_C_D_E",[60,62,64],["half","half","whole"]),
 ("passing_C_D_E_F_G",[60,62,64,65,67],["quarter","quarter","quarter","quarter","whole"]),
 ("neighbor_C_D_C",[60,62,60],["half","half","whole"]),
 ("neighbor_E_F_E",[64,65,64],["half","half","whole"]),
 ("neighbor_G_A_G",[67,69,67],["half","half","whole"]),
 ("passing_down_G_F_E",[67,65,64],["half","half","whole"]),
 ("passing_full_C..C",[60,62,64,65,67,65,64,62,60],["quarter"]*8+["whole"]),
 ("passing_G_A_B_C_D",[67,69,71,72,74],["quarter","quarter","quarter","quarter","whole"]),
]
for name,p,d in cases:
    mel=[{"pitch":x,"duration":dd,"is_downbeat":(i%2==0)} for i,(x,dd) in enumerate(zip(p,d))]
    r=h.harmonize(mel,Key("C" if name!="passing_G_A_B_C_D" else "G","Major"),time_signature="4/4",max_plans=50)
    print(f"{name:28s} {'OK ' if r.is_success else 'FAIL'} {([c.function for c in r.best_solution.chords] if r.is_success else r.message[:50])}")
