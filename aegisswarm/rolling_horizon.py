from __future__ import annotations

import copy

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .hybrid import RuleGuidedHungarianPolicy


class RuleGuidedRollingHorizonPolicy(RuleGuidedHungarianPolicy):
    """Short-horizon abstract planner using the incumbent rule-derived utility.

    Planner V2 fixes an action-deferral pathology found in the V1 development
    screen. V1 re-evaluated strategic utility on projected future states, so an
    already-reachable threat could become more valuable at h>0 simply because it
    was projected to be closer/more urgent. In receding-horizon control this can
    repeatedly postpone an action.

    V2 still uses projection to decide future reachability and whether a threat is
    expected to have reached its synthetic target. But whenever a defender/threat
    pair is already strategically valid and reachable now, future utility for that
    same pair is capped at its current utility before temporal discounting. Thus
    an identical feasible assignment cannot become more attractive merely by
    waiting. The 60-token strategic representation itself is unchanged.

    Only the first-step decision is executed; the plan is recomputed after the
    next observation.
    """

    name = "rule_guided_rolling_horizon_v2"

    def __init__(
        self,
        tokens,
        horizon: int = 4,
        discount: float = 0.90,
        time_limit_seconds: float = 0.25,
        name: str = "rule_guided_rolling_horizon_v2",
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

                # Current utility is the anchor that prevents receding-horizon
                # procrastination when the pair is already feasible now.
                current_value = self.pair_utility(scenario, defender, threat)
                current_positive = (
                    current_value is not None and float(current_value) > 0.0
                )

                for h in range(self.horizon):
                    projected = self._project_threat(threat, scenario, h)
                    if h > 0 and projected.distance_to(asset.x, asset.y) <= asset.radius:
                        continue

                    projected_value = self.pair_utility(scenario, defender, projected)
                    if projected_value is None or projected_value <= 0.0:
                        continue

                    strategic_value = float(projected_value)
                    if h > 0 and current_positive:
                        # Future state can reduce the value of a currently
                        # feasible pair, but cannot inflate it simply because we
                        # waited. Discount then strictly weakens later execution.
                        strategic_value = min(
                            strategic_value,
                            float(current_value),
                        )

                    utility = float((self.discount ** h) * strategic_value)
                    if utility <= 0.0:
                        continue

                    variables.append(
                        {
                            "defender_index": di,
                            "threat_index": ti,
                            "h": h,
                            "utility": utility,
                            "current_positive": bool(current_positive),
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

        # Deterministic planning approximation: one planned attempt per threat
        # over the horizon. The real simulator remains stochastic and the plan is
        # discarded/re-solved after the first actual step.
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
            # Fall back to the incumbent one-step optimizer if the planning
            # solver cannot return a usable plan.
            return super().assign(scenario, t)

        for selected, var in zip(solution, variables):
            if selected <= 0.5 or var["h"] != 0:
                continue
            defender = defenders[var["defender_index"]]
            threat = threats[var["threat_index"]]
            out[defender.id] = threat.id

        return out
