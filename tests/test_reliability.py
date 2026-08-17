import numpy as np

from aegisswarm.models import Defender, ProtectedAsset, Scenario, Sensor, Threat, ThreatType
from aegisswarm.reliability import (
    ReliabilityAwareBackupPolicy,
    ReliabilityWeightedHungarianPolicy,
    abstract_success_probability,
)
from aegisswarm.rule_program import PROGRAM_LENGTH
from aegisswarm.scenarios import ScenarioGenerator
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
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def _disabled_program():
    return np.zeros(PROGRAM_LENGTH, dtype=np.int16)


def _single_threat_two_defender_scenario():
    asset = ProtectedAsset(id=0, x=50.0, y=50.0, value=1.5, radius=4.0)
    threat = Threat(
        id=0,
        x=25.0,
        y=50.0,
        vx=1.0,
        vy=0.0,
        threat_type=ThreatType.DIRECT,
        target_asset_id=0,
        active=True,
        detected=True,
    )
    defenders = [
        Defender(
            id=0,
            x=25.0,
            y=50.0,
            capacity=0.80,
            range=20.0,
            remaining_uses=3,
        ),
        Defender(
            id=1,
            x=26.0,
            y=50.0,
            capacity=0.78,
            range=20.0,
            remaining_uses=3,
        ),
    ]
    return Scenario(
        threats=[threat],
        defenders=defenders,
        assets=[asset],
        sensors=[Sensor(id=0, x=50.0, y=50.0, range=60.0, detection_probability=0.9)],
        seed=123,
    )


def test_abstract_success_probability_matches_v2_formula_shape():
    scenario = _single_threat_two_defender_scenario()
    defender = scenario.defenders[0]
    threat = scenario.threats[0]
    p = abstract_success_probability(defender, threat)
    expected = np.clip(0.20 + 0.55 * defender.capacity * 1.0 * 1.0, 0.05, 0.90)
    assert abs(p - float(expected)) < 1e-12

    threat.x = defender.x + defender.range + 1.0
    assert abstract_success_probability(defender, threat) == 0.0


def test_reliability_weighted_assignment_is_one_to_one_and_reachable():
    tokens = _disabled_program()
    scenario = ScenarioGenerator().generate(seed=771)
    for threat in scenario.threats:
        threat.detected = True

    policy = ReliabilityWeightedHungarianPolicy(tokens)
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


def test_backup_policy_can_allocate_exactly_one_contingent_backup():
    scenario = _single_threat_two_defender_scenario()
    policy = ReliabilityAwareBackupPolicy(
        _disabled_program(),
        max_attempts_per_threat=2,
        time_limit_seconds=1.0,
    )
    assignments = policy.assign(scenario, 0)

    chosen = [did for did, tid in assignments.items() if tid == 0]
    assert len(chosen) == 2
    assert len(set(chosen)) == 2

    for did in chosen:
        defender = next(d for d in scenario.defenders if d.id == did)
        assert scenario.threats[0].distance_to(defender.x, defender.y) <= defender.range


def test_backup_policy_never_uses_defender_twice_or_more_than_two_per_threat():
    tokens = _disabled_program()
    scenario = ScenarioGenerator().generate(seed=991)
    for threat in scenario.threats:
        threat.detected = True

    policy = ReliabilityAwareBackupPolicy(tokens, time_limit_seconds=1.0)
    assignments = policy.assign(scenario, 0)

    assert set(assignments) == {d.id for d in scenario.defenders}
    counts = {}
    for did, tid in assignments.items():
        if tid is None:
            continue
        counts[tid] = counts.get(tid, 0) + 1
        defender = next(d for d in scenario.defenders if d.id == did)
        threat = next(t for t in scenario.threats if t.id == tid)
        assert threat.distance_to(defender.x, defender.y) <= defender.range
    assert all(count <= 2 for count in counts.values())


def test_reliability_seed_blocks_are_fresh():
    dev = set(RELIABILITY_DEV_SEEDS)
    confirm = set(RELIABILITY_CONFIRM_SEEDS)
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
    )

    assert len(RELIABILITY_DEV_SEEDS) == 400
    assert RELIABILITY_DEV_SEEDS[0] == 19000
    assert RELIABILITY_DEV_SEEDS[-1] == 19399
    assert len(RELIABILITY_CONFIRM_SEEDS) == 400
    assert RELIABILITY_CONFIRM_SEEDS[0] == 20000
    assert RELIABILITY_CONFIRM_SEEDS[-1] == 20399
    assert dev.isdisjoint(previous | confirm)
    assert confirm.isdisjoint(previous)
