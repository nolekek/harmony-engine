"""
Tests for T8: K64 Cadential Six-Four rules according to Brigade canon.
"""

from src.harmony.core.types import Chord, Key, Voicing
from src.harmony.rules.doubling import check_k64_doubling
from src.harmony.rules.engine import RuleEngine
from src.harmony.pipeline import Harmonizer


def test_k64_bass_not_scale_degree_five_rejected():
    """(г) K64 with bass that is not scale degree V is a hard violation."""
    key = Key("C", "Major")
    # In C-dur, scale degree V is G (PC 7).
    # Here bass is C3(48, PC 0, doubled with C4=60), not G:
    v_bad_bass = Voicing(soprano=67, alto=64, tenor=60, bass=48)
    violations = check_k64_doubling(v_bad_bass, Chord("K64"), key=key)
    assert any(viol.rule_id == "DOUBLING_K64_BASS_ONLY" for viol in violations)

    # With proper scale degree V in bass (G2=43) and doubled G:
    # S=E4(64), A=C4(60), T=G3(55), B=G2(43) -> tones: C, E, G, G (bass G doubled)
    v_proper = Voicing(soprano=64, alto=60, tenor=55, bass=43)
    assert len(check_k64_doubling(v_proper, Chord("K64"), key=key)) == 0


def test_k64_initial_chord_prohibited():
    """(а) K64 as the initial/first chord of a progression is strictly forbidden."""
    from src.harmony.solver.viterbi import ViterbiSolver
    engine = RuleEngine()
    key = Key("C", "Major")
    v_proper = Voicing(soprano=64, alto=60, tenor=55, bass=43)

    # First chord (prev_chord is None), even on downbeat:
    res = engine.validate(None, v_proper, prev_chord=None, curr_chord=Chord("K64"), key=key, is_downbeat=True)
    assert not res.is_valid
    assert any("K64" in v.rule_id for v in res.hard_violations)

    # Viterbi solver rejects any plan starting with K64:
    solver = ViterbiSolver()
    res_solver = solver.solve(
        melody=[72, 67, 64, 60],
        chords=["K64", "D", "T", "T"],
        key=key,
    )
    assert not res_solver.is_success
    assert "no valid voicings" in res_solver.message or "K64" in res_solver.message


def test_k64_weak_beat_prohibited():
    """(в) K64 on a weak beat is a hard violation."""
    engine = RuleEngine()
    key = Key("C", "Major")
    v_s = Voicing(soprano=65, alto=60, tenor=53, bass=41)  # S
    v_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)  # K64

    res = engine.validate(v_s, v_k64, prev_chord=Chord("S"), curr_chord=Chord("K64"), key=key, is_downbeat=False)
    assert not res.is_valid
    assert any(v.rule_id == "CADENCE_K64_STRONG_BEAT" for v in res.hard_violations)


def test_k64_on_downbeat_before_d_allowed():
    """(б) K64 on downbeat after S and resolving to D is completely valid."""
    engine = RuleEngine()
    key = Key("C", "Major")
    v_s = Voicing(soprano=65, alto=60, tenor=57, bass=41)  # S in F4, C4, A3, F2
    v_k64 = Voicing(soprano=64, alto=60, tenor=55, bass=43)  # K64 in E4, C4, G3, G2
    v_d = Voicing(soprano=62, alto=59, tenor=55, bass=43)  # D in D4, B3, G3, G2

    # S -> K64 on downbeat
    res1 = engine.validate(v_s, v_k64, prev_chord=Chord("S"), curr_chord=Chord("K64"), key=key, is_downbeat=True)
    assert res1.is_valid, f"S -> K64 must be valid, got: {[v.rule_id for v in res1.hard_violations]}"

    # K64 -> D
    res2 = engine.validate(v_k64, v_d, prev_chord=Chord("K64"), curr_chord=Chord("D"), key=key, is_downbeat=False)
    assert res2.is_valid, f"K64 -> D must be valid, got: {[v.rule_id for v in res2.hard_violations]}"


def test_melody_c5_g4_e4_c4_never_starts_with_k64():
    """(д) Melody C5 G4 E4 C4 (72, 67, 64, 60) must never produce K64 as its initial chord."""
    harmonizer = Harmonizer()
    res = harmonizer.harmonize([72, 67, 64, 60], key="C")
    assert res.is_success
    for sol in res.solutions:
        assert sol.chords[0].function != "K64", f"Solution started with K64: {[c.function for c in sol.chords]}"
