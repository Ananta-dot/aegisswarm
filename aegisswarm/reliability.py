from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linear_sum_assignment, milp
from scipy.sparse import lil_matrix

from .hybrid import RuleGuidedHungarianPolicy
from .models import ThreatType


def abstract_success_probability(defender, threat) -> float:
    """Mirror SimulatorV2's abstract interaction-success model.

    This is intentionally dimensionless and platform-independent. It is used by
    reliability-aware allocation only to rank feasible abstract assignments; the
    simulator remains the source of realized stochastic outcomes.
    """

    dist = threat.distance_to(defender.x, defender.y)
    if dist > defender.range:
        return 0.0

    distance_factor = max(0.10, 1.0 - dist / max(defender.range, 1e-9))
    type_factor = {
        ThreatType.DIRECT: 1.00,
        ThreatType.FAST: 0.82,
        ThreatType.DECOY: 1.08,
    }[threat.threat_type]
    return float(
        np.clip(
            0.20 + 0.55 * defender.capacity * distance_factor * type_factor,
            0.05,
            0.90,
        )
    )


class ReliabilityWeightedHungarianPolicy(RuleGuidedHungarianPolicy):
    """One-to-one assignment weighted by abstract success probability.

    This preserves incumbent one-step/Hungarian semantics. The only change is
    that each positive rule-derived pair utility is multiplied by the same
    abstract success probability used by SimulatorV2.
    """

    name = "reliability_weighted_hungarian"

    def __init__(self, tokens, name: str = "reliability_weighted_hungarian"):
        super().__init__(tokens, name=name)

    def assign(self, scenario, t):
        defenders = [
            d for d in scenario.defenders if d.available and d.remaining_uses > 0
        ]
        threats = [th for th in scenario.threats if th.active and th.detected]
        out = {d.id: None for d in scenario.defenders}

        if not defenders or not threats:
            return out

        n_d = len(defenders)
        n_t = len(threats)
        utility = np.zeros((n_d, n_t + n_d), dtype=float)
        utility[:, :n_t] = -1e9

        for i, defender in enumerate(defenders):
            for j, threat in enumerate(threats):
                strategic = self.pair_utility(scenario, defender, threat)
                if strategic is None or strategic <= 0.0:
                    continue
                p_success = abstract_success_probability(defender, threat)
                value = float(strategic) * p_success
                if value > 0.0:
                    utility[i, j] = value

        row_ind, col_ind = linear_sum_assignment(-utility)
        for i, j in zip(row_ind, col_ind):
            if j >= n_t or utility[i, j] <= 0.0:
                continue
            out[defenders[i].id] = threats[j].id
        return out


