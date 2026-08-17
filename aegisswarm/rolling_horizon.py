from __future__ import annotations

import copy

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .hybrid import RuleGuidedHungarianPolicy
from .policies import distance_to_target


class RuleGuidedRollingHorizonPolicy(RuleGuidedHungarianPolicy):
    """Short-horizon abstract planner using the existing rule-derived utility.

    This changes temporal allocation, not strategic representation. The same
    60-token rule program supplies pair utility. A small time-indexed binary
    optimization problem allocates defender uses over several predicted
    synthetic timesteps. Only the first-step decision is executed and the
    problem is solved again after the next observation.

    Prediction is deliberately simple and platform-independent: currently
    detected threats are projected linearly using their synthetic velocity.
    """

    name = "rule_guided_rolling_horizon"

    def __init__(
        self,
        tokens,
        horizon: int = 3,
        discount: float = 0.90,
        time_limit_seconds: float = 0.25,
        name: str = "rule_guided_rolling_horizon",
    ):
        super().__init__(tokens, name=name)
        self.horizon = max(1, int(horizon))
        self.discount = float(np.clip(discount, 0.0, 1.0))
        self.time_limit_seconds = max(0.01, float(time_limit_seconds))

    @staticmethod
    def _project_threat(threat, scenario, h: int):
        projected = copy.copy(threat)
        projected.x = float(threat.x + threat.vx * scenario.dt * h)
        projected.y = float(threat.y + threat.vy * scenario.dt * h)
        return projected

    def _candidate_variables(self, scenario):
        defenders = [
            d for d in scenario.defenders
            if d.available and d.remaining_uses > 0
        ]
        threats = [
            th for th in scenario.threats
            if th.active and th.detected
        ]

        variables = []
        for di, defender in enumerate(defenders):
            for ti, threat in enumerate(threats):
                asset = next(a for a in scenario.assets if a.id == threat.target_asset_id)
                for h in range(self.horizon):
                    projected = self._project_threat(threat, scenario, h)
                    # Do not schedule a future assignment after the simple
                    # projection says the threat has already reached its target.
                    if h > 0 and projected.distance_to(asset.x, asset.y) <= asset.radius:
                        continue
                    value = self.pair_utility(scenario, defender, projected)
                    if value is None or value <= 0.0:
                        continue
                    variables.append(
                        {
                            "defender_index": di,
                            "threat_index": ti,
                            "h": h,
                            "utility": float((self.discount ** h) * value),
                        }
                    )
        return defenders, threats, variables

    def _solve_plan(self, scenario):
        defenders, threats, variables = self._candidate_variables(scenario)
        if not defenders or not threats or not variables:
            return defenders, threats, variables, None

        n = len(variables)
        rows = []
        upper = []

        # One assignment per defender per planning step.
        for di, _ in enumerate(defenders):
            for h in range(self.horizon):
                idx = [
                    k for k, v in enumerate(variables)
                    if v["defender_index"] == di and v["h"] == h
                ]
                if idx:
                    rows.append(idx)
                    upper.append(1.0)

        # A threat receives at most one planned attempt over the deterministic
        # horizon. The plan is discarded after the first real simulator step.
        for ti, _ in enumerate(threats):
            idx = [
                k for k, v in enumerate(variables)
                if v["threat_index"] == ti
            ]
            if idx:
                rows.append(idx)
                upper.append(1.0)

        # Respect each defender's remaining abstract uses across the horizon.
        for di, defender in enumerate(defenders):
            idx = [
                k for k, v in enumerate(variables)
                if v["defender_index"] == di
            ]
            if idx:
                rows.append(idx)
                upper.append(float(min(defender.remaining_uses, self.horizon)))

        A = lil_matrix((len(rows), n), dtype=float)
        for r, idx in enumerate(rows):
            A[r, idx] = 1.0

        constraint = LinearConstraint(
            A.tocsr(),
            lb=np.full(len(rows), -np.inf, dtype=float),
            ub=np.asarray(upper, dtype=float),
        )
        c = -np.asarray([v["utility"] for v in variables], dtype=float)

        try:
            result = milp(
                c=c,
                integrality=np.ones(n, dtype=int),
                bounds=Bounds(np.zeros(n), np.ones(n)),
                constraints=constraint,
                options={"time_limit": self.time_limit_seconds, "presolve": True},
            )
        except Exception:
            return defenders, threats, variables, None

        if result.x is None:
            return defenders, threats, variables, None
        return defenders, threats, variables, np.asarray(result.x, dtype=float)

    def assign(self, scenario, t):
        out = {d.id: None for d in scenario.defenders}
        defenders, threats, variables, solution = self._solve_plan(scenario)

        if solution is None:
            # Fail closed to the existing one-step optimizer if the planning
            # solver cannot return a usable plan.
            return super().assign(scenario, t)

        for selected, var in zip(solution, variables):
            if selected <= 0.5 or var["h"] != 0:
                continue
            defender = defenders[var["defender_index"]]
            threat = threats[var["threat_index"]]
            out[defender.id] = threat.id

        return out
