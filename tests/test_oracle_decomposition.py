import numpy as np

from aegisswarm.oracle_decomposition import decompose_oracle, oracle_tape_seed
from aegisswarm.splits import (
    EVIDENCE_DEV_SEEDS,
    ORACLE_DECOMP_DEV_SEEDS,
    ORACLE_DECOMP_REPLICATION_SEEDS,
    RELIABILITY_DEV_SEEDS,
    ROBUST_DEV_SEEDS,
    SELECTOR_CONFIRM_SEEDS,
    SELECTOR_DEV_SEEDS,
    SELECTOR_TRAIN_SEEDS,
    STOCHASTIC_ABLATION_DEV_SEEDS,
)


def _metrics_from_survival(survival):
    survival = np.asarray(survival, dtype=float)
    return {
        "asset_survival_rate": survival,
        "reward": 100.0 * survival,
    }


def test_stable_specialization_survives_cross_tape_holdout():
    # Program 0 is structurally best for worlds 0/1; program 1 for worlds 2/3.
    # The preference is identical on every stochastic tape.
    survival = np.zeros((2, 4, 4), dtype=float)
    survival[0, 0:2, :] = 1.0
    survival[1, 2:4, :] = 1.0

    result = decompose_oracle(_metrics_from_survival(survival))

    assert result["cross_tape_choice_agreement"] == 1.0
    assert result["cross_tape_oracle_survival"] == 1.0
    assert result["cross_tape_fixed_survival"] == 0.5
    assert result["cross_tape_oracle_minus_fixed"]["mean"] == 0.5


def test_tape_specific_luck_does_not_create_cross_tape_advantage():
    # First-half tapes favor program 0; second-half tapes favor program 1.
    # A same-tape oracle looks strong, but the preference reverses out of sample.
    survival = np.zeros((2, 3, 4), dtype=float)
    survival[0, :, 0:2] = 1.0
    survival[1, :, 2:4] = 1.0

    result = decompose_oracle(_metrics_from_survival(survival))

    assert result["cross_tape_choice_agreement"] == 0.0
    assert result["cross_tape_oracle_survival"] == 0.0
    assert result["cross_tape_oracle_minus_fixed"]["mean"] == 0.0


def test_oracle_tape_seed_is_stable_and_replication_specific():
    assert oracle_tape_seed(30001, 2) == oracle_tape_seed(30001, 2)
    assert oracle_tape_seed(30001, 2) != oracle_tape_seed(30001, 3)
    assert oracle_tape_seed(30001, 2) != oracle_tape_seed(30002, 2)


def test_oracle_decomposition_seed_blocks_are_fresh_and_disjoint():
    dev = set(ORACLE_DECOMP_DEV_SEEDS)
    replication = set(ORACLE_DECOMP_REPLICATION_SEEDS)
    assert dev.isdisjoint(replication)

    prior = set(EVIDENCE_DEV_SEEDS)
    prior.update(RELIABILITY_DEV_SEEDS)
    prior.update(ROBUST_DEV_SEEDS)
    prior.update(STOCHASTIC_ABLATION_DEV_SEEDS)
    prior.update(SELECTOR_TRAIN_SEEDS)
    prior.update(SELECTOR_DEV_SEEDS)
    prior.update(SELECTOR_CONFIRM_SEEDS)

    assert dev.isdisjoint(prior)
    assert replication.isdisjoint(prior)