class ReliabilityAwareBackupPolicy(RuleGuidedHungarianPolicy):
    """Reliability-aware one-step allocation with at most one contingent backup.

    Candidate actions are either:

    - one defender assigned to one threat; or
    - an ordered pair of defenders assigned to the same threat, where the second
      defender is a contingent backup that is only consumed by SimulatorV2 if the
      first attempt does not already resolve the threat.

    The set-packing MILP chooses mutually compatible groups: each defender is used
    by at most one selected group and each threat receives at most one selected
    group. For an ordered pair (d1, d2), expected strategic score is

        u1*p1 + (1-p1)*u2*p2

    using the incumbent rule-derived utilities u and SimulatorV2's abstract
    success probabilities p. At most two defenders can be allocated to a threat.
    """

    name = "reliability_aware_backup"

    def __init__(
        self,
        tokens,
        *,
        max_attempts_per_threat: int = 2,
        time_limit_seconds: float = 0.05,
        name: str = "reliability_aware_backup",
    ):
        super().__init__(tokens, name=name)
        self.max_attempts_per_threat = int(np.clip(max_attempts_per_threat, 1, 2))
        self.time_limit_seconds = max(0.01, float(time_limit_seconds))
        self._fallback = ReliabilityWeightedHungarianPolicy(tokens)

    def _candidate_options(self, scenario):
        defenders = [
            d for d in scenario.defenders if d.available and d.remaining_uses > 0
        ]
        threats = [th for th in scenario.threats if th.active and th.detected]
        options = []

        for ti, threat in enumerate(threats):
            eligible = []
            for di, defender in enumerate(defenders):
                strategic = self.pair_utility(scenario, defender, threat)
                if strategic is None or strategic <= 0.0:
                    continue
                p_success = abstract_success_probability(defender, threat)
                if p_success <= 0.0:
                    continue
                eligible.append((di, float(strategic), float(p_success)))
                options.append(
                    {
                        "threat_index": ti,
                        "defender_indices": (di,),
                        "score": float(strategic) * float(p_success),
                        "success_probability": float(p_success),
                    }
                )

            if self.max_attempts_per_threat < 2:
                continue

            for a in range(len(eligible)):
                di1, u1, p1 = eligible[a]
                for b in range(a + 1, len(eligible)):
                    di2, u2, p2 = eligible[b]

                    score_12 = u1 * p1 + (1.0 - p1) * u2 * p2
                    score_21 = u2 * p2 + (1.0 - p2) * u1 * p1
                    if score_21 > score_12:
                        order = (di2, di1)
                        score = score_21
                    else:
                        order = (di1, di2)
                        score = score_12

                    combined_p = 1.0 - (1.0 - p1) * (1.0 - p2)
                    options.append(
                        {
                            "threat_index": ti,
                            "defender_indices": order,
                            "score": float(score),
                            "success_probability": float(combined_p),
                        }
                    )

        return defenders, threats, options

    def _solve_options(self, scenario):
        defenders, threats, options = self._candidate_options(scenario)
        if not defenders or not threats or not options:
            return defenders, threats, options, None

        n = len(options)
        rows = []
        upper = []

        for di, _ in enumerate(defenders):
            idx = [
                k
                for k, option in enumerate(options)
                if di in option["defender_indices"]
            ]
            if idx:
                rows.append(idx)
                upper.append(1.0)

        for ti, _ in enumerate(threats):
            idx = [
                k
                for k, option in enumerate(options)
                if option["threat_index"] == ti
            ]
            if idx:
                rows.append(idx)
                upper.append(1.0)

        A = lil_matrix((len(rows), n), dtype=float)
        for r, idx in enumerate(rows):
            A[r, idx] = 1.0

        constraint = LinearConstraint(
            A.tocsr(),
            lb=np.full(len(rows), -np.inf, dtype=float),
            ub=np.asarray(upper, dtype=float),
        )
        c = -np.asarray([option["score"] for option in options], dtype=float)

        try:
            result = milp(
                c=c,
                integrality=np.ones(n, dtype=int),
                bounds=Bounds(np.zeros(n), np.ones(n)),
                constraints=constraint,
                options={"time_limit": self.time_limit_seconds, "presolve": True},
            )
        except Exception:
            return defenders, threats, options, None

        if result.x is None:
            return defenders, threats, options, None
        return defenders, threats, options, np.asarray(result.x, dtype=float)

    def assign(self, scenario, t):
        defenders, threats, options, solution = self._solve_options(scenario)
        if solution is None:
            return self._fallback.assign(scenario, t)

        selected = [
            option
            for x, option in zip(solution, options)
            if x > 0.5 and option["score"] > 0.0
        ]

        # Dict insertion order defines SimulatorV2's abstract within-step
        # resolution order. For a selected backup pair, insert the intended
        # primary first and backup second. Different-threat groups are independent.
        out = {}
        selected.sort(key=lambda option: option["score"], reverse=True)
        for option in selected:
            threat = threats[option["threat_index"]]
            for di in option["defender_indices"]:
                defender = defenders[di]
                out[defender.id] = threat.id

        for defender in scenario.defenders:
            if defender.id not in out:
                out[defender.id] = None
        return out
