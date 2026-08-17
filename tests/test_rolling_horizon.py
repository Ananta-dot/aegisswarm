import numpy as np

from aegisswarm.rolling_horizon import RuleGuidedRollingHorizonPolicy
from aegisswarm.rule_program import PROGRAM_LENGTH
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.splits import (
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
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def test_rolling_horizon_assignment_is_one_to_one_and_reachable():
    rng = np.random.default_rng(123)
    tokens = rng.integers(0, 16, size=PROGRAM_LENGTH, dtype=np.int16)
    scenario = ScenarioGenerator().generate(seed=321)
    for threat in scenario.threats:
        threat.detected = True

    policy = RuleGuidedRollingHorizonPolicy(tokens, horizon=3, time_limit_seconds=1.0)
    assignments = policy.assign(scenario, 0)

    chosen = [tid for tid in assignments.values() if tid is not None]
    assert len(chosen) == len(set(chosen))

    defenders = {d.id: d for d in scenario.defenders}
    threats = {t.id: t for t in scenario.threats}
    for did, tid in assignments.items():
        if tid is None:
            continue
        assert defenders[did].remaining_uses > 0
        assert threats[tid].distance_to(defenders[did].x, defenders[did].y) <= defenders[did].range


def test_rolling_horizon_horizon_one_returns_valid_current_plan():
    tokens = np.full(PROGRAM_LENGTH, 15, dtype=np.int16)
    scenario = ScenarioGenerator().generate(seed=17)
    for threat in scenario.threats:
        threat.detected = True

    policy = RuleGuidedRollingHorizonPolicy(tokens, horizon=1, time_limit_seconds=1.0)
    assignments = policy.assign(scenario, 0)
    assert set(assignments) == {d.id for d in scenario.defenders}


def test_v2_does_not_inflate_future_value_for_currently_feasible_pair():
    # This directly guards the V1 receding-horizon procrastination mechanism.
    tokens = np.full(PROGRAM_LENGTH, 15, dtype=np.int16)
    scenario = ScenarioGenerator().generate(seed=91)
    for threat in scenario.threats:
        threat.detected = True

    policy = RuleGuidedRollingHorizonPolicy(
        tokens,
        horizon=4,
        discount=0.90,
        time_limit_seconds=1.0,
    )
    _, _, variables = policy._candidate_variables(scenario)

    grouped = {}
    for var in variables:
        key = (var["defender_index"], var["threat_index"])
        grouped.setdefault(key, []).append(var)

    checked = 0
    for vars_for_pair in grouped.values():
        by_h = {v["h"]: v for v in vars_for_pair}
        if 0 not in by_h:
            continue
        current = by_h[0]
        if not current["current_positive"]:
            continue
        for h, future in by_h.items():
            if h == 0:
                continue
            assert future["utility"] <= current["utility"] + 1e-12
            checked += 1

    assert checked > 0


def test_planning_v2_seed_blocks_are_fresh():
    dev = set(PLANNING_V2_DEV_SEEDS)
    confirm = set(PLANNING_V2_CONFIRM_SEEDS)
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
    )
    assert len(PLANNING_V2_DEV_SEEDS) == 400
    assert PLANNING_V2_DEV_SEEDS[0] == 15000
    assert PLANNING_V2_DEV_SEEDS[-1] == 15399
    assert len(PLANNING_V2_CONFIRM_SEEDS) == 400
    assert PLANNING_V2_CONFIRM_SEEDS[0] == 16000
    assert PLANNING_V2_CONFIRM_SEEDS[-1] == 16399
    assert dev.isdisjoint(previous | confirm)
    assert confirm.isdisjoint(previous)
