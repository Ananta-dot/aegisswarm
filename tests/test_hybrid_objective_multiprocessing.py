import numpy as np

from aegisswarm.hybrid_objective import HybridBudgetedOracle
from aegisswarm.rule_program import MAX_RULES, RULE_WIDTH
from aegisswarm.scoring import EvalConfig


def test_hybrid_objective_oracle_spawn_workers():
    config = EvalConfig(seeds=(0,))
    p0 = np.zeros(MAX_RULES * RULE_WIDTH, dtype=np.int16)
    p1 = p0.copy()
    p1[0] = 15
    with HybridBudgetedOracle(config, budget=4, workers=2) as oracle:
        count = oracle.evaluate_many([p0, p1])
        assert count == 2
        assert oracle.evaluations == 2
        assert len(oracle.rank()) == 2
