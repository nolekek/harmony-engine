import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import time
from src.harmony.pipeline import Harmonizer

h = Harmonizer()

# Melodies with chromatic leaps, or awkward soprano intervals that fail standard plans
test_melodies = [
    # Tritone leaps, chromatic notes not in key
    ([60, 66, 60, 66, 60], "C Major"),
    # Augmented 2nds or leaps back and forth
    ([60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71], "C Major"),
    # Impossible vocal leaps
    ([60, 72, 60, 72, 60, 72], "C Major"),
    # Unsolvable repeated notes or awkward cadences
    ([61, 61, 61, 61], "C Major"),
    ([66, 66, 66, 66], "C Major"),
]

for i, (mel, key) in enumerate(test_melodies):
    t0 = time.perf_counter()
    res = h.harmonize(mel, key, allow_replanning=True)
    elapsed = time.perf_counter() - t0
    print(f"Melody {i} ({mel}, {key}): success={res.is_success}, elapsed={elapsed:.3f}s, msg={res.message}")
