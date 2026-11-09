"""
Global Viterbi Dynamic Programming Optimizer for four-part harmony.
Computes the globally optimal SATB voice leading trajectory over the admissible state lattice,
minimizing total voice leading cost subject to zero Brigade hard rule violations.
"""

from typing import Any, Sequence, NamedTuple
from dataclasses import dataclass
from src.harmony.core.types import Voicing, Key, Chord, ValidationResult
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
    diagnostics: list[SolverStepDiagnostic]
    message: str = ""


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
    ) -> SolverResult:
        """
        Finds the globally optimal sequence of Voicings for the given melody and chord progression.
        """
        n = len(chords)
        if len(melody) != n or n == 0:
            return SolverResult(
                is_success=False,
                voicings=None,
                total_cost=float("inf"),
                diagnostics=[],
                message=f"Length mismatch: melody ({len(melody)}) vs chords ({n})",
            )

        # Parse melody and chords
        melody_pitches: list[int] = []
        downbeats: list[bool] = []
        for m in melody:
            if isinstance(m, dict):
                melody_pitches.append(int(m["pitch"]))
                downbeats.append(bool(m.get("is_downbeat", False)))
            else:
                melody_pitches.append(int(m))
                downbeats.append(False)

        parsed_chords: list[Chord] = []
        for c in chords:
            if isinstance(c, Chord):
                parsed_chords.append(c)
            else:
                parsed_chords.append(Chord(function=str(c)))

        # 1. Generate state lattice V[t]
        lattice: list[list[Voicing]] = []
        diagnostics: list[SolverStepDiagnostic] = []

        for t in range(n):
            candidates = generate_candidate_voicings(
                soprano_pitch=melody_pitches[t],
                chord=parsed_chords[t],
                key=key,
                allow_extended_ranges=allow_extended_ranges,
            )
            lattice.append(candidates)
            diagnostics.append(
                SolverStepDiagnostic(
                    step_index=t,
                    chord=parsed_chords[t].function,
                    soprano_pitch=melody_pitches[t],
                    candidates_count=len(candidates),
                    reachable_candidates_count=0,
                )
            )

            if len(candidates) == 0:
                return SolverResult(
                    is_success=False,
                    voicings=None,
                    total_cost=float("inf"),
                    diagnostics=diagnostics,
                    message=f"Step {t} ({parsed_chords[t].function}): no candidate voicings found for soprano pitch {melody_pitches[t]}",
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
                key=key,
                is_downbeat=downbeats[0],
            )
            if res.is_valid and not res.has_hard_violations:
                init_delta.append(res.cost)
            else:
                init_delta.append(float("inf"))

        delta.append(init_delta)
        psi.append([-1] * len(lattice[0]))
        diagnostics[0].reachable_candidates_count = sum(1 for c in init_delta if c < float("inf"))

        if diagnostics[0].reachable_candidates_count == 0:
            return SolverResult(
                is_success=False,
                voicings=None,
                total_cost=float("inf"),
                diagnostics=diagnostics,
                message="Initial step 0 has no valid voicings under rule engine constraints.",
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
                        key=key,
                        is_downbeat=is_downbeat,
                    )

                    if not res.is_valid or res.has_hard_violations:
                        continue

                    total_cost = delta[t - 1][i] + res.cost
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_prev_idx = i

                step_delta[j] = best_cost
                step_psi[j] = best_prev_idx

            delta.append(step_delta)
            psi.append(step_psi)
            reachable = sum(1 for c in step_delta if c < float("inf"))
            diagnostics[t].reachable_candidates_count = reachable

            if reachable == 0:
                return SolverResult(
                    is_success=False,
                    voicings=None,
                    total_cost=float("inf"),
                    diagnostics=diagnostics,
                    message=f"Step {t} ({curr_chord.function}): all {len(curr_candidates)} candidates blocked by hard-rule violations from step {t-1}.",
                )

        # 3. Backtrack optimal trajectory
        last_step_costs = delta[n - 1]
        best_last_idx = min(range(len(last_step_costs)), key=lambda idx: last_step_costs[idx])
        optimal_cost = last_step_costs[best_last_idx]

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
            diagnostics=diagnostics,
            message="Optimal SATB trajectory found successfully.",
        )
