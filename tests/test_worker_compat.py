import numpy as np

from aegisswarm.final_proof import BudgetedRuleOracle
from aegisswarm.rule_program import random_program
from aegisswarm.scoring import EvalConfig
from aegisswarm.worker_compat import (
    install_final_proof_worker_compat,
    universal_program_worker,
)


def test_universal_worker_candidate_signature():
    cfg = EvalConfig(seeds=(0,), n_threats=8, n_defenders=4, max_steps=40)
    program = random_program(np.random.default_rng(7))
    result = universal_program_worker(program, cfg)
    assert "fitness" in result
    assert 0.0 <= result["asset_survival_rate"] <= 1.0


def test_budgeted_oracle_parallel_spawn_path():
    install_final_proof_worker_compat()
    cfg = EvalConfig(seeds=(0,), n_threats=8, n_defenders=4, max_steps=40)
    rng = np.random.default_rng(11)
    programs = [random_program(rng), random_program(rng)]

    with BudgetedRuleOracle(cfg, budget=2, workers=2) as oracle:
        added = oracle.evaluate_many(programs)
        assert added == 2
        assert oracle.evaluations == 2
        assert len(oracle.cache) == 2
