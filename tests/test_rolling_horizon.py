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
    """Guard the V1 receding-horizon procrastination mechanism deterministically.

    Use a disabled-rule program so the positive structural base utility is the only
    strategic contribution, then construct one defender/threat pair that is
    reachable now and remains reachable throughout the short horizon. This avoids
    relying on a random scenario to happen to contain an admissible h=0 -> h>0
    pair and makes the regression test exercise the V2 cap directly.
    """
    tokens = np.zeros(PROGRAM_LENGTH, dtype=np.int16)
    scenario = ScenarioGenerator().generate(seed=91)

    defender = scenario.defenders[0]
    threat = scenario.threats[0]
    asset = next(a for a in scenario.assets if a.id == threat.target_asset_id)

    # Deterministic synthetic geometry: the pair is feasible now and for all four
    # projected steps, while the threat remains well outside the target radius.
    asset.x = 90.0
    asset.y = 90.0
    defender.x = 20.0
    defender.y = 20.0
    defender.range = 100.0
    defender.available = True
    defender.remaining_uses = max(int(defender.remaining_uses), 4)

    threat.x = 30.0
    threat.y = 30.0
    threat.vx = 1.0
    threat.vy = 1.0
    threat.active = True
    threat.detected = True

    # Keep the fixture focused on this pair so unrelated randomly generated
    # tracks cannot make the assertion vacuous or ambiguous.
    for other in scenario.threats[1:]:
        other.active = False

    policy = RuleGuidedRollingHorizonPolicy(
        tokens,
        horizon=4,
        discount=0.90,
        time_limit_seconds=1.0,
    )
    _, _, variables = policy._candidate_variables(scenario)

    pair_vars = [
        var
        for var in variables
        if var["defender_index"] == 0 and var["threat_index"] == 0
    ]
    by_h = {var["h"]: var for var in pair_vars}

    assert set(by_h) == {0, 1, 2, 3}
    assert by_h[0]["current_positive"] is True

    current_utility = by_h[0]["utility"]
    for h in (1, 2, 3):
        assert by_h[h]["current_positive"] is True
        assert by_h[h]["utility"] < current_utility


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
