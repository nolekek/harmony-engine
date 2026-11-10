import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.doubling import get_triad_tones
key=Key("C","Major")
for sym in ["D43","D2","D65","III","VI","K64"]:
    print(sym, "triad", get_triad_tones(sym,0,"MAJOR"))
    vs=generate_candidate_voicings(67 if sym in ("D43","D2","D65","K64") else 69 if sym=="VI" else 64, Chord(sym), key)
    basses=sorted({v.b%12 for v in vs})
    print("  bass pcs", basses, "count", len(vs), "sample", [(v.s,v.a,v.t,v.b) for v in vs[:4]])
