from aegisswarm.splits import HYBRID_OBJECTIVE_DEV_SEEDS


def test_hybrid_objective_development_block_boundaries():
    assert HYBRID_OBJECTIVE_DEV_SEEDS[0] == 5000
    assert HYBRID_OBJECTIVE_DEV_SEEDS[-1] == 5399
