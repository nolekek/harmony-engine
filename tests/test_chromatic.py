"""
Unit tests for Chromatic Voice Leading and False Relation (Переченье) - Brigade Chapter 26/28.
"""

from src.harmony.rules.chromatic import (
    check_false_relation,
)
from src.harmony.core.types import Voicing, Key
from src.harmony.rules.engine import RuleEngine


def test_correct_chromatic_step_in_same_voice():
    # C major: T (C, E, G, C) -> Secondary dominant DD7 (D, F#, A, C)
    # Tenor has F3 (53) -> steps to F#3 (54) in the SAME voice!
    # Alto has C4 (60) -> C4 (60)
    # Soprano has E4 (64) -> D4 (62)
    # Bass has C3 (48) -> D3 (50)
    v1 = Voicing(soprano=64, alto=60, tenor=53, bass=48)
    v2 = Voicing(soprano=62, alto=60, tenor=54, bass=50)

    violations = check_false_relation(v1, v2, key=Key(tonic="C", mode="Major"))
    # Since Tenor made the F -> F# chromatic step itself, there is NO false relation!
    assert len(violations) == 0


def test_diatonic_semitone_is_not_false_relation():
    # In G major, B (71, pc 11) in Soprano and C (60, pc 0) in Tenor
    # B and C are diatonic scale degrees 3 and 4 in G major!
    # They differ by 1 semitone, but must NEVER trigger false relation!
    v1 = Voicing(soprano=71, alto=67, tenor=62, bass=50)
    v2 = Voicing(soprano=69, alto=66, tenor=60, bass=50)

    violations = check_false_relation(v1, v2, key=Key(tonic="G", mode="Major"))
    assert len(violations) == 0


def test_false_relation_perechenie_forbidden():
    # False relation (Переченье):
    # In C major: F# (pc 6) is chromatic!
    # In v1: Alto has F4 (65, pc 5). Tenor has C4 (60).
    # In v2: Tenor takes F#3 (54, pc 6), while Alto stays or leaps to E4 (64).
    # The F-natural was in Alto, but F# is taken in Tenor!
    v1 = Voicing(soprano=67, alto=65, tenor=60, bass=48)
    v2 = Voicing(soprano=67, alto=64, tenor=54, bass=50)

    violations = check_false_relation(v1, v2, key=Key(tonic="C", mode="Major"))
    assert len(violations) > 0
    assert any(v.rule_id == "FALSE_RELATION_PERECHENIE" and v.is_hard for v in violations)


def test_rule_engine_integration_blocks_false_relation():
    engine = RuleEngine()
    key = Key(tonic="C", mode="Major")
    # v1 has F4 in Alto, v2 introduces F# in Tenor -> False relation!
    v1 = Voicing(soprano=67, alto=65, tenor=60, bass=48)
    v2 = Voicing(soprano=67, alto=64, tenor=54, bass=50)

    res = engine.validate(prev_voicing=v1, curr_voicing=v2, key=key)
    assert not res.is_valid
    assert res.cost == float("inf")
    assert any(v.rule_id == "FALSE_RELATION_PERECHENIE" for v in res.violations)
