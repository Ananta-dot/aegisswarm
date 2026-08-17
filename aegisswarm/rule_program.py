from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import numpy as np

from .models import ThreatType
from .policies import Policy, distance_to_target


MAX_RULES = 12
RULE_WIDTH = 5
TOKEN_LEVELS = 16
PROGRAM_LENGTH = MAX_RULES * RULE_WIDTH


class Condition(IntEnum):
    ALWAYS = 0
    URGENCY_GT = 1
    DISTANCE_LT = 2
    FAST = 3
    DIRECT = 4
    DECOY = 5
    LOW_RESOURCES = 6
    HIGH_DAMAGE = 7


class Action(IntEnum):
    ADD_PRIORITY = 0
    SUB_PRIORITY = 1
    RESERVE = 2
    RELEASE_RESERVE = 3
    BOOST_STICKINESS = 4
    PENALIZE_DECOY = 5


@dataclass(frozen=True)
class Rule:
    enabled: bool
    condition: Condition
    threshold: float
    action: Action
    magnitude: float


def _scale(v: int, lo: float, hi: float) -> float:
    v = int(np.clip(v, 0, TOKEN_LEVELS - 1))
    return lo + (hi - lo) * v / (TOKEN_LEVELS - 1)


def decode_program(tokens) -> list[Rule]:
    arr = np.asarray(tokens, dtype=np.int16).reshape(MAX_RULES, RULE_WIDTH)
    rules = []
    for row in arr:
        enabled = int(row[0]) >= TOKEN_LEVELS // 2
        condition = Condition(int(row[1]) % len(Condition))
        threshold = _scale(int(row[2]), 0.0, 1.0)
        action = Action(int(row[3]) % len(Action))
        magnitude = _scale(int(row[4]), 0.0, 4.0)
        rules.append(Rule(enabled, condition, threshold, action, magnitude))
    return rules


def random_program(rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, TOKEN_LEVELS, size=PROGRAM_LENGTH, dtype=np.int16)


def mutate_program(tokens, rng, n_mutations=2, radius=4):
    out = np.asarray(tokens, dtype=np.int16).copy()
    for _ in range(max(1, int(n_mutations))):
        idx = int(rng.integers(0, PROGRAM_LENGTH))
        if idx % RULE_WIDTH in (1, 3):
            out[idx] = int(rng.integers(0, TOKEN_LEVELS))
        else:
            delta = int(rng.integers(-radius, radius + 1))
            if delta == 0:
                delta = 1
            out[idx] = int(np.clip(int(out[idx]) + delta, 0, TOKEN_LEVELS - 1))
    return out


def crossover_program(a, b, rng):
    a = np.asarray(a, dtype=np.int16).reshape(MAX_RULES, RULE_WIDTH)
    b = np.asarray(b, dtype=np.int16).reshape(MAX_RULES, RULE_WIDTH)
    mask = rng.random(MAX_RULES) < 0.5
    child = np.where(mask[:, None], a, b)
    return child.reshape(-1).astype(np.int16)


class RuleProgramPolicy(Policy):
    """State-reactive policy built from an ordered sequence of abstract rules."""

    name = "rule_program"

    def __init__(self, tokens, name="rule_program"):
        self.tokens = np.asarray(tokens, dtype=np.int16).copy()
        if self.tokens.shape != (PROGRAM_LENGTH,):
            raise ValueError(f"Expected program shape {(PROGRAM_LENGTH,)}, got {self.tokens.shape}")
        self.rules = decode_program(self.tokens)
        self.name = name

    def reset(self, seed: int):
        self.seed = int(seed)

    @staticmethod
    def _type_prior(th):
        if th.threat_type == ThreatType.FAST:
            return 1.25
        if th.threat_type == ThreatType.DIRECT:
            return 1.0
        return 0.2

    def _condition_matches(self, rule, scenario, defender, threat, d_asset, d_def):
        if rule.condition == Condition.ALWAYS:
            return True
        if rule.condition == Condition.URGENCY_GT:
            urgency = 1.0 / max(d_asset, 1.0)
            return urgency > _scale(int(round(rule.threshold * 15)), 0.01, 0.20)
        if rule.condition == Condition.DISTANCE_LT:
            normalized = d_def / max(defender.range, 1e-9)
            return normalized < max(0.05, rule.threshold)
        if rule.condition == Condition.FAST:
            return threat.threat_type == ThreatType.FAST
        if rule.condition == Condition.DIRECT:
            return threat.threat_type == ThreatType.DIRECT
        if rule.condition == Condition.DECOY:
            return threat.threat_type == ThreatType.DECOY
        if rule.condition == Condition.LOW_RESOURCES:
            frac = defender.remaining_uses / max(1.0, scenario.metadata.get("initial_defender_uses", 1.0) / max(len(scenario.defenders), 1))
            return frac < max(0.05, rule.threshold)
        if rule.condition == Condition.HIGH_DAMAGE:
            damage = sum(a.damage / max(a.value, 1e-9) for a in scenario.assets) / max(len(scenario.assets), 1)
            return damage > rule.threshold
        return False

    def assign(self, scenario, t):
        detected = [th for th in scenario.threats if th.active and th.detected]
        out = {d.id: None for d in scenario.defenders}
        candidates = []

        for defender in scenario.defenders:
            if not defender.available or defender.remaining_uses <= 0:
                continue

            reserve = 0
            for threat in detected:
                d_def = threat.distance_to(defender.x, defender.y)
                if d_def > defender.range:
                    continue

                d_asset = distance_to_target(scenario, threat)
                base = (
                    2.0 * self._type_prior(threat)
                    + 1.5 / max(d_asset, 1.0)
                    + 1.0 / max(d_def, 1.0)
                )
                score = base
                local_reserve = reserve

                for rule in self.rules:
                    if not rule.enabled:
                        continue
                    if not self._condition_matches(rule, scenario, defender, threat, d_asset, d_def):
                        continue

                    if rule.action == Action.ADD_PRIORITY:
                        score += rule.magnitude
                    elif rule.action == Action.SUB_PRIORITY:
                        score -= rule.magnitude
                    elif rule.action == Action.RESERVE:
                        local_reserve = max(local_reserve, int(round(rule.magnitude)))
                    elif rule.action == Action.RELEASE_RESERVE:
                        local_reserve = 0
                    elif rule.action == Action.BOOST_STICKINESS and defender.assigned_threat_id == threat.id:
                        score += rule.magnitude
                    elif rule.action == Action.PENALIZE_DECOY and threat.threat_type == ThreatType.DECOY:
                        score -= rule.magnitude

                if defender.remaining_uses <= local_reserve and d_asset > 10.0:
                    continue
                candidates.append((score, defender.id, threat.id))

        candidates.sort(reverse=True)
        used_d, used_t = set(), set()
        for score, did, tid in candidates:
            if score <= 0.0 or did in used_d or tid in used_t:
                continue
            out[did] = tid
            used_d.add(did)
            used_t.add(tid)

        return out
