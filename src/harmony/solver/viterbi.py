"""
Global Viterbi Dynamic Programming Optimizer for four-part harmony.
Computes the globally optimal SATB voice leading trajectory over the admissible state lattice,
minimizing total voice leading cost subject to zero Brigade hard rule violations.
"""

from typing import Any, Sequence, NamedTuple
from dataclasses import dataclass
from src.harmony.core.types import (
    Voicing,
    Key,
    Chord,
    ValidationResult,
    calculate_metric_structure,
)
from src.harmony.rules.engine import RuleEngine
from src.harmony.solver.state_generator import generate_candidate_voicings


@dataclass
class SolverStepDiagnostic:
    step_index: int
    chord: str
    soprano_pitch: int
    candidates_count: int
    reachable_candidates_count: int


@dataclass
class SolverResult:
    is_success: bool
    voicings: list[Voicing] | None
    total_cost: float
    diagnostics: list[dict[str, Any]]
    message: str = ""
    step_diagnostics: list[SolverStepDiagnostic] | None = None


class ViterbiSolver:
    """
    Viterbi dynamic programming solver for classical four-part harmony.
    Complexity: O(N * K^2), where N is number of chords, K is max candidates per step.
    Runs in under 10ms for typical 8-16 bar exercises.
    """

    def __init__(self, rule_engine: RuleEngine | None = None):
        self.rule_engine = rule_engine or RuleEngine()

    def solve(
        self,
        melody: Sequence[int | dict[str, Any]],
        chords: Sequence[Chord | str],
        key: Any = None,
        allow_extended_ranges: bool = False,
        relax_soprano_intervals: bool = False,
    ) -> SolverResult:
        """
        Finds the globally optimal sequence of Voicings for the given melody and chord progression.
        """
        n = len(chords)
        if len(melody) != n or n == 0:
            msg = f"Length mismatch: melody ({len(melody)}) vs chords ({n})"
            return SolverResult(
                is_success=False,
                voicings=None,
                total_cost=float("inf"),
                diagnostics=[{
                    "step": None,
                    "chord": None,
                    "blocked": 0,
                    "message": msg,
                }],
                message=msg,
            )

        # Parse melody and chords
        melody_pitches: list[int] = []
        downbeats: list[bool] = []
        phrase_boundaries: list[bool] = []

        metric_structure = calculate_metric_structure(melody)
        has_explicit_downbeats = any(
            isinstance(m, dict) and "is_downbeat" in m for m in melody
        )
        for i, (m, metric) in enumerate(zip(melody, metric_structure)):
            if isinstance(m, dict):
                melody_pitches.append(int(m["pitch"]))
                if has_explicit_downbeats:
                    downbeats.append(bool(m.get("is_downbeat", False)))
                else:
                    downbeats.append(bool(metric.get("is_downbeat", False)))
                explicit_pb = m.get("phrase_boundary") if "phrase_boundary" in m else m.get("is_phrase_boundary")
                if explicit_pb is not None:
                    phrase_boundaries.append(bool(explicit_pb))
                else:
                    measure = metric.get("measure", 1)
                    is_pb = (measure % 4 == 0 and metric.get("is_downbeat", False)) or (i > 0 and (i % 4 == 0 or i == n // 2))
                    phrase_boundaries.append(bool(is_pb))
            else:
                melody_pitches.append(int(m))
                downbeats.append(bool(metric.get("is_downbeat", False)))
                measure = metric.get("measure", 1)
                is_pb = (measure % 4 == 0 and metric.get("is_downbeat", False)) or (i > 0 and (i % 4 == 0 or i == n // 2))
                phrase_boundaries.append(bool(is_pb))

        parsed_chords: list[Chord] = []
        for c in chords:
            if isinstance(c, Chord):
                parsed_chords.append(c)
            else:
                parsed_chords.append(Chord(function=str(c)))

        # Parse key
        parsed_key = Key.parse(key) if key is not None else Key("C", "Major")

        # Configure rule engine extended ranges
        orig_extended = getattr(self.rule_engine, "allow_extended_ranges", False)
        self.rule_engine.allow_extended_ranges = allow_extended_ranges

        try:
            # 1. Generate state lattice V[t]
            lattice: list[list[Voicing]] = []
            step_diag: list[SolverStepDiagnostic] = []

            for t in range(n):
                prev_s = melody_pitches[t - 1] if t > 0 else None
                next_s = melody_pitches[t + 1] if t + 1 < n else None
                is_db = downbeats[t]
                candidates = generate_candidate_voicings(
                    soprano_pitch=melody_pitches[t],
                    chord=parsed_chords[t],
                    key=parsed_key,
                    allow_extended_ranges=allow_extended_ranges,
                    prev_chord=parsed_chords[t - 1] if t > 0 else None,
                    prev_soprano=prev_s,
                    next_soprano=next_s,
                    is_downbeat=is_db,
                )
                lattice.append(candidates)
                step_diag.append(
                    SolverStepDiagnostic(
                        step_index=t,
                        chord=parsed_chords[t].function,
                        soprano_pitch=melody_pitches[t],
                        candidates_count=len(candidates),
                        reachable_candidates_count=0,
                    )
                )

                if len(candidates) == 0:
                    msg = f"Step {t} ({parsed_chords[t].function}): no candidate voicings found for soprano pitch {melody_pitches[t]}"
                    return SolverResult(
                        is_success=False,
                        voicings=None,
                        total_cost=float("inf"),
                        diagnostics=[{
                            "step": t,
                            "chord": parsed_chords[t].function,
                            "blocked": 0,
                            "message": msg,
                        }],
                        message=msg,
                        step_diagnostics=step_diag,
                    )

            # 2. Viterbi forward DP
            # delta[t][j] = min cost to reach candidate j at step t
            # psi[t][j] = index of best predecessor in lattice[t-1]
            delta: list[list[float]] = []
            psi: list[list[int]] = []

            # Step 0: Initial cost based on static spacing
            init_delta: list[float] = []
            for v in lattice[0]:
                res = self.rule_engine.validate(
                    prev_voicing=None,
                    curr_voicing=v,
                    prev_chord=None,
                    curr_chord=parsed_chords[0],
                    key=parsed_key,
                    is_downbeat=downbeats[0],
                    is_final_chord=(n == 1),
                    phrase_boundary=phrase_boundaries[0],
                )
                if res.is_valid and not res.has_hard_violations:
                    init_delta.append(res.cost)
                else:
                    init_delta.append(float("inf"))

            delta.append(init_delta)
            psi.append([-1] * len(lattice[0]))
            step_diag[0].reachable_candidates_count = sum(1 for c in init_delta if c < float("inf"))

            if step_diag[0].reachable_candidates_count == 0:
                msg = "Initial step 0 has no valid voicings under rule engine constraints."
                return SolverResult(
                    is_success=False,
                    voicings=None,
                    total_cost=float("inf"),
                    diagnostics=[{
                        "step": 0,
                        "chord": parsed_chords[0].function,
                        "blocked": len(lattice[0]),
                        "message": msg,
                    }],
                    message=msg,
                    step_diagnostics=step_diag,
                )

            # Steps 1 to N-1
            for t in range(1, n):
                curr_candidates = lattice[t]
                prev_candidates = lattice[t - 1]
                curr_chord = parsed_chords[t]
                prev_chord = parsed_chords[t - 1]
                is_downbeat = downbeats[t]

                step_delta: list[float] = [float("inf")] * len(curr_candidates)
                step_psi: list[int] = [-1] * len(curr_candidates)

                for j, curr_v in enumerate(curr_candidates):
                    best_cost = float("inf")
                    best_prev_idx = -1

                    for i, prev_v in enumerate(prev_candidates):
                        if delta[t - 1][i] == float("inf"):
                            continue

                        res = self.rule_engine.validate(
                            prev_voicing=prev_v,
                            curr_voicing=curr_v,
                            prev_chord=prev_chord,
                            curr_chord=curr_chord,
                            key=parsed_key,
                            is_downbeat=is_downbeat,
                            is_final_chord=(t == n - 1),
                            phrase_boundary=phrase_boundaries[t],
                        )

                        # In SATB harmonization of a given cantus firmus, soprano melodic intervals
                        # are immutable input constraints of the melody itself (such as degree 6 <-> 7
                        # in harmonic minor scales). Hard violations strictly confined to voice 0
                        # (soprano) melodic intervals must not prune the lattice for accompanying voices.
                        hard_violations = [
                            v for v in res.violations
                            if v.is_hard and not (relax_soprano_intervals and v.voices == (0,) and v.rule_id == "MELODIC_AUGMENTED_INTERVAL")
                        ]
                        if hard_violations:
                            continue

                        trans_cost = res.cost if res.cost < float("inf") else self.rule_engine.compute_soft_cost(prev_v, curr_v)
                        total_cost = delta[t - 1][i] + trans_cost
                        if total_cost < best_cost:
                            best_cost = total_cost
                            best_prev_idx = i

                    step_delta[j] = best_cost
                    step_psi[j] = best_prev_idx

                delta.append(step_delta)
                psi.append(step_psi)
                reachable = sum(1 for c in step_delta if c < float("inf"))
                step_diag[t].reachable_candidates_count = reachable

                if reachable == 0:
                    msg = f"Step {t} ({curr_chord.function}): all {len(curr_candidates)} candidates blocked by hard-rule violations from step {t-1}."
                    return SolverResult(
                        is_success=False,
                        voicings=None,
                        total_cost=float("inf"),
                        diagnostics=[{
                            "step": t,
                            "chord": curr_chord.function,
                            "blocked": len(curr_candidates),
                            "message": msg,
                        }],
                        message=msg,
                        step_diagnostics=step_diag,
                    )

            # 3. Backtrack optimal trajectory
            last_step_costs = delta[n - 1]
            best_last_idx = min(range(len(last_step_costs)), key=lambda idx: last_step_costs[idx])
            optimal_cost = last_step_costs[best_last_idx]

            if optimal_cost == float("inf"):
                msg = f"Step {n - 1} ({parsed_chords[-1].function}): final cadence unreachable or no valid path across lattice."
                return SolverResult(
                    is_success=False,
                    voicings=None,
                    total_cost=float("inf"),
                    diagnostics=[{
                        "step": n - 1,
                        "chord": parsed_chords[-1].function,
                        "blocked": len(lattice[n - 1]),
                        "message": msg,
                    }],
                    message=msg,
                    step_diagnostics=step_diag,
                )

            optimal_path: list[Voicing] = [lattice[n - 1][best_last_idx]]
            curr_idx = best_last_idx

            for t in range(n - 1, 0, -1):
                prev_idx = psi[t][curr_idx]
                optimal_path.append(lattice[t - 1][prev_idx])
                curr_idx = prev_idx

            optimal_path.reverse()

            return SolverResult(
                is_success=True,
                voicings=optimal_path,
                total_cost=optimal_cost,
                diagnostics=[],
                message="Optimal SATB trajectory found successfully.",
                step_diagnostics=step_diag,
            )
        finally:
            self.rule_engine.allow_extended_ranges = orig_extended
