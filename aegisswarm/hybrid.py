from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from .models import ThreatType
from .rule_program import Action, RuleProgramPolicy
from .policies import distance_to_target


class RuleGuidedHungarianPolicy(RuleProgramPolicy):
    """Hybrid policy: strategic rule program + exact per-step assignment.

    The rule program shapes pairwise utility and reserve intent. A Hungarian
    assignment layer then chooses the globally best one-to-one matching among
    reachable defender/threat pairs, with explicit zero-utility no-op columns so
    the optimizer is never forced to make a strategically bad assignment.
    """

    name = "rule_guided_hungarian"

    def __init__(self, tokens, name="rule_guided_hungarian"):
        super().__init__(tokens, name=name)

    def pair_utility(self, scenario, defender, threat):
        d_def = threat.distance_to(defender.x, defender.y)
        if d_def > defender.range:
            return None

        d_asset = distance_to_target(scenario, threat)
        score = (
            2.0 * self._type_prior(threat)
            + 1.5 / max(d_asset, 1.0)
            + 1.0 / max(d_def, 1.0)
        )
        reserve = 0

        for rule in self.rules:
            if not rule.enabled:
                continue
            if not self._condition_matches(
                rule,
                scenario,
                defender,
                threat,
                d_asset,
                d_def,
            ):
                continue

            if rule.action == Action.ADD_PRIORITY:
                score += rule.magnitude
            elif rule.action == Action.SUB_PRIORITY:
                score -= rule.magnitude
            elif rule.action == Action.RESERVE:
                reserve = max(reserve, int(round(rule.magnitude)))
            elif rule.action == Action.RELEASE_RESERVE:
                reserve = 0
            elif (
                rule.action == Action.BOOST_STICKINESS
                and defender.assigned_threat_id == threat.id
            ):
                score += rule.magnitude
            elif (
                rule.action == Action.PENALIZE_DECOY
                and threat.threat_type == ThreatType.DECOY
            ):
                score -= rule.magnitude

        if defender.remaining_uses <= reserve and d_asset > 10.0:
            return None
        return float(score)

    def assign(self, scenario, t):
        defenders = [
            d
            for d in scenario.defenders
            if d.available and d.remaining_uses > 0
        ]
        threats = [
            th
            for th in scenario.threats
            if th.active and th.detected
        ]
        out = {d.id: None for d in scenario.defenders}

        if not defenders or not threats:
            return out

        # Real threat columns followed by one independent no-op column per
        # defender. Zero utility for no-op means negative strategic assignments
        # are rejected automatically.
        n_d = len(defenders)
        n_t = len(threats)
        utility = np.zeros((n_d, n_t + n_d), dtype=float)
        utility[:, :n_t] = -1e9

        for i, defender in enumerate(defenders):
            for j, threat in enumerate(threats):
                value = self.pair_utility(scenario, defender, threat)
                if value is not None:
                    utility[i, j] = value

        row_ind, col_ind = linear_sum_assignment(-utility)

        for i, j in zip(row_ind, col_ind):
            if j >= n_t:
                continue
            if utility[i, j] <= 0.0:
                continue
            out[defenders[i].id] = threats[j].id

        return out
