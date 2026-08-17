import numpy as np

from aegisswarm.hybrid import RuleGuidedHungarianPolicy
from aegisswarm.hybrid_ablation import (
    evaluate_greedy_program_runs,
    evaluate_hybrid_program_runs,
)
from aegisswarm.hybrid_search import evaluate_hybrid_program
from aegisswarm.rule_program import MAX_RULES, RULE_WIDTH, TOKEN_LEVELS
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.scoring import EvalConfig
from aegisswarm.splits import (
    FINAL_HOLDOUT_SEEDS,
    HYBRID_CONFIRM_SEEDS,
    HYBRID_DEV_SEEDS,
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def _all_subtract_program():
    # enabled | ALWAYS | threshold | SUB_PRIORITY | max magnitude
    row = np.asarray([TOKEN_LEVELS - 1, 0, 0, 1, TOKEN_LEVELS - 1], dtype=np.int16)
    return np.tile(row, MAX_RULES)


def test_hybrid_optimizer_can_abstain_from_negative_assignments():
    scenario = ScenarioGenerator().generate(seed=123)
    for threat in scenario.threats:
        threat.detected = True

    policy = RuleGuidedHungarianPolicy(_all_subtract_program())
    assignments = policy.assign(scenario, 0)
    assert all(target is None for target in assignments.values())


def test_hybrid_assignments_are_one_to_one_and_reachable():
    scenario = ScenarioGenerator().generate(seed=321)
    for threat in scenario.threats:
        threat.detected = True

    neutral = np.zeros(MAX_RULES * RULE_WIDTH, dtype=np.int16)
    policy = RuleGuidedHungarianPolicy(neutral)
    assignments = policy.assign(scenario, 0)

    chosen = [target for target in assignments.values() if target is not None]
    assert len(chosen) == len(set(chosen))

    defenders = {d.id: d for d in scenario.defenders}
    threats = {t.id: t for t in scenario.threats}
    for did, tid in assignments.items():
        if tid is None:
            continue
        defender = defenders[did]
        threat = threats[tid]
        assert threat.distance_to(defender.x, defender.y) <= defender.range


def test_hybrid_evaluator_exposes_same_fitness_metrics():
    program = np.zeros(MAX_RULES * RULE_WIDTH, dtype=np.int16)
    metrics = evaluate_hybrid_program(program, EvalConfig(seeds=(0, 1)))
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


def test_hybrid_and_greedy_parallel_evaluators_spawn_cleanly():
    neutral = np.zeros(MAX_RULES * RULE_WIDTH, dtype=np.int16)
    subtract = _all_subtract_program()
    programs = [neutral, subtract]

    greedy = evaluate_greedy_program_runs(programs, seeds=(0,), workers=2)
    hybrid = evaluate_hybrid_program_runs(programs, seeds=(0,), workers=2)

    assert greedy["matrices"]["asset_survival_rate"].shape == (2, 1)
    assert hybrid["matrices"]["asset_survival_rate"].shape == (2, 1)


def test_hybrid_seed_blocks_are_separate_from_previous_evidence():
    hybrid_dev = set(HYBRID_DEV_SEEDS)
    hybrid_confirm = set(HYBRID_CONFIRM_SEEDS)
    previous = set(FINAL_HOLDOUT_SEEDS) | set(V2_DEV_SEEDS) | set(V2_CONFIRM_SEEDS)

    assert len(HYBRID_DEV_SEEDS) == 400
    assert HYBRID_DEV_SEEDS[0] == 4000 and HYBRID_DEV_SEEDS[-1] == 4399
    assert len(HYBRID_CONFIRM_SEEDS) == 400
    assert HYBRID_CONFIRM_SEEDS[0] == 7000 and HYBRID_CONFIRM_SEEDS[-1] == 7399
    assert hybrid_dev.isdisjoint(previous | hybrid_confirm)
    assert hybrid_confirm.isdisjoint(previous)
