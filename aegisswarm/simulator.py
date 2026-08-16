from __future__ import annotations

import numpy as np

from .models import Scenario, ThreatType, StepResult, Metrics


class Simulator:
    """
    Abstract counter-swarm coordination simulator.

    Defensive interactions are deliberately represented by synthetic probabilities.
    """

    def __init__(self, scenario: Scenario):
        self.scenario = scenario
        self.rng = np.random.default_rng(scenario.seed)
        self.t = 0
        self.total_penetrations = 0
        self.cumulative_damage = 0.0
        self.total_resources_used = 0

    def _detect(self):
        for th in self.scenario.threats:
            if not th.active or th.detected:
                continue
            miss_prob = 1.0
            for sensor in self.scenario.sensors:
                dist = th.distance_to(sensor.x, sensor.y)
                if dist <= sensor.range:
                    p = sensor.detection_probability * max(
                        0.15, 1.0 - 0.45 * (dist / max(sensor.range, 1e-9))
                    )
                    if th.threat_type == ThreatType.DECOY:
                        p *= 0.95
                    miss_prob *= (1.0 - p)
            if self.rng.random() < (1.0 - miss_prob):
                th.detected = True
                th.first_detected_t = self.t

    def _move_threats(self):
        for th in self.scenario.threats:
            if not th.active:
                continue
            noise = self.rng.normal(0.0, 0.025, size=2)
            th.vx += float(noise[0])
            th.vy += float(noise[1])
            th.x += th.vx * self.scenario.dt
            th.y += th.vy * self.scenario.dt
            th.age += 1

    def _resolve_assignments(self, assignments: dict[int, int | None]) -> tuple[int, int]:
        threats_by_id = {th.id: th for th in self.scenario.threats}
        defenders_by_id = {d.id: d for d in self.scenario.defenders}
        contained_real = 0
        resources_used = 0

        for defender_id, threat_id in assignments.items():
            if threat_id is None:
                continue
            d = defenders_by_id.get(int(defender_id))
            th = threats_by_id.get(int(threat_id))
            if d is None or th is None:
                continue
            if not d.available or d.remaining_uses <= 0 or not th.active or not th.detected:
                continue

            dist = th.distance_to(d.x, d.y)
            if dist > d.range:
                continue

            distance_factor = max(0.10, 1.0 - dist / max(d.range, 1e-9))
            type_factor = {
                ThreatType.DIRECT: 1.00,
                ThreatType.FAST: 0.82,
                ThreatType.DECOY: 1.08,
            }[th.threat_type]
            p_success = float(np.clip(
                0.20 + 0.55 * d.capacity * distance_factor * type_factor,
                0.05,
                0.90,
            ))

            d.remaining_uses -= 1
            d.assigned_threat_id = th.id
            resources_used += 1

            if self.rng.random() < p_success:
                th.active = False
                th.contained_t = self.t
                if th.threat_type != ThreatType.DECOY:
                    contained_real += 1

        return contained_real, resources_used

    def _resolve_penetrations(self) -> tuple[int, float]:
        penetrations = 0
        damage_added = 0.0
        assets_by_id = {a.id: a for a in self.scenario.assets}

        for th in self.scenario.threats:
            if not th.active:
                continue
            asset = assets_by_id[th.target_asset_id]
            if th.distance_to(asset.x, asset.y) <= asset.radius:
                th.active = False
                if th.threat_type == ThreatType.DECOY:
                    continue

                penetrations += 1
                base = 0.45 if th.threat_type == ThreatType.DIRECT else 0.60
                dmg = base * asset.value
                asset.damage += dmg
                damage_added += dmg
                if asset.damage >= asset.value:
                    asset.alive = False

        return penetrations, damage_added

    def is_done(self) -> bool:
        real_active = [
            th for th in self.scenario.threats
            if th.active and th.threat_type != ThreatType.DECOY
        ]
        return (not real_active) or self.t >= self.scenario.max_steps

    def sense(self):
        """Advance the abstract observation model for the current timestep."""
        self._detect()

    def step(self, assignments: dict[int, int | None]) -> StepResult:
        """
        Apply one coordination decision after `sense()` has been called.
        """
        if self.is_done():
            return StepResult(done=True)

        contained_real, used = self._resolve_assignments(assignments)
        self._move_threats()
        penetrations, damage = self._resolve_penetrations()

        self.total_penetrations += penetrations
        self.cumulative_damage += damage
        self.total_resources_used += used
        self.t += 1

        return StepResult(
            contained_real=contained_real,
            penetrations=penetrations,
            damage_added=damage,
            resources_used=used,
            done=self.is_done(),
        )

    def run(self, policy) -> Metrics:
        policy.reset(self.scenario.seed)

        while not self.is_done():
            self.sense()
            assignments = policy.assign(self.scenario, self.t)
            contained_real, used = self._resolve_assignments(assignments)
            self._move_threats()
            penetrations, damage = self._resolve_penetrations()

            self.total_penetrations += penetrations
            self.cumulative_damage += damage
            self.total_resources_used += used
            self.t += 1

        return self.metrics(policy.name)

    def metrics(self, policy_name: str) -> Metrics:
        real_threats = [
            th for th in self.scenario.threats
            if th.threat_type != ThreatType.DECOY
        ]
        contained_real = [
            th for th in real_threats
            if th.contained_t is not None
        ]

        delays = [
            th.contained_t - th.first_detected_t
            for th in contained_real
            if th.contained_t is not None and th.first_detected_t is not None
        ]

        return Metrics(
            seed=self.scenario.seed,
            policy=policy_name,
            total_threats=len(self.scenario.threats),
            real_threats=len(real_threats),
            contained_real_threats=len(contained_real),
            penetrations=self.total_penetrations,
            assets_total=len(self.scenario.assets),
            assets_survived=sum(1 for a in self.scenario.assets if a.alive),
            defenders_consumed=self.total_resources_used,
            cumulative_damage=self.cumulative_damage,
            mean_response_delay=float(np.mean(delays)) if delays else float(self.scenario.max_steps),
            steps=self.t,
        )

    @staticmethod
    def evaluate_policy(scenario: Scenario, policy) -> Metrics:
        return Simulator(scenario).run(policy)
