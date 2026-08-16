from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from .policies import Policy, type_priority, distance_to_target


class HungarianPolicy(Policy):
    """
    Per-step exact bipartite assignment baseline.

    This is an optimization baseline for immediate assignment utility, not a
    full-horizon operational optimizer.
    """
    name = "hungarian"

    def assign(self, scenario, t):
        defenders = [
            d for d in scenario.defenders
            if d.available and d.remaining_uses > 0
        ]
        threats = [
            th for th in scenario.threats
            if th.active and th.detected
        ]
        out = {d.id: None for d in scenario.defenders}

        if not defenders or not threats:
            return out

        utility = np.full((len(defenders), len(threats)), -1e6, dtype=float)

        for i, d in enumerate(defenders):
            for j, th in enumerate(threats):
                dist = th.distance_to(d.x, d.y)
                if dist > d.range:
                    continue
                urgency = 1.0 / max(distance_to_target(scenario, th), 1.0)
                utility[i, j] = (
                    6.0 * type_priority(th) * urgency
                    + 2.0 / max(dist, 1.0)
                    - 0.20 / max(d.remaining_uses, 1)
                )

        row_ind, col_ind = linear_sum_assignment(-utility)

        for i, j in zip(row_ind, col_ind):
            if utility[i, j] <= -1e5:
                continue
            out[defenders[i].id] = threats[j].id

        return out
