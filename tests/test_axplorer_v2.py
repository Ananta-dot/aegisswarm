import numpy as np
import torch

from aegisswarm.axplorer_v2 import (
    FitnessConditionedRuleTransformer,
    canonicalize_program,
    quality_buckets,
    sample_v2_programs,
    score_weights,
)
from aegisswarm.rule_program import Action, Condition, MAX_RULES, RULE_WIDTH, TOKEN_LEVELS
from aegisswarm.splits import (
    FINAL_HOLDOUT_SEEDS,
    TRAIN_SEEDS,
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
    VALIDATION_SEEDS,
)


def _assert_canonical(program):
    rows = np.asarray(program).reshape(MAX_RULES, RULE_WIDTH)
    assert set(np.unique(rows[:, 0])).issubset({0, TOKEN_LEVELS - 1})
    assert np.all((0 <= rows[:, 1]) & (rows[:, 1] < len(Condition)))
    assert np.all((0 <= rows[:, 2]) & (rows[:, 2] < TOKEN_LEVELS))
    assert np.all((0 <= rows[:, 3]) & (rows[:, 3] < len(Action)))
    assert np.all((0 <= rows[:, 4]) & (rows[:, 4] < TOKEN_LEVELS))


def test_canonicalize_program_enforces_field_grammar():
    raw = np.arange(MAX_RULES * RULE_WIDTH, dtype=np.int16) % TOKEN_LEVELS
    canonical = canonicalize_program(raw)
    _assert_canonical(canonical)


def test_rank_condition_and_score_weights_favor_best_programs():
    fitness = np.asarray([100.0, 120.0, 140.0, 160.0, 180.0])
    buckets = quality_buckets(fitness)
    weights = score_weights(fitness, temperature=4.0)
    assert buckets[-1] == 3
    assert buckets[0] == 0
    assert weights[-1] > weights[-2] > weights[0]


def test_v2_sampler_emits_only_canonical_programs_on_cpu():
    torch.manual_seed(7)
    model = FitnessConditionedRuleTransformer(d_model=32, nhead=4, layers=1)
    programs = sample_v2_programs(
        model,
        n=3,
        temperature=1.0,
        quality_level=3,
        device="cpu",
        seed=7,
    )
    assert len(programs) == 3
    for program in programs:
        _assert_canonical(program)


def test_v2_development_and_confirmation_blocks_are_disjoint():
    train = set(TRAIN_SEEDS)
    validation = set(VALIDATION_SEEDS)
    v1_final = set(FINAL_HOLDOUT_SEEDS)
    dev = set(V2_DEV_SEEDS)
    confirm = set(V2_CONFIRM_SEEDS)

    assert len(dev) == 400
    assert len(confirm) == 400
    assert V2_DEV_SEEDS[0] == 3000 and V2_DEV_SEEDS[-1] == 3399
    assert V2_CONFIRM_SEEDS[0] == 6000 and V2_CONFIRM_SEEDS[-1] == 6399
    assert dev.isdisjoint(train | validation | v1_final | confirm)
    assert confirm.isdisjoint(train | validation | v1_final)
