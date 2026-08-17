import numpy as np

from aegisswarm.hybrid_stats import paired_run_sign_flip_pvalue


def test_paired_run_sign_flip_uses_training_runs_as_unit():
    first = np.zeros((5, 40), dtype=float)
    second = np.ones((5, 40), dtype=float)

    # With five independent paired training runs, an exact two-sided label-swap
    # test has only 2^5 assignments. Even a perfect all-run advantage therefore
    # has minimum attainable p = 2/32 = 0.0625.
    assert paired_run_sign_flip_pvalue(first, second) == 0.0625


def test_paired_run_sign_flip_returns_one_for_no_effect():
    matrix = np.arange(50, dtype=float).reshape(5, 10)
    assert paired_run_sign_flip_pvalue(matrix, matrix) == 1.0
