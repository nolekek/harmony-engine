import sys
import time
sys.path.insert(0, ".")
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.core.types import Key

key = Key("C", "Major")
solver = ViterbiSolver()

# Progression where melody pitches match chord tones:
# T: 64 (E), S6: 65 (F), D: 67 (G), T: 64 (E), D: 62 (D), T: 60 (C)
unit_melody = [64, 65, 67, 64, 62, 60]
unit_chords = ["T", "S6", "D", "T", "D", "T"]

for repeat in [1, 2, 3, 4, 6, 8]:
    mel = unit_melody * repeat
    chords = unit_chords * repeat
    n = len(mel)
    mel_dicts = [{"pitch": p, "is_downbeat": (i % 2 == 0)} for i, p in enumerate(mel)]

    # Run 5 iterations to get clean average
    times_std = []
    for _ in range(5):
        t0 = time.perf_counter()
        res_std = solver.solve(mel_dicts, chords, key=key, allow_extended_ranges=False)
        times_std.append((time.perf_counter() - t0) * 1000)

    times_ext = []
    for _ in range(5):
        t0 = time.perf_counter()
        res_ext = solver.solve(mel_dicts, chords, key=key, allow_extended_ranges=True)
        times_ext.append((time.perf_counter() - t0) * 1000)

    avg_std = sum(times_std) / len(times_std)
    avg_ext = sum(times_ext) / len(times_ext)
    max_k_std = max((d.candidates_count for d in res_std.diagnostics), default=0)
    max_k_ext = max((d.candidates_count for d in res_ext.diagnostics), default=0)

    print(f"N = {n:2d} chords | Std: {avg_std:6.2f} ms (max K={max_k_std:2d}, ok={res_std.is_success}) | "
          f"Ext: {avg_ext:6.2f} ms (max K={max_k_ext:2d}, ok={res_ext.is_success})")
