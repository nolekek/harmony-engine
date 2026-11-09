"""
Solver package: State space generator and Viterbi dynamic programming optimizer.
"""

from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.solver.viterbi import ViterbiSolver, SolverResult, SolverStepDiagnostic

__all__ = [
    "generate_candidate_voicings",
    "ViterbiSolver",
    "SolverResult",
    "SolverStepDiagnostic",
]
