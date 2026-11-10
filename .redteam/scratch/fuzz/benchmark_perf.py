"""
Benchmark Performance & Complexity:
Measures latency, scaling O(N*K^2), candidate count K per step,
and breaks down execution time across:
- Grammar plan generation
- Viterbi forward DP + state lattice generation
- Full pipeline harmonize
- FastAPI endpoint round-trip (including MusicXML colorizer)
Tested on 4, 8, 12, 16 bars (8, 16, 24, 32 notes).
"""

import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path("D:/aitraining")
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.harmony.pipeline import Harmonizer
from src.harmony.core.types import Key, Chord
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.solver.state_generator import generate_candidate_voicings

API_URL = "http://127.0.0.1:8000/api/harmonize"


def generate_benchmark_melody(num_notes: int) -> list[dict[str, Any]]:
    # Repeating viable pattern that can be harmonized
    # Pattern: E4 (64), F4 (65), G4 (67), E4 (64), D4 (62), C4 (60)
    base = [64, 65, 67, 64, 62, 60]
    pitches = []
    while len(pitches) < num_notes - 1:
        pitches.extend(base)
    pitches = pitches[: num_notes - 1]
    pitches.append(60)  # final tonic

    mel = []
    for i, p in enumerate(pitches):
        dur = "whole" if i == len(pitches) - 1 else "half"
        mel.append({"pitch": p, "duration": dur, "is_downbeat": (i % 2 == 0)})
    return mel


def benchmark():
    print("=== BENCHMARKING TIME & COMPLEXITY ===")
    harmonizer = Harmonizer()
    solver = ViterbiSolver()
    key = Key("C", "Major")

    # Bar counts: 4 bars (8 notes), 8 bars (16 notes), 12 bars (24 notes), 16 bars (32 notes)
    # Also 2 bars (4 notes)
    test_sizes = [
        ("2_bars_4_notes", 4),
        ("4_bars_8_notes", 8),
        ("8_bars_16_notes", 16),
        ("12_bars_24_notes", 24),
        ("16_bars_32_notes", 32),
    ]

    bench_records = []

    for label, num_notes in test_sizes:
        mel = generate_benchmark_melody(num_notes)
        print(f"\n--- Testing {label} (N = {num_notes}) ---")

        # 1. Grammar time
        grammar = HarmonicGrammar(key=key)
        t_g_list = []
        plans = []
        for _ in range(5):
            t0 = time.perf_counter()
            plans = grammar.generate_plans(mel, key=key, max_plans=50)
            t_g_list.append((time.perf_counter() - t0) * 1000)
        t_grammar_avg = statistics.mean(t_g_list)
        print(f"  Grammar plans count: {len(plans)}, avg time: {t_grammar_avg:.2f} ms")

        # 2. Lattice candidate size K per step
        k_values = []
        test_plan = plans[0] if plans else [Chord("T")] * num_notes
        for t, m in enumerate(mel):
            c_fn = test_plan[t] if t < len(test_plan) else Chord("T")
            cands = generate_candidate_voicings(m["pitch"], c_fn, key)
            k_values.append(len(cands))
        avg_k = statistics.mean(k_values) if k_values else 0
        max_k = max(k_values) if k_values else 0
        min_k = min(k_values) if k_values else 0
        print(f"  Lattice K: min={min_k}, max={max_k}, avg={avg_k:.1f}")

        # 3. Solver solve time per single plan
        t_s_list = []
        if plans:
            for _ in range(5):
                t0 = time.perf_counter()
                solver.solve(mel, plans[0], key)
                t_s_list.append((time.perf_counter() - t0) * 1000)
            t_solver_avg = statistics.mean(t_s_list)
        else:
            t_solver_avg = 0.0
        print(f"  Viterbi solve 1 plan: avg time: {t_solver_avg:.2f} ms")

        # 4. Pipeline harmonize (trying candidate plans until 3 solutions or max_plans)
        t_pipe_list = []
        pipe_success = False
        solutions_count = 0
        for _ in range(3):
            t0 = time.perf_counter()
            res = harmonizer.harmonize(mel, key, max_plans=50)
            t_pipe_list.append((time.perf_counter() - t0) * 1000)
            pipe_success = res.is_success
            solutions_count = len(res.solutions)
        t_pipe_avg = statistics.mean(t_pipe_list)
        print(f"  Harmonizer.harmonize: success={pipe_success}, solutions={solutions_count}, avg time: {t_pipe_avg:.2f} ms")

        # 5. Live FastAPI endpoint round-trip
        api_payload = {
            "melody": mel,
            "key": {"tonic": "C", "mode": "Major"},
            "time_signature": "4/4",
            "allow_secondary_dominants": True,
            "allow_extended_ranges": False,
            "max_plans": 50,
        }
        t_api_list = []
        server_latency = None
        for _ in range(3):
            t0 = time.perf_counter()
            try:
                r = urllib.request.Request(
                    API_URL,
                    data=json.dumps(api_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(r) as resp:
                    api_data = json.loads(resp.read().decode("utf-8"))
                    server_latency = api_data.get("latency_ms")
                t_api_list.append((time.perf_counter() - t0) * 1000)
            except Exception as e:
                print(f"  API call failed: {e}")
                t_api_list.append(None)
        valid_api_times = [t for t in t_api_list if t is not None]
        t_api_avg = statistics.mean(valid_api_times) if valid_api_times else None
        print(f"  API HTTP roundtrip: avg time: {t_api_avg:.2f} ms (server reported: {server_latency} ms)")

        # Theoretical N * K^2
        theoretical_ops = num_notes * (avg_k ** 2)

        bench_records.append({
            "label": label,
            "num_notes": num_notes,
            "lattice_k": {
                "min": min_k,
                "max": max_k,
                "avg": round(avg_k, 1),
            },
            "theoretical_N_K2": round(theoretical_ops),
            "timing_ms": {
                "grammar_plans_avg": round(t_grammar_avg, 2),
                "viterbi_single_plan_avg": round(t_solver_avg, 2),
                "harmonizer_pipeline_avg": round(t_pipe_avg, 2),
                "api_http_roundtrip_avg": round(t_api_avg, 2) if t_api_avg else None,
                "api_server_latency_ms": server_latency,
            },
            "pipeline_success": pipe_success,
            "solutions_count": solutions_count,
        })

    evidence_file = Path("D:/aitraining/.redteam/evidence/benchmark_results.json")
    evidence_file.write_text(json.dumps(bench_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved benchmark results to: {evidence_file}")


if __name__ == "__main__":
    benchmark()
