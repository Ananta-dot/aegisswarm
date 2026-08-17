from aegisswarm.splits import HYBRID_OBJECTIVE_CONFIRM_SEEDS, HYBRID_OBJECTIVE_DEV_SEEDS


def test_hybrid_objective_seed_block_lengths():
    assert len(HYBRID_OBJECTIVE_DEV_SEEDS) == 400
    assert len(HYBRID_OBJECTIVE_CONFIRM_SEEDS) == 400
