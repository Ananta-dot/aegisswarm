import numpy as np

from aegisswarm.hybrid_objective import HybridBudgetedOracle
from aegisswarm.hybrid_objective_proof import QUICK_BUDGET
from aegisswarm.rule_program import MAX_RULES, RULE_WIDTH
from aegisswarm.scoring import EvalConfig
from aegisswarm.splits import (
    FINAL_HOLDOUT_SEEDS,
    HYBRID_CONFIRM_SEEDS,
    HYBRID_DEV_SEEDS,
    HYBRID_OBJECTIVE_CONFIRM_SEEDS,
    HYBRID_OBJECTIVE_DEV_SEEDS,
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def test_hybrid_objective_oracle_scores_through_optimizer():
    config = EvalConfig(seeds=(0,))
    program = np.zeros(MAX_RULES * RULE_WIDTH, dtype=np.int16)
    with HybridBudgetedOracle(config, budget=4, workers=1) as oracle:
        count = oracle.evaluate_many([program])
        assert count == 1
        ranked = oracle.rank()
        assert len(ranked) == 1
        metrics = ranked[0][2]
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


def test_hybrid_objective_oracle_deduplicates_candidates():
    config = EvalConfig(seeds=(0,))
    program = np.zeros(MAX_RULES * RULE_WIDTH, dtype=np.int16)
    with HybridBudgetedOracle(config, budget=QUICK_BUDGET, workers=1) as oracle:
        count = oracle.evaluate_many([program, program.copy(), program.copy()])
        assert count == 1
        assert oracle.evaluations == 1


def test_hybrid_objective_seed_blocks_are_fresh():
    dev = set(HYBRID_OBJECTIVE_DEV_SEEDS)
    confirm = set(HYBRID_OBJECTIVE_CONFIRM_SEEDS)
    previous = (
        set(FINAL_HOLDOUT_SEEDS)
        | set(V2_DEV_SEEDS)
        | set(V2_CONFIRM_SEEDS)
        | set(HYBRID_DEV_SEEDS)
        | set(HYBRID_CONFIRM_SEEDS)
    )
    assert len(HYBRID_OBJECTIVE_DEV_SEEDS) == 400
    assert HYBRID_OBJECTIVE_DEV_SEEDS[0] == 5000
    assert HYBRID_OBJECTIVE_DEV_SEEDS[-1] == 5399
    assert len(HYBRID_OBJECTIVE_CONFIRM_SEEDS) == 400
    assert HYBRID_OBJECTIVE_CONFIRM_SEEDS[0] == 8000
    assert HYBRID_OBJECTIVE_CONFIRM_SEEDS[-1] == 8399
    assert dev.isdisjoint(previous | confirm)
    assert confirm.isdisjoint(previous)
