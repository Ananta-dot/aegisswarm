from __future__ import annotations

import numpy as np


def universal_program_worker(payload, config=None):
    """Dispatch both program-scoring worker signatures used by final_proof.

    `BudgetedRuleOracle` calls the worker as `(tokens, EvalConfig)`, while
    holdout/stress evaluation calls it as a single packed payload
    `(program, seeds, scenario_kwargs)`.  Older V1 code accidentally reused the
    same function name for those two signatures; this compatibility worker is
    deliberately valid for both process-pool call shapes.
    """
    if config is not None:
        from .rule_search import evaluate_rule_program

        return evaluate_rule_program(np.asarray(payload, dtype=np.int16), config)

    from .final_proof import _evaluate_program_on_seeds

    program, seeds, scenario_kwargs = payload
    return _evaluate_program_on_seeds(program, seeds, scenario_kwargs)


def install_final_proof_worker_compat():
    """Install the spawn-safe dual-signature worker into final_proof."""
    from . import final_proof

    final_proof._evaluate_program_worker = universal_program_worker
    return final_proof
