from aegisswarm.hybrid_objective_proof import QUICK_EVAL_SEEDS


def test_hybrid_objective_quick_uses_20_dev_scenarios():
    assert len(QUICK_EVAL_SEEDS) == 20
    assert QUICK_EVAL_SEEDS[0] == 5000
