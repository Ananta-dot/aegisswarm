import numpy as np

from aegisswarm.final_proof import (
    hierarchical_bootstrap_ci,
    paired_hierarchical_bootstrap,
    paired_sign_flip_pvalue,
)
from aegisswarm.splits import (
    TRAIN_SEEDS,
    VALIDATION_SEEDS,
    TEST_SEEDS,
    FINAL_HOLDOUT_SEEDS,
)


def test_final_holdout_is_disjoint_and_frozen_size():
    final = set(FINAL_HOLDOUT_SEEDS)
    assert len(FINAL_HOLDOUT_SEEDS) == 400
    assert FINAL_HOLDOUT_SEEDS[0] == 2100
    assert FINAL_HOLDOUT_SEEDS[-1] == 2499
    assert final.isdisjoint(TRAIN_SEEDS)
    assert final.isdisjoint(VALIDATION_SEEDS)
    assert final.isdisjoint(TEST_SEEDS)


def test_hierarchical_bootstrap_constant_matrix():
    matrix = np.full((5, 20), 0.75)
    lo, hi = hierarchical_bootstrap_ci(matrix, n_boot=100)
    assert lo == 0.75
    assert hi == 0.75


def test_paired_statistics_detect_clear_improvement():
    local = np.zeros((5, 40), dtype=float)
    axplorer = np.ones((5, 40), dtype=float)

    stats = paired_hierarchical_bootstrap(
        local,
        axplorer,
        "asset_survival_rate",
        n_boot=200,
    )
    assert stats["axplorer_minus_local"] == 1.0
    assert stats["ci95"][0] > 0.0
    assert stats["probability_axplorer_better"] == 1.0
    assert stats["paired_training_run_win_rate"] == 1.0

    p = paired_sign_flip_pvalue(local, axplorer, n_perm=2000)
    assert p < 0.01
