"""
Synthetic SATB Harmony Dataset Generator.
Synthesizes tens of thousands of textbook-compliant 4-part harmony training pairs
(soprano melody -> SATB voicings + functional progression) using Harmonizer (Grammar + Viterbi DP).

Output format: JSON Lines (.jsonl) ready for training lightweight neural models (Bi-GRU / Transformer).
"""

import argparse
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# Ensure workspace root is in sys.path
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from src.harmony.core.types import Key
from src.harmony.pipeline import Harmonizer

ALL_KEYS = [
    # Major keys
    ("C", "Major"), ("G", "Major"), ("D", "Major"), ("A", "Major"),
    ("E", "Major"), ("B", "Major"), ("F", "Major"), ("Bb", "Major"),
    ("Eb", "Major"), ("Ab", "Major"),
    # Minor keys
    ("A", "MinorHarmonic"), ("E", "MinorHarmonic"), ("B", "MinorHarmonic"),
    ("D", "MinorHarmonic"), ("G", "MinorHarmonic"), ("C", "MinorHarmonic"),
    ("F", "MinorHarmonic"),
]

MAJOR_SCALE_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_HARMONIC_STEPS = [0, 2, 3, 5, 7, 8, 11]

NOTE_TO_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def get_scale_pitches(tonic: str, mode: str, min_pitch: int = 60, max_pitch: int = 77) -> list[int]:
    """Generates all admissible soprano pitches for the given key in range [C4..F5]."""
    tonic_pc = NOTE_TO_PC.get(tonic, 0)
    steps = MINOR_HARMONIC_STEPS if "minor" in mode.lower() else MAJOR_SCALE_STEPS
    scale_pcs = {(tonic_pc + s) % 12 for s in steps}

    return [p for p in range(min_pitch, max_pitch + 1) if p % 12 in scale_pcs]


def generate_classical_melody(tonic: str, mode: str, length: int = 8, rng: random.Random | None = None) -> list[int]:
    """
    Synthesizes a musically coherent soprano line following classical period syntax:
    - Stepwise motion with occasional consonant leaps (3rds, 4ths, 5ths).
    - Cadence formulas ending on tonic (scale degree 1) or dominant (scale degree 5 or 2).
    """
    r = rng or random.Random()
    pitches = get_scale_pitches(tonic, mode)
    if not pitches:
        pitches = [60, 62, 64, 65, 67, 69, 71, 72]

    tonic_pc = NOTE_TO_PC.get(tonic, 0)
    tonic_candidates = [p for p in pitches if p % 12 == tonic_pc]
    mediant_candidates = [p for p in pitches if p % 12 == (tonic_pc + (3 if "minor" in mode.lower() else 4)) % 12]
    dominant_candidates = [p for p in pitches if p % 12 == (tonic_pc + 7) % 12]
    supertonic_candidates = [p for p in pitches if p % 12 == (tonic_pc + 2) % 12]

    # Start note: typically 1, 3, or 5 in soprano register [60..72]
    start_pool = (tonic_candidates + mediant_candidates + dominant_candidates) or pitches
    current = r.choice(start_pool)
    melody = [current]

    for i in range(1, length - 2):
        # Prefer step motion (neighboring scale pitches)
        curr_idx = pitches.index(current) if current in pitches else len(pitches) // 2
        step_options = []
        if curr_idx > 0:
            step_options.append(pitches[curr_idx - 1])
        if curr_idx < len(pitches) - 1:
            step_options.append(pitches[curr_idx + 1])
        if curr_idx > 1:
            step_options.append(pitches[curr_idx - 2])  # 3rd down
        if curr_idx < len(pitches) - 2:
            step_options.append(pitches[curr_idx + 2])  # 3rd up

        weights = [3, 3, 1, 1][:len(step_options)]
        current = r.choices(step_options, weights=weights)[0]
        melody.append(current)

    # Penultimate note: supertonic (degree 2) or leading tone (degree 7)
    penult_pool = supertonic_candidates or dominant_candidates or pitches
    penult = r.choice(penult_pool)
    melody.append(penult)

    # Final note: tonic (degree 1)
    final_pool = tonic_candidates or pitches
    # Choose final closest to penult
    final = min(final_pool, key=lambda p: abs(p - penult))
    melody.append(final)

    return melody


