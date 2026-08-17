from aegisswarm.splits import (
    FINAL_HOLDOUT_SEEDS,
    HYBRID_CONFIRM_SEEDS,
    HYBRID_DEV_SEEDS,
    HYBRID_OBJECTIVE_CONFIRM_SEEDS,
    HYBRID_OBJECTIVE_DEV_SEEDS,
    V2_CONFIRM_SEEDS,
    V2_DEV_SEEDS,
)


def test_hybrid_objective_blocks_do_not_overlap_prior_evidence():
    prior = set(FINAL_HOLDOUT_SEEDS) | set(V2_DEV_SEEDS) | set(V2_CONFIRM_SEEDS) | set(HYBRID_DEV_SEEDS) | set(HYBRID_CONFIRM_SEEDS)
    assert set(HYBRID_OBJECTIVE_DEV_SEEDS).isdisjoint(prior)
    assert set(HYBRID_OBJECTIVE_CONFIRM_SEEDS).isdisjoint(prior | set(HYBRID_OBJECTIVE_DEV_SEEDS))
