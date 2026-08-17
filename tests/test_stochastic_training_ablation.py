import numpy as np

from aegisswarm.hybrid_ablation import SCENARIO_KWARGS
from aegisswarm.stochastic_robust import RobustEvalSpec, robust_tape_seed
from aegisswarm.stochastic_training_ablation import QUICK_REPEATED_TAPES
from aegisswarm.splits import (
    EVIDENCE_CONFIRM_SEEDS,
    EVIDENCE_DEV_SEEDS,
    FINAL_HOLDOUT_SEEDS,
    HYBRID_CONFIRM_SEEDS,
    HYBRID_DEV_SEEDS,
    HYBRID_OBJECTIVE_CONFIRM_SEEDS,
    HYBRID_OBJECTIVE_DEV_SEEDS,
    NATIVE_OBJECTIVE_CONFIRM_SEEDS,
    NATIVE_OBJECTIVE_DEV_SEEDS,
    NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS,
    NATIVE_OBJECTIVE_V2_DEV_SEEDS,
    PLANNING_CONFIRM_SEEDS,
    PLANNING_DEV_SEEDS,
    PLANNING_V2_CONFIRM_SEEDS,
    PLANNING_V2_DEV_SEEDS,
    RELIABILITY_CONFIRM_SEEDS,
    RELIABILITY_DEV_SEEDS,
    ROBUST_CONFIRM_SEEDS,
    ROBUST_DEV_SEEDS,
    ROBUST_TRAIN_WORLD_SEEDS,
    STOCHASTIC_ABLATION_CONFIRM_SEEDS,
    STOCHASTIC_ABLATION_DEV_SEEDS,
    STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS,
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def test_repeated_tape_bundle_strictly_contains_single_tape_bundle():
    world = 24000
    single = [robust_tape_seed(world, 0)]
    repeated = [robust_tape_seed(world, i) for i in range(QUICK_REPEATED_TAPES)]
    assert repeated[0] == single[0]
    assert len(set(repeated)) == QUICK_REPEATED_TAPES
    assert set(single).issubset(set(repeated))


def test_primary_specs_differ_only_in_tape_replication_count():
    kwargs = tuple(sorted(dict(SCENARIO_KWARGS).items()))
    worlds = tuple(STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS[:4])
    single = RobustEvalSpec(worlds, 1, "incumbent", kwargs)
    repeated = RobustEvalSpec(worlds, 2, "incumbent", kwargs)

    assert single.world_seeds == repeated.world_seeds
    assert single.executor_mode == repeated.executor_mode == "incumbent"
    assert single.scenario_kwargs == repeated.scenario_kwargs
    assert single.tape_replicates == 1
    assert repeated.tape_replicates == 2


def test_stochastic_ablation_blocks_are_fresh():
    train = set(STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS)
    dev = set(STOCHASTIC_ABLATION_DEV_SEEDS)
    confirm = set(STOCHASTIC_ABLATION_CONFIRM_SEEDS)

    previous = (
        set(FINAL_HOLDOUT_SEEDS)
        | set(V2_DEV_SEEDS)
        | set(V2_CONFIRM_SEEDS)
        | set(HYBRID_DEV_SEEDS)
        | set(HYBRID_CONFIRM_SEEDS)
        | set(HYBRID_OBJECTIVE_DEV_SEEDS)
        | set(HYBRID_OBJECTIVE_CONFIRM_SEEDS)
        | set(NATIVE_OBJECTIVE_DEV_SEEDS)
        | set(NATIVE_OBJECTIVE_CONFIRM_SEEDS)
        | set(NATIVE_OBJECTIVE_V2_DEV_SEEDS)
        | set(NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS)
        | set(PLANNING_DEV_SEEDS)
        | set(PLANNING_CONFIRM_SEEDS)
        | set(PLANNING_V2_DEV_SEEDS)
        | set(PLANNING_V2_CONFIRM_SEEDS)
        | set(EVIDENCE_DEV_SEEDS)
        | set(EVIDENCE_CONFIRM_SEEDS)
        | set(RELIABILITY_DEV_SEEDS)
        | set(RELIABILITY_CONFIRM_SEEDS)
        | set(ROBUST_TRAIN_WORLD_SEEDS)
        | set(ROBUST_DEV_SEEDS)
        | set(ROBUST_CONFIRM_SEEDS)
    )

    assert len(STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS) == 32
    assert STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS[0] == 24000
    assert STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS[-1] == 24031
    assert len(STOCHASTIC_ABLATION_DEV_SEEDS) == 400
    assert STOCHASTIC_ABLATION_DEV_SEEDS[0] == 25000
    assert STOCHASTIC_ABLATION_DEV_SEEDS[-1] == 25399
    assert len(STOCHASTIC_ABLATION_CONFIRM_SEEDS) == 400
    assert STOCHASTIC_ABLATION_CONFIRM_SEEDS[0] == 26000
    assert STOCHASTIC_ABLATION_CONFIRM_SEEDS[-1] == 26399

    assert train.isdisjoint(previous | dev | confirm)
    assert dev.isdisjoint(previous | confirm)
    assert confirm.isdisjoint(previous)
