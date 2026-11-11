import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import time
import threading
from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import TimeSignature

harmonizer = Harmonizer()

def run_with_timeout(name, fn, timeout_sec=5.0):
    res_box = [None, None, None]  # result, exception, timed_out
    def target():
        try:
            t0 = time.perf_counter()
            res_box[0] = fn()
            res_box[2] = time.perf_counter() - t0
        except Exception as e:
            res_box[1] = e
            res_box[2] = time.perf_counter() - t0

    t = threading.Thread(target=target)
    t.daemon = True
    t.start()
    t.join(timeout_sec)
    if t.is_alive():
        print(f"=== {name} === TIMED OUT (> {timeout_sec}s) - INFINITE LOOP OR HANG", flush=True)
    elif res_box[1]:
        print(f"=== {name} === ERROR ({res_box[2]:.3f}s): {type(res_box[1]).__name__}: {res_box[1]}", flush=True)
    else:
        res = res_box[0]
        succ = getattr(res, 'is_success', None)
        msg = getattr(res, 'message', '')
        print(f"=== {name} === OK ({res_box[2]:.3f}s): is_success={succ}, msg={msg[:80]}", flush=True)

run_with_timeout("Time signature '0/4'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="0/4"), timeout_sec=2.0)
run_with_timeout("Time signature 'abc'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="abc"), timeout_sec=2.0)
run_with_timeout("Time signature 'abc/def'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="abc/def"), timeout_sec=2.0)
run_with_timeout("Time signature '4/0'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="4/0"), timeout_sec=2.0)
run_with_timeout("Time signature '-1/4'", lambda: harmonizer.harmonize([60, 62], "C Major", time_signature="-1/4"), timeout_sec=2.0)

run_with_timeout("is_downbeat True on all notes", lambda: harmonizer.harmonize(
    [{"pitch": 60, "is_downbeat": True}, {"pitch": 64, "is_downbeat": True}, {"pitch": 67, "is_downbeat": True}],
    "C Major"
), timeout_sec=3.0)

run_with_timeout("allow_extended_ranges=True (59, 60)", lambda: harmonizer.harmonize([59, 60], "C Major", allow_extended_ranges=True), timeout_sec=3.0)
run_with_timeout("allow_extended_ranges=False (59, 60)", lambda: harmonizer.harmonize([59, 60], "C Major", allow_extended_ranges=False), timeout_sec=3.0)

run_with_timeout("max_plans=1", lambda: harmonizer.harmonize([60, 62, 64], "C Major", max_plans=1), timeout_sec=3.0)
run_with_timeout("max_plans=100", lambda: harmonizer.harmonize([60, 62, 64], "C Major", max_plans=100), timeout_sec=3.0)
run_with_timeout("128 notes [60]*128 (max_plans=1)", lambda: harmonizer.harmonize([60] * 128, "C Major", max_plans=1), timeout_sec=10.0)
