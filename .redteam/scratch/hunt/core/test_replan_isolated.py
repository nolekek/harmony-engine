import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import time
from unittest.mock import patch
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key

h = Harmonizer()
mel = [67, 65, 64, 62, 60, 71, 69, 67, 65, 64]

orig_replan = h._replan
replan_stats = {}

def monitored_replan(*args, **kwargs):
    t0 = time.perf_counter()
    res = orig_replan(*args, **kwargs)
    el = time.perf_counter() - t0
    replan_stats["time"] = el
    return res

h._replan = monitored_replan
res = h.harmonize(mel, "C Major", allow_replanning=True)
print(f"Total time: {time.perf_counter()}, Replan time: {replan_stats.get('time'):.3f}s")
