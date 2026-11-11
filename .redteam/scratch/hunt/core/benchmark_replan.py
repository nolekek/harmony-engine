import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import time
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

h = Harmonizer()

# Let's test a melody with lots of diatonic chords but voice-leading deadlocks
# e.g., large leaps between diatonic steps
melodies = [
    [60, 69, 62, 71, 64, 72, 65, 74],
    [60, 71, 60, 71, 60, 71, 60, 71],
    [60, 62, 60, 62, 60, 62, 60, 62, 60, 62],
    [67, 65, 64, 62, 60, 71, 69, 67, 65, 64],
    [60, 67, 60, 67, 60, 67, 60, 67],
]

for idx, mel in enumerate(melodies):
    t0 = time.perf_counter()
    res = h.harmonize(mel, "C Major", allow_replanning=True)
    el = time.perf_counter() - t0
    print(f"Melody {idx} (len {len(mel)}): success={res.is_success}, time={el:.3f}s, msg={res.message}")
