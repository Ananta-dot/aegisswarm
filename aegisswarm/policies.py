from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np

from .models import Scenario, Threat, ThreatType


def type_priority(threat: Threat) -> float:
    if threat.threat_type == ThreatType.FAST:
        return 1.25
    if threat.threat_type == ThreatType.DIRECT:
        return 1.00
    return 0.20


def distance_to_target(scenario: Scenario, threat: Threat) -> float:
    asset = next(a for a in scenario.assets if a.id == threat.target_asset_id)
    return threat.distance_to(asset.x, asset.y)


class Policy(ABC):
    name = "base"

    def reset(self, seed: int):
        return

    @abstractmethod
    def assign(self, scenario: Scenario, t: int) -> dict[int, int | None]:
        raise NotImplementedError


class RandomPolicy(Policy):
    name = "random"

    def reset(self, seed: int):
        self.rng = np.random.default_rng(seed + 100_003)

    def assign(self, scenario: Scenario, t: int):
        detected = [th for th in scenario.threats if th.active and th.detected]
        out = {}
        for d in scenario.defenders:
            if not d.available or d.remaining_uses <= 0 or not detected:
                out[d.id] = None
            else:
                out[d.id] = int(self.rng.choice([th.id for th in detected]))
        return out


class ClosestThreatPolicy(Policy):
    name = "closest"

    def assign(self, scenario: Scenario, t: int):
        detected = [th for th in scenario.threats if th.active and th.detected]
        out = {}
        for d in scenario.defenders:
            reachable = [th for th in detected if th.distance_to(d.x, d.y) <= d.range]
            if not d.available or d.remaining_uses <= 0 or not reachable:
                out[d.id] = None
            else:
                out[d.id] = min(reachable, key=lambda th: th.distance_to(d.x, d.y)).id
        return out


class HighestRiskPolicy(Policy):
    name = "highest_risk"

    def assign(self, scenario: Scenario, t: int):
        detected = [th for th in scenario.threats if th.active and th.detected]
        ranked = sorted(
            detected,
            key=lambda th: type_priority(th) / max(distance_to_target(scenario, th), 1.0),
            reverse=True,
        )
        out = {d.id: None for d in scenario.defenders}
        used = set()
        for d in scenario.defenders:
            if not d.available or d.remaining_uses <= 0:
                continue
            for th in ranked:
                if th.id in used:
                    continue
                if th.distance_to(d.x, d.y) <= d.range:
                    out[d.id] = th.id
                    used.add(th.id)
                    break
        return out


class GreedyRiskCostPolicy(Policy):
    name = "greedy_risk_cost"

    def assign(self, scenario: Scenario, t: int):
        detected = [th for th in scenario.threats if th.active and th.detected]
        defenders = [d for d in scenario.defenders if d.available and d.remaining_uses > 0]
        out = {d.id: None for d in scenario.defenders}
        pairs = []

        for d in defenders:
            for th in detected:
                dist = th.distance_to(d.x, d.y)
                if dist > d.range:
                    continue
                urgency = 1.0 / max(distance_to_target(scenario, th), 1.0)
                utility = (
                    4.0 * type_priority(th) * urgency
                    + 1.5 / max(dist, 1.0)
                    - 0.15 / max(d.remaining_uses, 1)
                )
                pairs.append((utility, d.id, th.id))

        pairs.sort(reverse=True)
        used_d, used_t = set(), set()
        for utility, did, tid in pairs:
            if did in used_d or tid in used_t:
                continue
            out[did] = tid
            used_d.add(did)
            used_t.add(tid)
        return out


BASELINE_POLICIES = {
    "random": RandomPolicy,
    "closest": ClosestThreatPolicy,
    "highest_risk": HighestRiskPolicy,
    "greedy_risk_cost": GreedyRiskCostPolicy,
}
