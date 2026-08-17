import numpy as np

from aegisswarm.hybrid_ablation import SCENARIO_KWARGS
from aegisswarm.rule_program import PROGRAM_LENGTH
from aegisswarm.splits import (
    RELIABILITY_CONFIRM_SEEDS,
    ROBUST_CONFIRM_SEEDS,
    ROBUST_DEV_SEEDS,
    ROBUST_TRAIN_WORLD_SEEDS,
)
from aegisswarm.stochastic_robust import (
    RobustEvalSpec,
    evaluate_program_replicated,
    robust_tape_seed,
)


def _spec(worlds=(21000,), tapes=2, mode="incumbent"):
    return RobustEvalSpec(
        world_seeds=tuple(worlds),
        tape_replicates=int(tapes),
        executor_mode=mode,
        scenario_kwargs=tuple(sorted(dict(SCENARIO_KWARGS).items())),
    )


def test_robust_tape_seed_is_stable_and_replication_specific():
    assert robust_tape_seed(21000, 0) == robust_tape_seed(21000, 0)
    assert robust_tape_seed(21000, 0) != robust_tape_seed(21000, 1)
    assert robust_tape_seed(21000, 0) != robust_tape_seed(21001, 0)


def test_replicated_evaluator_uses_world_times_tape_rollouts_and_is_repeatable():
    tokens = np.zeros(PROGRAM_LENGTH, dtype=np.int16)
    spec = _spec(worlds=(21000,), tapes=2)

    first = evaluate_program_replicated(tokens, spec)
    second = evaluate_program_replicated(tokens, spec)

    assert first["rollouts"] == 2
    assert second["rollouts"] == 2
    assert first == second
    assert 0.0 <= first["asset_survival_rate"] <= 1.0
    assert 0.0 <= first["worst_quartile_survival_diagnostic"] <= 1.0


def test_backup_replicated_evaluator_uses_same_tape_bundle_shape():
    tokens = np.zeros(PROGRAM_LENGTH, dtype=np.int16)
    result = evaluate_program_replicated(tokens, _spec(worlds=(21000, 21001), tapes=2, mode="backup"))
    assert result["rollouts"] == 4
    assert np.isfinite(result["fitness"])


def test_robust_seed_blocks_are_fresh_and_disjoint():
    train = set(ROBUST_TRAIN_WORLD_SEEDS)
    dev = set(ROBUST_DEV_SEEDS)
    confirm = set(ROBUST_CONFIRM_SEEDS)

    assert len(ROBUST_TRAIN_WORLD_SEEDS) == 32
    assert ROBUST_TRAIN_WORLD_SEEDS[0] == 21000
    assert ROBUST_TRAIN_WORLD_SEEDS[-1] == 21031
    assert len(ROBUST_DEV_SEEDS) == 400
    assert ROBUST_DEV_SEEDS[0] == 22000
    assert ROBUST_DEV_SEEDS[-1] == 22399
    assert len(ROBUST_CONFIRM_SEEDS) == 400
    assert ROBUST_CONFIRM_SEEDS[0] == 23000
    assert ROBUST_CONFIRM_SEEDS[-1] == 23399

    assert train.isdisjoint(dev | confirm)
    assert dev.isdisjoint(confirm)
    assert min(train) > max(RELIABILITY_CONFIRM_SEEDS)
