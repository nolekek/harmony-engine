"""
Benchmark CLI for SATB Harmonization pipeline.
Measures total latency and per-stage timings across various melody lengths.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Sequence

# Ensure project root is in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.harmony.pipeline import Harmonizer
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver import state_generator, viterbi
from src.harmony.rules.engine import RuleEngine


DEFAULT_MELODIES: dict[int, list[int]] = {
    4: [64, 65, 62, 60],
    8: [64, 65, 64, 65, 64, 62, 62, 60],
    16: [64, 65, 64, 65, 64, 62, 62, 60] * 2,
    32: [64, 65, 64, 65, 64, 62, 62, 60] * 4,
    64: [64, 65, 64, 65, 64, 62, 62, 60] * 8,
}


def benchmark_single(
    melody: Sequence[int | dict[str, Any]],
    key: str = "C Major",
    allow_extended_ranges: bool = False,
) -> dict[str, Any]:
    """Runs harmonization once with stage instrumentation."""
    times = {
        "generate_plans": 0.0,
        "state_generator": 0.0,
        "validate": 0.0,
        "replanning": 0.0,
    }

    orig_gp = HarmonicGrammar.generate_plans
    def timed_gp(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return orig_gp(*args, **kwargs)
        finally:
            times["generate_plans"] += time.perf_counter() - t0

    orig_gcv = state_generator.generate_candidate_voicings
    def timed_gcv(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return orig_gcv(*args, **kwargs)
        finally:
            times["state_generator"] += time.perf_counter() - t0

    orig_val = RuleEngine.validate
    def timed_val(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return orig_val(*args, **kwargs)
        finally:
            times["validate"] += time.perf_counter() - t0

    orig_rep = Harmonizer._replan
    def timed_rep(*args: Any, **kwargs: Any) -> Any:
        t0 = time.perf_counter()
        try:
            return orig_rep(*args, **kwargs)
        finally:
            times["replanning"] += time.perf_counter() - t0

    # Apply temporary hooks
    HarmonicGrammar.generate_plans = timed_gp
    state_generator.generate_candidate_voicings = timed_gcv
    viterbi.generate_candidate_voicings = timed_gcv
    RuleEngine.validate = timed_val
    Harmonizer._replan = timed_rep

    try:
        harmonizer = Harmonizer()
        t_start = time.perf_counter()
        res = harmonizer.harmonize(
            melody=melody,
            key=key,
            allow_extended_ranges=allow_extended_ranges,
        )
        total_sec = time.perf_counter() - t_start
    finally:
        HarmonicGrammar.generate_plans = orig_gp
        state_generator.generate_candidate_voicings = orig_gcv
        viterbi.generate_candidate_voicings = orig_gcv
        RuleEngine.validate = orig_val
        Harmonizer._replan = orig_rep

    return {
        "length": len(melody),
        "total_ms": total_sec * 1000.0,
        "gp_ms": times["generate_plans"] * 1000.0,
        "sg_ms": times["state_generator"] * 1000.0,
        "val_ms": times["validate"] * 1000.0,
        "replan_ms": times["replanning"] * 1000.0,
        "is_success": res.is_success,
        "solutions_count": len(res.solutions) if res.solutions else 0,
        "best_cost": res.best_solution.cost if res.best_solution else None,
    }


def run_benchmarks(
    lengths: list[int],
    runs: int = 1,
    key: str = "C Major",
) -> list[dict[str, Any]]:
    results = []
    for length in lengths:
        if length not in DEFAULT_MELODIES:
            # Generate repeated base phrase to desired length
            base = DEFAULT_MELODIES[8]
            mel = (base * ((length // 8) + 1))[:length]
        else:
            mel = DEFAULT_MELODIES[length]

        run_records = []
        for _ in range(runs):
            rec = benchmark_single(mel, key=key)
            run_records.append(rec)

        # Average results over runs
        avg_total = sum(r["total_ms"] for r in run_records) / runs
        avg_gp = sum(r["gp_ms"] for r in run_records) / runs
        avg_sg = sum(r["sg_ms"] for r in run_records) / runs
        avg_val = sum(r["val_ms"] for r in run_records) / runs
        avg_replan = sum(r["replan_ms"] for r in run_records) / runs
        last = run_records[-1]

        summary = {
            "length": length,
            "total_ms": avg_total,
            "gp_ms": avg_gp,
            "sg_ms": avg_sg,
            "val_ms": avg_val,
            "replan_ms": avg_replan,
            "is_success": last["is_success"],
            "solutions_count": last["solutions_count"],
            "best_cost": last["best_cost"],
        }
        results.append(summary)

    return results


def print_table(results: list[dict[str, Any]]) -> None:
    header = (
        f"{'Length':>8} | {'Total (ms)':>10} | {'Grammar (ms)':>12} | "
        f"{'StateGen (ms)':>13} | {'Validate (ms)':>13} | {'Replan (ms)':>11} | "
        f"{'Success':>7} | {'Solutions':>9} | {'Best Cost':>9}"
    )
    separator = "-" * len(header)
    print("\n" + separator)
    print(header)
    print(separator)
    for r in results:
        cost_str = f"{r['best_cost']:.2f}" if r["best_cost"] is not None else "N/A"
        print(
            f"{r['length']:>8} | {r['total_ms']:>10.2f} | {r['gp_ms']:>12.2f} | "
            f"{r['sg_ms']:>13.2f} | {r['val_ms']:>13.2f} | {r['replan_ms']:>11.2f} | "
            f"{str(r['is_success']):>7} | {r['solutions_count']:>9} | {cost_str:>9}"
        )
    print(separator + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark SATB Harmonizer performance")
    parser.add_argument(
        "--lengths",
        type=str,
        default="4,8,16,32,64",
        help="Comma-separated melody lengths to test (default: 4,8,16,32,64)",
    )
    parser.add_argument(
        "--key",
        type=str,
        default="C Major",
        help="Key for harmonization (default: C Major)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per melody length for averaging (default: 1)",
    )
    args = parser.parse_args()

    try:
        lengths = [int(x.strip()) for x in args.lengths.split(",") if x.strip()]
    except ValueError:
        print(f"Error parsing --lengths: {args.lengths}", file=sys.stderr)
        return 1

    print(f"Starting SATB Harmonizer benchmark (key='{args.key}', runs={args.runs})...")
    results = run_benchmarks(lengths=lengths, runs=args.runs, key=args.key)
    print_table(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
