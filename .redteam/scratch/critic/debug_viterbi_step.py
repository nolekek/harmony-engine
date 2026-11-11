# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.harmony.core.types import Key
from src.harmony.syntax.grammar import HarmonicGrammar
from src.harmony.solver.viterbi import ViterbiSolver
from src.harmony.solver.state_generator import generate_candidate_voicings
from src.harmony.rules.engine import RuleEngine

key = Key("C", "Major")
grammar = HarmonicGrammar(key=key)
pitches = [65, 61, 59, 60] # F4, Db4, B3, C4
melody_objs = [{"pitch": p, "duration": "quarter", "is_downbeat": (i % 2 == 0)} for i, p in enumerate(pitches)]
plans = grammar.generate_plans(melody_objs, key=key)

engine = RuleEngine()
solver = ViterbiSolver(rule_engine=engine)

for plan in plans:
    plan_str = " -> ".join(c.function for c in plan)
    print(f"\n--- Testing plan: {plan_str} ---")
    for step_idx, (m_item, chord) in enumerate(zip(melody_objs, plan)):
        states = generate_candidate_voicings(m_item["pitch"], chord, key=key)
        print(f"  Step {step_idx} ({chord.function}, soprano={m_item['pitch']}): {len(states)} candidate voicings")
    sol = solver.solve(melody=melody_objs, chords=plan, key=key)
    if not sol.is_success:
        print(f"  Viterbi FAILED: {sol.message}")
        for diag in sol.diagnostics:
            print("   Diag:", diag)
    else:
        print(f"  Viterbi SUCCESS! cost={sol.total_cost}")
