import numpy as np

from aegisswarm.rule_program import (
    PROGRAM_LENGTH,
    TOKEN_LEVELS,
    random_program,
    mutate_program,
    RuleProgramPolicy,
)
from aegisswarm.rule_search import evaluate_rule_program, hill_climb_rule_program
from aegisswarm.scoring import EvalConfig
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator import Simulator


def test_rule_program_shape_and_bounds():
    rng = np.random.default_rng(7)
    p = random_program(rng)
    assert p.shape == (PROGRAM_LENGTH,)
    assert np.all(p >= 0)
    assert np.all(p < TOKEN_LEVELS)

    q = mutate_program(p, rng, n_mutations=4)
    assert q.shape == p.shape
    assert np.all(q >= 0)
    assert np.all(q < TOKEN_LEVELS)


def test_rule_program_runs():
    rng = np.random.default_rng(2)
    p = random_program(rng)
    gen = ScenarioGenerator(max_steps=50)
    scenario = gen.generate(seed=11, n_threats=10, n_defenders=4)
    metrics = Simulator.evaluate_policy(scenario, RuleProgramPolicy(p))
    assert 0.0 <= metrics.asset_survival_rate <= 1.0
    assert 0.0 <= metrics.containment_rate <= 1.0


def test_rule_program_score_and_local_search_non_degrading():
    rng = np.random.default_rng(3)
    p = random_program(rng)
    cfg = EvalConfig(seeds=(0, 1), n_threats=10, n_defenders=4, max_steps=50)
    before = evaluate_rule_program(p, cfg)
    _, after = hill_climb_rule_program(p, cfg, trials=2, seed=99)
    assert after["fitness"] >= before["fitness"]
