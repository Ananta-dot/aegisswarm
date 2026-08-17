import numpy as np

from aegisswarm.hybrid import RuleGuidedHungarianPolicy
from aegisswarm.models import ThreatType
from aegisswarm.random_tape import IndexedRandomTape
from aegisswarm.rule_program import PROGRAM_LENGTH
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator_v2 import SimulatorV2
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
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def test_indexed_random_tape_is_order_independent():
    tape = IndexedRandomTape(1234)
    a1 = tape.uniform("detect", 7, 3)
    b1 = tape.normal("motion", 8, 2, "x")
    c1 = tape.uniform("interaction", 9, 1, 4)

    # Query the same events in a different order from a fresh stateless tape.
    tape2 = IndexedRandomTape(1234)
    c2 = tape2.uniform("interaction", 9, 1, 4)
    a2 = tape2.uniform("detect", 7, 3)
    b2 = tape2.normal("motion", 8, 2, "x")

    assert a1 == a2
    assert b1 == b2
    assert c1 == c2
    assert tape.uniform("detect", 7, 4) != a1


def test_simulator_v2_repeats_identical_policy_scenario_exactly():
    tokens = np.zeros(PROGRAM_LENGTH, dtype=np.int16)
    gen = ScenarioGenerator()

    scenario_a = gen.generate(seed=222)
    scenario_b = gen.generate(seed=222)
    metrics_a = SimulatorV2.evaluate_policy(
        scenario_a,
        RuleGuidedHungarianPolicy(tokens),
    ).as_dict()
    metrics_b = SimulatorV2.evaluate_policy(
        scenario_b,
        RuleGuidedHungarianPolicy(tokens),
    ).as_dict()

    assert metrics_a == metrics_b


def test_perfect_sensing_marks_all_active_threats_detected():
    scenario = ScenarioGenerator().generate(seed=333)
    sim = SimulatorV2(scenario, perfect_sensing=True)
    assert any(not th.detected for th in scenario.threats)

    sim.sense()

    assert all(th.detected for th in scenario.threats if th.active)
    assert all(th.first_detected_t == 0 for th in scenario.threats if th.active)


def test_deterministic_interaction_succeeds_for_valid_reachable_pair():
    scenario = ScenarioGenerator().generate(seed=444)
    defender = scenario.defenders[0]
    threat = scenario.threats[0]

    # Scenario threats normally enter from the world boundary. Put one synthetic
    # target inside the defender's abstract range so this unit test exercises a
    # valid interaction deterministically rather than depending on random geometry.
    threat.x = float(defender.x + min(1.0, 0.25 * defender.range))
    threat.y = float(defender.y)
    threat.vx = 0.0
    threat.vy = 0.0
    threat.detected = True
    threat.first_detected_t = 0

    was_real = threat.threat_type != ThreatType.DECOY
    sim = SimulatorV2(scenario, deterministic_interactions=True)
    before_uses = defender.remaining_uses
    sim.step({defender.id: threat.id})

    assert defender.remaining_uses == before_uses - 1
    assert not threat.active
    if was_real:
        assert threat.contained_t == 0
        assert sim.diagnostics()["real_interaction_failures"] == 0


def test_evidence_seed_blocks_are_fresh_and_reserved():
    dev = set(EVIDENCE_DEV_SEEDS)
    confirm = set(EVIDENCE_CONFIRM_SEEDS)
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
    )

    assert len(EVIDENCE_DEV_SEEDS) == 400
    assert EVIDENCE_DEV_SEEDS[0] == 17000
    assert EVIDENCE_DEV_SEEDS[-1] == 17399
    assert len(EVIDENCE_CONFIRM_SEEDS) == 400
    assert EVIDENCE_CONFIRM_SEEDS[0] == 18000
    assert EVIDENCE_CONFIRM_SEEDS[-1] == 18399
    assert dev.isdisjoint(previous | confirm)
    assert confirm.isdisjoint(previous)
