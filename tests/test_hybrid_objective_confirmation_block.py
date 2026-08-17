from aegisswarm.splits import HYBRID_OBJECTIVE_CONFIRM_SEEDS


def test_hybrid_objective_confirmation_block_boundaries():
    assert HYBRID_OBJECTIVE_CONFIRM_SEEDS[0] == 8000
    assert HYBRID_OBJECTIVE_CONFIRM_SEEDS[-1] == 8399
