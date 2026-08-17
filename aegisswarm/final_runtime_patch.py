from __future__ import annotations

"""Runtime fix for the final-proof candidate-scoring process pool.

`final_proof.py` contains two historical helpers named `_evaluate_program_worker`:
one scores search candidates and one evaluates completed policies. Python keeps the
later definition, so the candidate-scoring pool receives the wrong callable.

Keep the frozen protocol/search implementation unchanged and replace only the
`BudgetedRuleOracle.evaluate_many` dispatch with an unambiguous worker function.
"""

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

import numpy as np

from .rule_search import evaluate_rule_program


def _program_key(program) -> tuple[int, ...]:
    return tuple(int(x) for x in np.asarray(program, dtype=np.int16))


def _score_candidate_payload(payload):
    """Top-level, spawn-safe worker: (tokens, EvalConfig) -> metrics."""
    tokens, config = payload
    return evaluate_rule_program(np.asarray(tokens, dtype=np.int16), config)


def _budgeted_evaluate_many(self, programs) -> int:
    pending = []
    pending_keys = []
    seen_pending = set()

    for program in programs:
        key = _program_key(program)
        if key in self.cache or key in seen_pending:
            continue
        if len(pending) >= self.remaining:
            break
        seen_pending.add(key)
        pending_keys.append(key)
        pending.append(list(key))

    if not pending:
        return 0

    payloads = [(tokens, self.config) for tokens in pending]

    if self._executor is None:
        results = [_score_candidate_payload(payload) for payload in payloads]
    else:
        results = list(self._executor.map(_score_candidate_payload, payloads))

    for key, metrics in zip(pending_keys, results):
        self.cache[key] = metrics
    self.evaluations += len(results)
    return len(results)


def install_budgeted_oracle_patch():
    """Install the collision-free candidate evaluator used by final_cli."""
    from .final_proof import BudgetedRuleOracle

    BudgetedRuleOracle.evaluate_many = _budgeted_evaluate_many
