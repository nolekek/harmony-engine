"""
Tests for Neuro-Symbolic StylePriorModel and its integration into RuleEngine and Viterbi.
"""

import pytest
from pathlib import Path
from src.harmony.ml.model import StylePriorModel
from src.harmony.rules.engine import RuleEngine
from src.harmony.core.types import Voicing, Key, Chord
from src.harmony.solver.viterbi import ViterbiSolver


def test_style_prior_initial_priors():
    model = StylePriorModel(weight=1.5)
    assert model.total_transitions > 0

    # Common contrary stepwise motion: S up, B down, A/T stay
    # (1, 0, -1, -2) vs wild jumps (5, 6, 7, 8)
    cost_smooth = model.score_transition((64, 60, 55, 48), (65, 60, 53, 45))
    cost_wild = model.score_transition((64, 60, 55, 48), (71, 68, 65, 36))

    assert cost_smooth < cost_wild


def test_style_prior_training_from_dataset(tmp_path: Path):
    model = StylePriorModel()
    dataset_file = tmp_path / "train.jsonl"
    dataset_file.write_text(
        '{"id": "1", "satb": [{"soprano": 64, "alto": 60, "tenor": 55, "bass": 48}, {"soprano": 65, "alto": 60, "tenor": 53, "bass": 45}]}\n'
        '{"id": "2", "satb": [{"soprano": 60, "alto": 55, "tenor": 52, "bass": 48}, {"soprano": 62, "alto": 55, "tenor": 50, "bass": 43}]}\n',
        encoding="utf-8",
    )

    initial_count = model.total_transitions
    processed = model.train_on_dataset(dataset_file)
    assert processed == 2
    assert model.total_transitions == initial_count + 2


def test_style_prior_serialization(tmp_path: Path):
    model = StylePriorModel(weight=2.0)
    save_path = tmp_path / "weights.json"
    model.save_weights(save_path)
    assert save_path.exists()

    loaded = StylePriorModel.load_weights(save_path)
    assert loaded.weight == 2.0
    assert loaded.total_transitions == model.total_transitions


def test_rule_engine_integration_with_style_scorer():
    scorer = StylePriorModel(weight=2.0)
    engine_with_scorer = RuleEngine(style_scorer=scorer)
    engine_without_scorer = RuleEngine()

    v1 = Voicing(soprano=64, alto=60, tenor=55, bass=48)
    v2 = Voicing(soprano=65, alto=60, tenor=57, bass=41)
    k = Key(tonic="C", mode="Major")
    c1 = Chord(function="T")
    c2 = Chord(function="S")

    res_without = engine_without_scorer.validate(
        prev_voicing=v1,
        curr_voicing=v2,
        prev_chord=c1,
        curr_chord=c2,
        key=k,
    )
    res_with = engine_with_scorer.validate(
        prev_voicing=v1,
        curr_voicing=v2,
        prev_chord=c1,
        curr_chord=c2,
        key=k,
    )

    assert res_without.is_valid
    assert res_with.is_valid
    # The cost with style scorer includes the style prior score
    assert res_with.cost != res_without.cost
