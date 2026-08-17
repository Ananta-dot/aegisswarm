from __future__ import annotations

import itertools
import numpy as np


def paired_run_sign_flip_pvalue(first_matrix, second_matrix) -> float:
    """Exact two-sided paired randomization test at the training-run level.

    Scenarios are repeated measurements for each independently trained policy.
    The method comparison therefore first averages the paired scenario outcomes
    within each training run and then flips the method label for whole paired
    runs. For five runs there are only 2^5=32 assignments, so this is exact.
    """
    first = np.asarray(first_matrix, dtype=float)
    second = np.asarray(second_matrix, dtype=float)
    if first.shape != second.shape or first.ndim != 2 or first.shape[0] == 0:
        raise ValueError("paired matrices must have the same non-empty 2D shape")

    run_diff = (second - first).mean(axis=1)
    observed = abs(float(run_diff.mean()))
    if observed == 0.0:
        return 1.0

    n_runs = len(run_diff)
    if n_runs <= 20:
        values = []
        for signs in itertools.product((-1.0, 1.0), repeat=n_runs):
            values.append(abs(float(np.mean(np.asarray(signs) * run_diff))))
        values = np.asarray(values, dtype=float)
        return float(np.mean(values >= observed - 1e-15))

    # Defensive fallback for unusually many runs.
    rng = np.random.default_rng(97531)
    n_perm = 20000
    signs = rng.choice((-1.0, 1.0), size=(n_perm, n_runs))
    values = np.abs((signs * run_diff[None, :]).mean(axis=1))
    return float((np.sum(values >= observed - 1e-15) + 1) / (n_perm + 1))
