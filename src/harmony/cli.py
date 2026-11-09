"""
CLI entrypoint for the Brigade Harmony Engine.
Allows command-line harmonization of melodies with MusicXML, MIDI, and ASCII outputs.
"""

import argparse
import sys
from pathlib import Path
from src.harmony.core.types import Key
from src.harmony.pipeline import Harmonizer


def parse_melody(melody_arg: str) -> list[dict]:
    """
    Parses comma-separated MIDI pitch numbers into melody note dicts.
    Example: '64,65,67,62,60' -> [{'pitch': 64, 'is_downbeat': True}, ...]
    """
    pitches = [int(p.strip()) for p in melody_arg.split(",") if p.strip()]
    if not pitches:
        raise ValueError("Melody cannot be empty.")
    
    # Simple metric heuristic: alternate downbeat / upbeat
    return [
        {"pitch": p, "is_downbeat": (i % 2 == 0)}
        for i, p in enumerate(pitches)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Brigade Classical 4-Part Harmony Engine (Способин / Дубовский)"
    )
    parser.add_argument(
        "--melody",
        type=str,
        required=True,
        help="Comma-separated MIDI pitch numbers (e.g., '64,65,67,62,60' for E4, F4, G4, D4, C4)",
    )
    parser.add_argument(
        "--tonic",
        type=str,
        default="C",
        help="Tonic note name (default: 'C')",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="Major",
        choices=["Major", "Minor"],
        help="Mode: Major or Minor (default: Major)",
    )
    parser.add_argument(
        "--musicxml",
        type=str,
        default=None,
        help="Path to save MusicXML score (e.g. output/result.musicxml)",
    )
    parser.add_argument(
        "--midi",
        type=str,
        default=None,
        help="Path to save MIDI audio playback (e.g. output/result.mid)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Brigade Harmony Exercise",
        help="Title for the score",
    )
    parser.add_argument(
        "--time-signature",
        type=str,
        default="4/4",
        help="Time signature (meter), e.g. 4/4, 3/4, 2/4, 6/8 (default: 4/4)",
    )

    args = parser.parse_args(argv)

    try:
        melody = parse_melody(args.melody)
        key = Key(args.tonic, args.mode)
    except Exception as e:
        print(f"Error parsing inputs: {e}", file=sys.stderr)
        return 1

    print(f"Harmonizing {len(melody)} notes in {key.name} ({args.time_signature})...")
    harmonizer = Harmonizer()
    result = harmonizer.harmonize(melody=melody, key=key, time_signature=args.time_signature)

    if not result.is_success or not result.best_solution:
        print(f"FAILED: {result.message}", file=sys.stderr)
        return 2

    solution = result.best_solution
    print("\n" + solution.ascii_score)

    if args.musicxml:
        out_xml = solution.save_musicxml(args.musicxml, title=args.title)
        print(f"Saved MusicXML to {out_xml}")

    if args.midi:
        out_mid = solution.save_midi(args.midi)
        print(f"Saved MIDI to {out_mid}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