def harmonize_single_sample(sample_id: int, tonic: str, mode: str, length: int, seed: int) -> dict[str, Any] | None:
    """Harmonizes one synthetic melody into a verified dataset record."""
    rng = random.Random(seed)
    melody = generate_classical_melody(tonic, mode, length=length, rng=rng)
    key = Key(tonic=tonic, mode=mode)

    harmonizer = Harmonizer()
    res = harmonizer.harmonize(melody=melody, key=key, max_plans=3)

    if not res.is_success or not res.best_solution:
        return None

    best = res.best_solution
    satb_tuples = [
        {"soprano": v.soprano, "alto": v.alto, "tenor": v.tenor, "bass": v.bass}
        for v in best.voicings
    ]

    return {
        "id": f"sample_{sample_id:06d}",
        "key": {"tonic": tonic, "mode": mode},
        "melody": melody,
        "functions": [c.function for c in best.chords],
        "satb": satb_tuples,
        "cost": round(best.cost, 3),
        "num_chords": len(melody),
    }


def generate_batch(start_id: int, count: int, base_seed: int) -> list[dict[str, Any]]:
    """Worker task to generate a batch of samples."""
    samples: list[dict[str, Any]] = []
    for i in range(count):
        sid = start_id + i
        seed = base_seed + sid * 31
        rng = random.Random(seed)
        tonic, mode = rng.choice(ALL_KEYS)
        length = rng.choice([6, 7, 8, 9, 10])

        rec = harmonize_single_sample(sid, tonic, mode, length, seed)
        if rec:
            samples.append(rec)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic SATB Harmony Dataset Generator")
    parser.add_argument("--count", type=int, default=1000, help="Target number of verified samples")
    parser.add_argument("--output", type=str, default="output/harmony_dataset.jsonl", help="Output .jsonl path")
    parser.add_argument("--workers", type=int, default=4, help="Number of worker processes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"=== SATB Dataset Generator ===")
    print(f"Target count: {args.count}")
    print(f"Output path:  {out_path}")
    print(f"Workers:      {args.workers}")
    print(f"Base seed:    {args.seed}")

    start_time = time.time()
    collected: list[dict[str, Any]] = []
    chunk_size = 20
    next_id = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        active_futures = set()
        
        # Prime initial tasks
        for _ in range(args.workers * 2):
            active_futures.add(executor.submit(generate_batch, next_id, chunk_size, args.seed))
            next_id += chunk_size

        while active_futures and len(collected) < args.count:
            # Wait for at least one future to complete
            done_futures = []
            for f in as_completed(active_futures):
                done_futures.append(f)
                break

            for f in done_futures:
                active_futures.remove(f)
                res = f.result()
                collected.extend(res)
                print(f"Progress: {min(len(collected), args.count)}/{args.count} samples synthesized...", end="\r", flush=True)

                if len(collected) < args.count:
                    active_futures.add(executor.submit(generate_batch, next_id, chunk_size, args.seed))
                    next_id += chunk_size

        # Cancel any remaining pending futures
        for f in active_futures:
            f.cancel()

    # Trim to exact count
    final_samples = collected[:args.count]

    # Write to JSON Lines
    with open(out_path, "w", encoding="utf-8") as f:
        for s in final_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    elapsed = time.time() - start_time
    rate = len(final_samples) / elapsed if elapsed > 0 else 0

    print()
    print(f"Done! Successfully generated {len(final_samples)} verified SATB harmony pairs.")
    print(f"Elapsed time: {elapsed:.2f}s ({rate:.1f} samples/sec)")
    print(f"Saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
