import json

import numpy as np
import pytest

from aegisswarm.optimizer_native import (
    DEFAULT_NATIVE_OBJECTIVE,
    LOWER_BOUNDS,
    OBJECTIVE_DIM,
    PARAM_NAMES,
    UPPER_BOUNDS,
    NativeBudgetedOracle,
    OptimizerNativePolicy,
    canonicalize_objective,
    evaluate_native_objective,
)
from aegisswarm.optimizer_native_proof import (
    PROTOCOL_ID,
    run_native_objective_confirmation,
)
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.scoring import EvalConfig
from aegisswarm.splits import (
    FINAL_HOLDOUT_SEEDS,
    HYBRID_CONFIRM_SEEDS,
    HYBRID_DEV_SEEDS,
    HYBRID_OBJECTIVE_CONFIRM_SEEDS,
    HYBRID_OBJECTIVE_DEV_SEEDS,
    NATIVE_OBJECTIVE_CONFIRM_SEEDS,
    NATIVE_OBJECTIVE_DEV_SEEDS,
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def test_native_objective_is_bounded_and_fixed_width():
    raw = np.linspace(-100.0, 100.0, OBJECTIVE_DIM)
    vector = canonicalize_objective(raw)
    assert vector.shape == (OBJECTIVE_DIM,)
    assert len(PARAM_NAMES) == OBJECTIVE_DIM == 14
    assert np.all(vector >= LOWER_BOUNDS)
    assert np.all(vector <= UPPER_BOUNDS)
    assert PROTOCOL_ID.endswith("-v2")


def test_native_policy_assignment_is_one_to_one_and_reachable():
    scenario = ScenarioGenerator().generate(seed=321)
    for threat in scenario.threats:
        threat.detected = True

    policy = OptimizerNativePolicy(DEFAULT_NATIVE_OBJECTIVE)
    assignments = policy.assign(scenario, 0)
    chosen = [tid for tid in assignments.values() if tid is not None]
    assert len(chosen) == len(set(chosen))

    defenders = {d.id: d for d in scenario.defenders}
    threats = {t.id: t for t in scenario.threats}
    for did, tid in assignments.items():
        if tid is None:
            continue
        assert (
            threats[tid].distance_to(defenders[did].x, defenders[did].y)
            <= defenders[did].range
        )


def test_native_v2_neutral_modifiers_keep_positive_structural_base():
    scenario = ScenarioGenerator().generate(seed=777)
    defender = scenario.defenders[0]
    threat = scenario.threats[0]

    # Build one guaranteed reachable detected pair. All learned modifiers are
    # neutral; only the shared structural base utility should make the pair
    # attractive. This prevents regression to the V1 zero-centred no-op failure.
    for th in scenario.threats:
        th.detected = False
    threat.detected = True
    threat.x = float(defender.x)
    threat.y = float(defender.y)

    neutral = np.zeros(OBJECTIVE_DIM, dtype=float)
    neutral[9] = 0.30  # lower bound for release_urgency_threshold
    policy = OptimizerNativePolicy(neutral)
    assignments = policy.assign(scenario, 0)
    assert any(tid == threat.id for tid in assignments.values())


def test_native_evaluator_exposes_full_metric_schema():
    metrics = evaluate_native_objective(
        DEFAULT_NATIVE_OBJECTIVE,
        EvalConfig(seeds=(0, 1)),
    )
    for key in (
        "fitness",
        "loss",
        "asset_survival_rate",
        "containment_rate",
        "penetrations",
        "cumulative_damage",
        "defenders_consumed",
        "mean_response_delay",
    ):
        assert key in metrics


def test_native_oracle_deduplicates_canonical_vectors():
    with NativeBudgetedOracle(
        EvalConfig(seeds=(0,)),
        budget=4,
        workers=1,
    ) as oracle:
        count = oracle.evaluate_many(
            [
                DEFAULT_NATIVE_OBJECTIVE,
                DEFAULT_NATIVE_OBJECTIVE.copy(),
                DEFAULT_NATIVE_OBJECTIVE + 1e-6,
            ]
        )
        assert count == 1
        assert oracle.evaluations == 1


def test_native_seed_blocks_are_fresh():
    dev = set(NATIVE_OBJECTIVE_DEV_SEEDS)
    confirm = set(NATIVE_OBJECTIVE_CONFIRM_SEEDS)
    previous = (
        set(FINAL_HOLDOUT_SEEDS)
        | set(V2_DEV_SEEDS)
        | set(V2_CONFIRM_SEEDS)
        | set(HYBRID_DEV_SEEDS)
        | set(HYBRID_CONFIRM_SEEDS)
        | set(HYBRID_OBJECTIVE_DEV_SEEDS)
        | set(HYBRID_OBJECTIVE_CONFIRM_SEEDS)
    )
    assert len(dev) == 400
    assert NATIVE_OBJECTIVE_DEV_SEEDS[0] == 9000
    assert NATIVE_OBJECTIVE_DEV_SEEDS[-1] == 9399
    assert len(confirm) == 400
    assert NATIVE_OBJECTIVE_CONFIRM_SEEDS[0] == 10000
    assert NATIVE_OBJECTIVE_CONFIRM_SEEDS[-1] == 10399
    assert dev.isdisjoint(previous | confirm)
    assert confirm.isdisjoint(previous)


def test_native_confirmation_requires_explicit_freeze(tmp_path):
    source = tmp_path / "dev"
    source.mkdir()
    (source / "protocol.json").write_text(
        json.dumps({"architecture_frozen": False})
    )
    with pytest.raises(RuntimeError, match="not frozen"):
        run_native_objective_confirmation(
            source_dir=source,
            out_dir=tmp_path / "confirm",
            workers=1,
        )
