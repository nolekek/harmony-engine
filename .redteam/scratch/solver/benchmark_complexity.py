import sys
import time
sys.path.insert(0, ".")
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.core.types import Key, Chord
from src.harmony.syntax.grammar import HarmonicGrammar

key = Key("C", "Major")
solver = ViterbiSolver()

print("=== 1. MEASURING K (CANDIDATES PER STEP) ===")
test_chords = [
    ("T", 64),
    ("T", 60),
    ("S", 65),
    ("D", 67),
    ("S6", 65),
    ("T6", 64),
    ("D7", 65),
    ("D65", 67),
    ("D43", 67),
    ("D2", 67),
    ("K64", 64),
    ("VII7", 68),
    ("II6", 65),
]

for fn, pitch in test_chords:
    cands_std = generate_candidate_voicings(pitch, Chord(fn), key=key, allow_extended_ranges=False)
    cands_ext = generate_candidate_voicings(pitch, Chord(fn), key=key, allow_extended_ranges=True)
    print(f"Chord {fn:5s} (S={pitch:2d}): std K = {len(cands_std):2d}, ext K = {len(cands_ext):2d}")

print("\n=== 2. RUNTIME AND COMPLEXITY ON 6, 8, 12, 16, 24, 32 CHORDS ===")
# Base 8-chord authentic cadence progression
base_melody = [64, 65, 67, 65, 64, 62, 60, 60]
base_chords = ["T", "S", "D", "T", "S6", "K64", "D7", "T"]

for n_chords in [6, 8, 12, 16, 24, 32]:
    # Tile the progression to target length
    mel = (base_melody * ((n_chords // 8) + 1))[:n_chords]
    # Ensure downbeat alternations
    mel_dicts = [{"pitch": p, "is_downbeat": (i % 2 == 0)} for i, p in enumerate(mel)]
    chords = (base_chords * ((n_chords // 8) + 1))[:n_chords]

    # Benchmark standard ranges
    t0 = time.perf_counter()
    res_std = solver.solve(mel_dicts, chords, key=key, allow_extended_ranges=False)
    t_std_ms = (time.perf_counter() - t0) * 1000

    # Benchmark extended ranges
    t0 = time.perf_counter()
    res_ext = solver.solve(mel_dicts, chords, key=key, allow_extended_ranges=True)
    t_ext_ms = (time.perf_counter() - t0) * 1000

    max_k_std = max((d.candidates_count for d in res_std.diagnostics), default=0)
    max_k_ext = max((d.candidates_count for d in res_ext.diagnostics), default=0)

    print(f"N = {n_chords:2d} chords | Std: {t_std_ms:6.2f} ms (max K={max_k_std:2d}, success={res_std.is_success}) | "
          f"Ext: {t_ext_ms:6.2f} ms (max K={max_k_ext:2d}, success={res_ext.is_success})")
