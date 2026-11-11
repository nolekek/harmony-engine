import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import time
import traceback
from src.harmony.pipeline import Harmonizer

harmonizer = Harmonizer()

def test_case(name, func):
    print(f"=== TEST: {name} ===", flush=True)
    t0 = time.perf_counter()
    try:
        res = func()
        elapsed = time.perf_counter() - t0
        print(f"  Result ({elapsed:.2f}s): is_success={getattr(res, 'is_success', None)}, msg={getattr(res, 'message', '')[:100]}", flush=True)
    except Exception as e:
        elapsed = time.perf_counter() - t0
        print(f"  CRASH ({elapsed:.2f}s, {type(e).__name__}): {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()

test_case("Empty input []", lambda: harmonizer.harmonize([], "C Major"))
test_case("1 note [60]", lambda: harmonizer.harmonize([60], "C Major"))
test_case("Pitch 0 [0, 60]", lambda: harmonizer.harmonize([0, 60], "C Major"))
test_case("Pitch 127 [127, 60]", lambda: harmonizer.harmonize([127, 60], "C Major"))
test_case("Duration 'whole' in 3/8", lambda: harmonizer.harmonize(
    [{"pitch": 60, "duration": "whole"}, {"pitch": 62, "duration": "eighth"}],
    "C Major",
    time_signature="3/8"
))
test_case("Time signature '7/8'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="7/8"))
test_case("Time signature '0/4'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="0/4"))
test_case("Time signature 'abc'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="abc"))
test_case("is_downbeat True on all notes", lambda: harmonizer.harmonize(
    [{"pitch": 60, "is_downbeat": True}, {"pitch": 64, "is_downbeat": True}, {"pitch": 67, "is_downbeat": True}],
    "C Major"
))
test_case("allow_extended_ranges=True with low soprano 59", lambda: harmonizer.harmonize([59, 60], "C Major", allow_extended_ranges=True))
test_case("allow_extended_ranges=False with low soprano 59", lambda: harmonizer.harmonize([59, 60], "C Major", allow_extended_ranges=False))
test_case("max_plans=1", lambda: harmonizer.harmonize([60, 62, 64], "C Major", max_plans=1))
test_case("max_plans=100", lambda: harmonizer.harmonize([60, 62, 64], "C Major", max_plans=100))
test_case("128 notes [60]*128", lambda: harmonizer.harmonize([60] * 128, "C Major", max_plans=1))
