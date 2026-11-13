"""
Tests verifying the removal of rigid soprano heuristic filters from plan generation.
Ensures previously discarded valid functional plans and SATB solutions are unlocked,
and verifies regressions across default, minor, and long melodic arch benchmarks.
"""

import importlib.util
from pathlib import Path
import pytest

from src.harmony.core.types import Key
from src.harmony.pipeline import Harmonizer
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.syntax.grammar import HarmonicGrammar


def _load_grammar_before():
    project_root = Path(__file__).resolve().parents[1]
    before_path = project_root / ".redteam" / "scratch" / "grammar_metrics" / "grammar_before.py"
    if not before_path.exists():
        pytest.skip("grammar_before.py baseline file is not present")
    spec = importlib.util.spec_from_file_location("grammar_before", str(before_path))
    if spec is None or spec.loader is None:
        pytest.skip("Failed to create spec for grammar_before.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.HarmonicGrammar


def test_same_triad_inversion_filter_removal_unlocks_plans_and_solutions():
    """
    Melody [60, 64, 62, 60] (C4 -> E4 -> D4 -> C4 in C Major).
    Old filter (same_triad_inversion) discarded T -> T6 and T6 -> T transitions
    when soprano moved between root (C) and third (E).
    After removal, more plans are generated and more solutions are solved.
    """
    GrammarBefore = _load_grammar_before()
    key = Key(tonic="C", mode="Major")
    melody = [60, 64, 62, 60]
    proc_mel = [
        {"pitch": p, "duration": 4, "is_downbeat": (i % 2 == 0)}
        for i, p in enumerate(melody)
    ]

    gb = GrammarBefore(key)
    ga = HarmonicGrammar(key)
    solver = ViterbiSolver()

    plans_before = gb.generate_plans(proc_mel, key=key, max_plans=60)
    plans_after = ga.generate_plans(proc_mel, key=key, max_plans=60)

    # 1. Total plans increased
    assert len(plans_after) > len(plans_before), (
        f"Expected plans_after ({len(plans_after)}) > plans_before ({len(plans_before)})"
    )

    # 2. Solved plans increased
    solved_before = sum(1 for p in plans_before if solver.solve(proc_mel, p, key).is_success)
    solved_after = sum(1 for p in plans_after if solver.solve(proc_mel, p, key).is_success)
    assert solved_after > solved_before, (
        f"Expected solved_after ({solved_after}) > solved_before ({solved_before})"
    )

    # 3. Unlocked specific transitions previously rejected
    plans_after_tuples = {tuple(c.function for c in p) for p in plans_after}
    plans_before_tuples = {tuple(c.function for c in p) for p in plans_before}
    new_plans = plans_after_tuples - plans_before_tuples

    # T -> T6 progressions unlocked
    assert any(p[0] in ("T", "t") and p[1] in ("T6", "t6") for p in new_plans), (
        f"Expected unlocked T->T6 plan in new plans, got: {new_plans}"
    )


def test_subdominant_to_dominant_leap_filter_removal_unlocks_plans_and_solutions():
    """
    Melody [65, 67, 60] (F4 -> G4 -> C4 in C Major).
    Old filter discarded S -> Dominant transitions when soprano leaped up 4th -> 5th degree.
    After replacing hard rejection with penalty, S -> D6/D65/D43 transitions are generated and solved.
    """
    GrammarBefore = _load_grammar_before()
    key = Key(tonic="C", mode="Major")
    melody = [65, 67, 60]
    proc_mel = [
        {"pitch": p, "duration": 4, "is_downbeat": (i % 2 == 0)}
        for i, p in enumerate(melody)
    ]

    gb = GrammarBefore(key)
    ga = HarmonicGrammar(key)
    solver = ViterbiSolver()

    plans_before = gb.generate_plans(proc_mel, key=key, max_plans=60)
    plans_after = ga.generate_plans(proc_mel, key=key, max_plans=60)

    # Plans and solved plans increased
    assert len(plans_after) > len(plans_before)
    solved_before = sum(1 for p in plans_before if solver.solve(proc_mel, p, key).is_success)
    solved_after = sum(1 for p in plans_after if solver.solve(proc_mel, p, key).is_success)
    assert solved_after > solved_before

    # Verify S -> D dominant group transitions unlocked
    plans_after_tuples = {tuple(c.function for c in p) for p in plans_after}
    plans_before_tuples = {tuple(c.function for c in p) for p in plans_before}
    new_plans = plans_after_tuples - plans_before_tuples
    assert any(p[0] in ("S", "s") and p[1] in ("D6", "D65", "D43") for p in new_plans)


def test_regression_default_melody():
    """Default melody [64, 65, 67, 64, 62, 60] harmonizes successfully and final chord is root T."""
    mel = [64, 65, 67, 64, 62, 60]
    h = Harmonizer()
    res = h.harmonize(mel, key="C Major")
    assert res.is_success is True, f"Failed: {res.message}"
    assert res.best_solution is not None
    final_fn = res.best_solution.chords[-1].function
    assert final_fn in ("T", "t")
    assert final_fn not in ("D7", "d7", "T6", "t6", "K64", "k64", "D6", "d6", "D65", "d65")


def test_regression_a_moll_desc():
    """a-moll desc melody [81, 80, 77, 76, 74, 72, 71, 69] harmonizes successfully and final chord is root T."""
    mel = [81, 80, 77, 76, 74, 72, 71, 69]
    h = Harmonizer()
    res = h.harmonize(mel, key="A Minor")
    assert res.is_success is True, f"Failed: {res.message}"
    assert res.best_solution is not None
    final_fn = res.best_solution.chords[-1].function
    assert final_fn in ("T", "t")
    assert final_fn not in ("D7", "d7", "T6", "t6", "K64", "k64", "D6", "d6", "D65", "d65")


def test_regression_32_note_arch():
    """32-note arch melody harmonizes successfully and final chord is root T."""
    mel = [
        60, 62, 64, 65, 67, 69, 71, 72, 74, 72, 71, 69, 67, 65, 64, 62,
        60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62, 60, 60,
    ]
    h = Harmonizer()
    res = h.harmonize(mel, key="C Major")
    assert res.is_success is True, f"Failed: {res.message}"
    assert res.best_solution is not None
    final_fn = res.best_solution.chords[-1].function
    assert final_fn in ("T", "t")
    assert final_fn not in ("D7", "d7", "T6", "t6", "K64", "k64", "D6", "d6", "D65", "d65")
