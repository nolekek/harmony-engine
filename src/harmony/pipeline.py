"""
End-to-End Orchestrator Pipeline for four-part harmony.
Unifies Macro Syntax Generation, State Lattice Pruning, Viterbi Optimization,
and Multi-Format Score Exporting.
"""

from typing import Any, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from src.harmony.core.types import (
    Voicing,
    Key,
    Chord,
    TimeSignature,
    calculate_metric_structure,
)
from src.harmony.rules.engine import RuleEngine
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver, SolverResult
from src.harmony.export.musicxml import export_to_musicxml
from src.harmony.export.midi import export_to_midi
from src.harmony.export.ascii import format_ascii_score


@dataclass
class HarmonizationSolution:
    chords: list[Chord]
    voicings: list[Voicing]
    cost: float
    ascii_score: str
    durations: list[str] = field(default_factory=list)
    time_signature: str = "4/4"
    metric_info: list[dict[str, Any]] = field(default_factory=list)

    def to_musicxml(self, title: str = "Harmonization Exercise") -> str:
        return export_to_musicxml(
            self.voicings,
            self.chords,
            title=title,
            durations=self.durations,
            time_signature=self.time_signature,
        )

    def save_musicxml(self, output_path: str | Path, title: str = "Harmonization Exercise") -> Path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(self.to_musicxml(title=title), encoding="utf-8")
        return p

    def save_midi(self, output_path: str | Path, bpm: int = 80) -> Path:
        return export_to_midi(
            self.voicings,
            output_path,
            bpm=bpm,
            durations=self.durations,
            time_signature=self.time_signature,
        )


@dataclass
class HarmonizationResult:
    is_success: bool
    solutions: list[HarmonizationSolution]
    best_solution: HarmonizationSolution | None
    message: str = ""


class Harmonizer:
    """
    Complete end-to-end Classical Harmony Engine.
    Harmonizes any given soprano melody according to the Brigade textbook rules.
    """

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        solver: ViterbiSolver | None = None,
        grammar: HarmonicGrammar | None = None,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.solver = solver or ViterbiSolver(rule_engine=self.rule_engine)
        self.grammar = grammar or HarmonicGrammar()

    def harmonize(
        self,
        melody: Sequence[int | dict[str, Any]],
        key: Key | str,
        chords: Sequence[Chord | str] | None = None,
        time_signature: Any = "4/4",
        max_plans: int = 60,
        allow_extended_ranges: bool = False,
    ) -> HarmonizationResult:
        """
        Harmonizes a soprano melody.
        If 'chords' is provided, uses that functional plan directly.
        Otherwise, uses the HarmonicGrammar to synthesize valid plans.
        Supports custom time signatures (3/4, 2/4, 6/8, 4/4) and dotted durations.
        """
        parsed_key = Key.parse(key)
        parsed_ts = TimeSignature.parse(time_signature)

        # Pre-process melody with exact metric structure and durations
        metric_info = calculate_metric_structure(melody, default_time_signature=parsed_ts)
        processed_melody = []
        for i, info in enumerate(metric_info):
            raw_item = melody[i]
            if isinstance(raw_item, dict) and "is_downbeat" in raw_item and raw_item["is_downbeat"] is not None:
                db = bool(raw_item["is_downbeat"])
            elif isinstance(raw_item, int) or (isinstance(raw_item, dict) and "is_downbeat" not in raw_item):
                # When downbeats are not explicitly declared, measure start (offset 0.0)
                # defines the primary downbeat; secondary accents (offset > 0.0) are
                # unaccented for NCT melodic classifications.
                db = (info["offset_in_measure"] == 0.0)
            else:
                db = bool(info["is_downbeat"])
            processed_melody.append({
                "pitch": info["pitch"],
                "duration": info["duration"],
                "is_downbeat": db,
            })
        durations_list = [info["duration"] for info in metric_info]

        # 1. Determine functional plans to try
        plans_to_try: list[list[Chord]] = []
        if chords is not None and len(chords) > 0:
            parsed_chords = [c if isinstance(c, Chord) else Chord(function=str(c)) for c in chords]
            plans_to_try.append(parsed_chords)
        else:
            grammar = HarmonicGrammar(key=parsed_key)
            plans_to_try = grammar.generate_plans(melody=processed_melody, key=parsed_key, max_plans=max_plans)

        if not plans_to_try:
            return HarmonizationResult(
                is_success=False,
                solutions=[],
                best_solution=None,
                message="No viable functional plans could be synthesized for the melody.",
            )

        solutions: list[HarmonizationSolution] = []

        # 2. Run Viterbi optimization on candidate plans
        for plan in plans_to_try:
            res: SolverResult = self.solver.solve(
                melody=processed_melody,
                chords=plan,
                key=parsed_key,
                allow_extended_ranges=allow_extended_ranges,
            )

            if res.is_success and res.voicings:
                ascii_view = format_ascii_score(
                    voicings=res.voicings,
                    chords=plan,
                    key=f"{parsed_key.tonic} {parsed_key.mode}",
                )
                solutions.append(
                    HarmonizationSolution(
                        chords=plan,
                        voicings=res.voicings,
                        cost=res.total_cost,
                        ascii_score=ascii_view,
                        durations=durations_list,
                        time_signature=str(parsed_ts),
                        metric_info=metric_info,
                    )
                )

        if not solutions:
            return HarmonizationResult(
                is_success=False,
                solutions=[],
                best_solution=None,
                message="All candidate plans were rejected by hard voice-leading constraints.",
            )

        # Sort solutions by ascending cost and take top-3
        solutions.sort(key=lambda s: s.cost)
        top_solutions = solutions[:3]

        return HarmonizationResult(
            is_success=True,
            solutions=top_solutions,
            best_solution=top_solutions[0],
            message=f"Found {len(top_solutions)} mathematically optimal solutions.",
        )
