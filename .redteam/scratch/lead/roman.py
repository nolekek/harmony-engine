import sys
sys.path.insert(0, r"D:\aitraining")
from src.harmony.rules.doubling import get_triad_tones
for s in ["I","IV","V","i","iv","v","III","VII","V7","ii","ii6"]:
    print(s, get_triad_tones(s,0,"MAJOR"))
