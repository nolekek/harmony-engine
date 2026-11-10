import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.core.types import Key, Chord
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.doubling import check_doubling
key=Key("C","Major")
for sym,sp in [("T",67),("T",64),("S",60),("D",62),("II",62),("VI",69),("K64",67)]:
    vs=generate_candidate_voicings(sp,Chord(sym),key)
    bad=[]
    for v in vs:
        pcs={x%12 for x in (v.s,v.a,v.t,v.b)}
        # triad completeness: all 3 pcs present
        from src.harmony.rules.doubling import get_triad_tones
        r,t,f=get_triad_tones(sym,0,"MAJOR")
        missing=({r,t,f}-pcs)
        if missing: bad.append((tuple(v), sorted(missing)))
    print(sym,sp,"count",len(vs),"missing-tone",len(bad),bad[:5])
