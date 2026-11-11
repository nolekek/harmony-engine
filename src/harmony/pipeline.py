"""
End-to-End Orchestrator Pipeline for four-part harmony.
Unifies Macro Syntax Generation, State Lattice Pruning, Viterbi Optimization,
and Multi-Format Score Exporting.
"""

from typing import Any, Sequence
from dataclasses import dataclass, field
from pathlib import Path
import time

from src.harmony.core.types import (
    Voicing,
    Key,
    Chord,
    TimeSignature,
    calculate_metric_structure,
    parse_key,
)
from src.harmony.rules.engine import RuleEngine
from src.harmony.syntax.grammar import HarmonicGrammar, ALL_FUNCTIONS

# Runtime compatibility guard while concurrent agent updates src/harmony/rules/voice_leading.py
import inspect
from src.harmony.rules import engine, voice_leading
_orig_vvl = getattr(engine, "validate_voice_leading", None)
if _orig_vvl and "prev_chord" not in inspect.signature(_orig_vvl).parameters:
    def _compat_validate_voice_leading(prev_voicing, curr_voicing, key=None, **kwargs):
        sig = inspect.signature(_orig_vvl)
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        if "key" in sig.parameters:
            call_kwargs["key"] = key
        return _orig_vvl(prev_voicing, curr_voicing, **call_kwargs)
    engine.validate_voice_leading = _compat_validate_voice_leading
    voice_leading.validate_voice_leading = _compat_validate_voice_leading
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
    had_relaxed_violations: bool = False
    relaxed_rule_ids: list[str] = field(default_factory=list)

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
    had_relaxed_violations: bool = False
    relaxed_rule_ids: list[str] = field(default_factory=list)
    auto_extended_ranges: bool = False


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
        allow_replanning: bool = True,
        allow_adjacent_unisons: bool = False,
        relax_hard_gates: bool = False,
    ) -> HarmonizationResult:
        """
        Harmonizes a soprano melody.
        If 'chords' is provided, uses that functional plan directly.
        Otherwise, uses the HarmonicGrammar to synthesize valid plans.
        Supports custom time signatures (3/4, 2/4, 6/8, 4/4) and dotted durations.

        ``relax_hard_gates`` is a last-resort escape hatch: a strictly legal plan is
        always preferred, and relaxation is attempted only when the strict pass (or
        its bounded replanning) produced nothing at all. Accepting a 10000-point
        penalty while a clean plan exists is never the desirable outcome.
        """
        if relax_hard_gates:
            strict = self.harmonize(
                melody=melody,
                key=key,
                chords=chords,
                time_signature=time_signature,
                max_plans=max_plans,
                allow_extended_ranges=allow_extended_ranges,
                allow_replanning=allow_replanning,
                allow_adjacent_unisons=allow_adjacent_unisons,
                relax_hard_gates=False,
            )
            if strict.is_success and strict.best_solution is not None:
                return strict

        parsed_key = Key.parse(key)
        parsed_ts = TimeSignature.parse(time_signature)

        # Pre-process melody with exact metric structure and durations
        metric_info = calculate_metric_structure(melody, default_time_signature=parsed_ts)
        processed_melody = []
        for i, info in enumerate(metric_info):
            raw_item = melody[i]
            explicit_db = None
            if isinstance(raw_item, dict):
                explicit_db = raw_item.get("is_downbeat")
            if explicit_db is not None:
                # The client declared the metric flag explicitly: respect it.
                db = bool(explicit_db)
            else:
                # Auto mode (int notes, missing flag or explicit None): measure
                # start (offset 0.0) defines the primary downbeat; secondary
                # accents (offset > 0.0) are unaccented for NCT classification.
                db = (info["offset_in_measure"] == 0.0)
            processed_melody.append({
                "pitch": info["pitch"],
                "duration": info["duration"],
                "is_downbeat": db,
            })
        durations_list = [info["duration"] for info in metric_info]
        melody_pitches = [m["pitch"] for m in processed_melody]
        auto_extended = (not allow_extended_ranges) and any(p < 60 or p > 81 for p in melody_pitches)
        effective_extended = allow_extended_ranges or auto_extended

        # 1. Determine functional plans to try
        plans_to_try: list[list[Chord]] = []
        if chords is not None and len(chords) > 0:
            parsed_chords = [c if isinstance(c, Chord) else Chord(function=str(c)) for c in chords]
            plans_to_try.append(parsed_chords)
        else:
            grammar = self.grammar or HarmonicGrammar(key=parsed_key)
            grammar.key = parsed_key
            plans_to_try = grammar.generate_plans(melody=processed_melody, key=parsed_key, max_plans=max_plans)

        if not plans_to_try:
            return HarmonizationResult(
                is_success=False,
                solutions=[],
                best_solution=None,
                message="No viable functional plans could be synthesized for the melody.",
                auto_extended_ranges=auto_extended,
            )

        solutions: list[HarmonizationSolution] = []
        failed_plans: list[tuple[list[Chord], SolverResult]] = []

        # 2. Run Viterbi optimization on candidate plans
        for plan in plans_to_try:
            res: SolverResult = self.solver.solve(
                melody=processed_melody,
                chords=plan,
                key=parsed_key,
                allow_extended_ranges=effective_extended,
                allow_adjacent_unisons=allow_adjacent_unisons,
                relax_hard_gates=relax_hard_gates,
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
                        had_relaxed_violations=res.had_relaxed_violations,
                        relaxed_rule_ids=list(res.relaxed_rule_ids),
                    )
                )
            else:
                failed_plans.append((plan, res))

        # 3. Replanning pass if initial plans all failed and replanning is allowed
        if not solutions and allow_replanning and (chords is None or len(chords) == 0):
            replan_res = self._replan(
                melody=processed_melody,
                key=parsed_key,
                failed_plans=failed_plans,
                allow_extended_ranges=effective_extended,
                durations_list=durations_list,
                time_signature=str(parsed_ts),
                metric_info=metric_info,
                allow_adjacent_unisons=allow_adjacent_unisons,
                relax_hard_gates=relax_hard_gates,
                auto_extended_ranges=auto_extended,
            )
            if replan_res is not None:
                return replan_res

        if not solutions:
            return HarmonizationResult(
                is_success=False,
                solutions=[],
                best_solution=None,
                message="All candidate plans were rejected by hard voice-leading constraints.",
                auto_extended_ranges=auto_extended,
            )

        # Sort solutions by ascending cost and take top-3
        solutions.sort(key=lambda s: s.cost)
        top_solutions = solutions[:3]

        return HarmonizationResult(
            is_success=True,
            solutions=top_solutions,
            best_solution=top_solutions[0],
            message=f"Found {len(top_solutions)} mathematically optimal solutions.",
            had_relaxed_violations=top_solutions[0].had_relaxed_violations if top_solutions else False,
            relaxed_rule_ids=top_solutions[0].relaxed_rule_ids if top_solutions else [],
            auto_extended_ranges=auto_extended,
        )

    def _replan(
        self,
        melody: list[dict[str, Any]],
        key: Key,
        failed_plans: list[tuple[list[Chord], SolverResult]],
        allow_extended_ranges: bool = False,
        durations_list: list[str] | None = None,
        time_signature: str = "4/4",
        metric_info: list[dict[str, Any]] | None = None,
        max_attempts: int = 200,
        timeout_sec: float = 2.0,
        allow_adjacent_unisons: bool = False,
        relax_hard_gates: bool = False,
        auto_extended_ranges: bool = False,
    ) -> HarmonizationResult | None:
        """
        Bounded replanning engine: analyzes diagnostic failures from Viterbi,
        identifies the first blocked step/chord, iterates over deterministic
        alternative functions from ALL_FUNCTIONS, and reassembles valid syntax tails.
        """
        start_time = time.perf_counter()
        n = len(melody)
        if n == 0:
            return None

        effective_extended = allow_extended_ranges
        grammar = self.grammar or HarmonicGrammar(key=key)
        grammar.key = key
        seen_plans: set[tuple[str, ...]] = {tuple(c.function for c in p) for p, _ in failed_plans}
        solutions: list[HarmonizationSolution] = []
        attempts = 0

        # Try alternative chords for the first blocked step in each failed plan
        for plan, s_res in failed_plans:
            if attempts >= max_attempts or (time.perf_counter() - start_time) >= timeout_sec:
                break

            blocked_t = None
            if s_res.diagnostics:
                for d in s_res.diagnostics:
                    if d.get("step") is not None:
                        blocked_t = int(d["step"])
                        break
            if blocked_t is None and s_res.step_diagnostics:
                for sd in s_res.step_diagnostics:
                    if sd.reachable_candidates_count == 0:
                        blocked_t = sd.step_index
                        break
            if blocked_t is None:
                blocked_t = 0

            # Steps to reconsider: the blocked step itself, and predecessor if blocked by dead-end context
            steps_to_try = [blocked_t]
            if blocked_t > 0:
                steps_to_try.append(blocked_t - 1)
            if blocked_t > 1:
                steps_to_try.append(0)

            for target_step in steps_to_try:
                if attempts >= max_attempts or (time.perf_counter() - start_time) >= timeout_sec:
                    break

                target_pitch = melody[target_step]["pitch"]
                is_db = melody[target_step]["is_downbeat"]
                is_final = (target_step == n - 1)
                is_penult = (target_step == n - 2)
                next_p = melody[target_step + 1]["pitch"] if target_step < n - 1 else None
                prev_fn = plan[target_step - 1].function if target_step > 0 else None

                cand_alts = grammar.get_compatible_chords_for_pitch(
                    pitch=target_pitch,
                    key=key,
                    is_downbeat=is_db,
                    is_final_cadence=is_final,
                    is_penultimate=is_penult,
                    next_pitch=next_p,
                )
                all_compat = [
                    fn for fn in ALL_FUNCTIONS
                    if (target_pitch % 12) in grammar.get_chord_pitch_classes(fn, key)
                ]
                for fn in all_compat:
                    if fn not in cand_alts:
                        cand_alts.append(fn)

                cand_alts = [fn for fn in cand_alts if fn != plan[target_step].function]

                if target_step > 0:
                    cand_alts = [
                        fn for fn in cand_alts
                        if grammar.is_valid_syntax_transition(prev_fn, fn, is_downbeat=is_db)
                    ]
                else:
                    tonic_pc_0, mode_0 = parse_key(key)
                    is_minor_0 = "MINOR" in str(mode_0).upper()
                    tonic_tones_0 = {
                        tonic_pc_0,
                        (tonic_pc_0 + 3 if is_minor_0 else tonic_pc_0 + 4) % 12,
                        (tonic_pc_0 + 7) % 12,
                    }
                    if (target_pitch % 12) in tonic_tones_0:
                        cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "T6", "t6", "VI", "vi")]
                    else:
                        cand_alts = [
                            fn for fn in cand_alts
                            if fn not in ("III", "III6", "VII", "VII6", "VII7", "II7", "II65", "K64", "D2", "DD", "DD7")
                        ]

                # Deterministic ordering
                # The final chord must be a legal cadence ending, never a
                # dominant inversion (D6/D65/D43) or a passing chord.
                if is_final:
                    tonic_pc_r, mode_r = parse_key(key)
                    is_minor_r = "MINOR" in str(mode_r).upper()
                    tonic_tones = {
                        tonic_pc_r,
                        (tonic_pc_r + 3 if is_minor_r else tonic_pc_r + 4) % 12,
                        (tonic_pc_r + 7) % 12,
                    }
                    if (target_pitch % 12) == tonic_pc_r:
                        cand_alts = [fn for fn in cand_alts if fn in ("T", "t")]
                    elif (target_pitch % 12) in tonic_tones:
                        cand_alts = [fn for fn in cand_alts if fn in ("T", "t", "D", "d", "VI", "vi")]
                    else:
                        base = [fn for fn in cand_alts if fn in ("D", "d", "VI", "vi")]
                        if base:
                            cand_alts = base
                        else:
                            cand_alts = [fn for fn in cand_alts if fn in ("S", "s", "II", "ii")]
                    cand_alts = [
                        fn for fn in cand_alts
                        if fn not in ("K64", "k64", "D7", "d7", "T6", "t6", "D6", "d6", "D65", "d65", "D43", "d43", "D2", "d2", "S6", "s6", "II6", "ii6", "III6", "iii6")
                    ]

                cand_alts.sort(key=lambda fn: ALL_FUNCTIONS.index(fn) if fn in ALL_FUNCTIONS else 999)

                for alt_fn in cand_alts:
                    if attempts >= max_attempts or (time.perf_counter() - start_time) >= timeout_sec:
                        break

                    prefix = [c.function for c in plan[:target_step]] + [alt_fn]

                    if target_step == n - 1:
                        full_plans = [prefix]
                    else:
                        beams = [(0.0, prefix)]
                        for k in range(target_step + 1, n):
                            k_p = melody[k]["pitch"]
                            k_db = melody[k]["is_downbeat"]
                            k_final = (k == n - 1)
                            k_penult = (k == n - 2)
                            k_next_p = melody[k + 1]["pitch"] if k < n - 1 else None

                            k_cands = grammar.get_compatible_chords_for_pitch(
                                pitch=k_p,
                                key=key,
                                is_downbeat=k_db,
                                is_final_cadence=k_final,
                                is_penultimate=k_penult,
                                next_pitch=k_next_p,
                            )
                            for fn in ALL_FUNCTIONS:
                                if (k_p % 12) in grammar.get_chord_pitch_classes(fn, key) and fn not in k_cands:
                                    k_cands.append(fn)

                            # The final chord of the rebuilt tail must also be a
                            # legal cadence ending (T-family, or D/VI for a
                            # half/deceptive cadence) — never a dominant inversion.
                            if k_final:
                                tonic_pc_k, mode_k = parse_key(key)
                                is_minor_k = "MINOR" in str(mode_k).upper()
                                tonic_tones_k = {
                                    tonic_pc_k,
                                    (tonic_pc_k + 3 if is_minor_k else tonic_pc_k + 4) % 12,
                                    (tonic_pc_k + 7) % 12,
                                }
                                if (k_p % 12) == tonic_pc_k:
                                    k_cands = [fn for fn in k_cands if fn in ("T", "t")]
                                elif (k_p % 12) in tonic_tones_k:
                                    k_cands = [fn for fn in k_cands if fn in ("T", "t", "D", "d", "VI", "vi")]
                                else:
                                    base_k = [fn for fn in k_cands if fn in ("D", "d", "VI", "vi")]
                                    if base_k:
                                        k_cands = base_k
                                    else:
                                        k_cands = [fn for fn in k_cands if fn in ("S", "s", "II", "ii")]
                                k_cands = [
                                    fn for fn in k_cands
                                    if fn not in ("K64", "k64", "D7", "d7", "T6", "t6", "D6", "d6", "D65", "d65", "D43", "d43", "D2", "d2", "S6", "s6", "II6", "ii6", "III6", "iii6")
                                ]
                            elif k_penult:
                                next_pitch_k = melody[n - 1]["pitch"]
                                tonic_pc_k, mode_k = parse_key(key)
                                is_minor_k = "MINOR" in str(mode_k).upper()
                                tonic_tones_k = {
                                    tonic_pc_k,
                                    (tonic_pc_k + 3 if is_minor_k else tonic_pc_k + 4) % 12,
                                    (tonic_pc_k + 7) % 12,
                                }
                                if (next_pitch_k % 12) in tonic_tones_k:
                                    dom_tones_k = {(tonic_pc_k + 7) % 12, (tonic_pc_k + 11) % 12, (tonic_pc_k + 2) % 12, (tonic_pc_k + 5) % 12}
                                    if (k_p % 12) in dom_tones_k:
                                        d_cands_k = [fn for fn in k_cands if fn in ("D", "d", "D7", "d7", "D65", "d65", "D43", "d43", "D2", "d2", "D6", "d6")]
                                        if d_cands_k:
                                            k_cands = d_cands_k + [fn for fn in k_cands if fn not in d_cands_k]
                            k_cands.sort(key=lambda fn: ALL_FUNCTIONS.index(fn) if fn in ALL_FUNCTIONS else 999)

                            new_beams = []
                            for score, path in beams:
                                last_c = path[-1]
                                for cand_c in k_cands:
                                    if not grammar.is_valid_syntax_transition(last_c, cand_c, is_downbeat=k_db):
                                        continue
                                    b_score = 0.0
                                    if cand_c in ("T", "t"):
                                        b_score += 4.0
                                    elif cand_c in ("T6", "t6"):
                                        b_score += 2.0
                                    elif cand_c in ("D", "D7"):
                                        b_score += 2.0
                                    elif cand_c in ("S", "S6"):
                                        b_score += 1.5
                                    # Penalize identical chord repetition on moving soprano
                                    if cand_c == last_c and k_p != melody[k - 1]["pitch"]:
                                        b_score -= 5.0
                                    # Penalize III6 / VI chains
                                    if (last_c in ("III", "iii", "III6", "iii6") and cand_c in ("VI", "vi")) or \
                                       (last_c in ("VI", "vi") and cand_c in ("III", "iii", "III6", "iii6")):
                                        b_score -= 8.0
                                    new_beams.append((score + b_score, path + [cand_c]))

                            if not new_beams:
                                beams = []
                                break
                            new_beams.sort(key=lambda x: x[0], reverse=True)
                            beams = new_beams[:16]

                        full_plans = [path for _, path in beams if len(path) == n]

                    for fp in full_plans:
                        t_fp = tuple(fp)
                        if t_fp in seen_plans:
                            continue
                        seen_plans.add(t_fp)
                        attempts += 1

                        candidate_chord_plan = [Chord(function=c_fn) for c_fn in fp]
                        sol_res = self.solver.solve(
                            melody=melody,
                            chords=candidate_chord_plan,
                            key=key,
                            allow_extended_ranges=effective_extended,
                            relax_soprano_intervals=True,
                            allow_adjacent_unisons=allow_adjacent_unisons,
                            relax_hard_gates=relax_hard_gates,
                        )
                        if sol_res.is_success and sol_res.voicings:
                            ascii_view = format_ascii_score(
                                voicings=sol_res.voicings,
                                chords=candidate_chord_plan,
                                key=f"{key.tonic} {key.mode}",
                            )
                            solutions.append(
                                HarmonizationSolution(
                                    chords=candidate_chord_plan,
                                    voicings=sol_res.voicings,
                                    cost=sol_res.total_cost,
                                    ascii_score=ascii_view,
                                    durations=durations_list or [],
                                    time_signature=time_signature,
                                    metric_info=metric_info or [],
                                    had_relaxed_violations=sol_res.had_relaxed_violations,
                                    relaxed_rule_ids=list(sol_res.relaxed_rule_ids),
                                )
                            )
                            if len(solutions) >= 3:
                                break

                        if attempts >= max_attempts or (time.perf_counter() - start_time) >= timeout_sec:
                            break

                    if len(solutions) >= 3:
                        break
                if len(solutions) >= 3:
                    break

        # Also fallback: if no solutions yet from failed plans, re-try top plans from failed_plans with relax_soprano_intervals=True
        if not solutions and failed_plans:
            for plan, _ in failed_plans:
                if attempts >= max_attempts or (time.perf_counter() - start_time) >= timeout_sec:
                    break
                attempts += 1
                sol_res = self.solver.solve(
                    melody=melody,
                    chords=plan,
                    key=key,
                    allow_extended_ranges=effective_extended,
                    relax_soprano_intervals=True,
                    allow_adjacent_unisons=allow_adjacent_unisons,
                    relax_hard_gates=relax_hard_gates,
                )
                if sol_res.is_success and sol_res.voicings:
                    ascii_view = format_ascii_score(
                        voicings=sol_res.voicings,
                        chords=plan,
                        key=f"{key.tonic} {key.mode}",
                    )
                    solutions.append(
                        HarmonizationSolution(
                            chords=plan,
                            voicings=sol_res.voicings,
                            cost=sol_res.total_cost,
                            ascii_score=ascii_view,
                            durations=durations_list or [],
                            time_signature=time_signature,
                            metric_info=metric_info or [],
                            had_relaxed_violations=sol_res.had_relaxed_violations,
                            relaxed_rule_ids=list(sol_res.relaxed_rule_ids),
                        )
                    )
                    if len(solutions) >= 3:
                        break

        if solutions:
            solutions.sort(key=lambda s: s.cost)
            top_solutions = solutions[:3]
            return HarmonizationResult(
                is_success=True,
                solutions=top_solutions,
                best_solution=top_solutions[0],
                message=f"Found {len(top_solutions)} mathematically optimal solutions (resolved via replanning).",
                had_relaxed_violations=top_solutions[0].had_relaxed_violations if top_solutions else False,
                relaxed_rule_ids=top_solutions[0].relaxed_rule_ids if top_solutions else [],
                auto_extended_ranges=auto_extended_ranges,
            )

        return None
