from __future__ import annotations

import numpy as np

from .models import Metrics, Scenario, StepResult, ThreatType
from .random_tape import IndexedRandomTape


class SimulatorV2:
    """Evidence-oriented simulator with indexed, policy-independent randomness.

    This intentionally lives beside the legacy `Simulator` rather than replacing
    it. Old experimental protocols keep their original sequential-RNG semantics;
    new evidence-hardening protocols opt into this simulator explicitly.

    Optional diagnostic relaxations:
    - perfect_sensing: all active threats are observable at each sense step.
    - deterministic_interactions: every valid/reachable abstract interaction
      succeeds. This is a headroom diagnostic, not a deployable assumption.
    """

    def __init__(
        self,
        scenario: Scenario,
        *,
        perfect_sensing: bool = False,
        deterministic_interactions: bool = False,
    ):
        self.scenario = scenario
        self.tape = IndexedRandomTape(scenario.seed)
        self.t = 0
        self.total_penetrations = 0
        self.cumulative_damage = 0.0
        self.total_resources_used = 0
        self.perfect_sensing = bool(perfect_sensing)
        self.deterministic_interactions = bool(deterministic_interactions)
        self._diag = {
            "detection_opportunities": 0,
            "detections": 0,
            "real_interaction_attempts": 0,
            "real_interaction_failures": 0,
            "decoy_interaction_attempts": 0,
            "decoy_resource_uses": 0,
            "penetrations_undetected": 0,
            "penetrations_no_in_range_defender": 0,
            "penetrations_in_range_no_resource": 0,
            "penetrations_with_reachable_resource": 0,
            "overload_steps": 0,
        }

    def _detect(self):
        for th in self.scenario.threats:
            if not th.active or th.detected:
                continue

            if self.perfect_sensing:
                th.detected = True
                th.first_detected_t = self.t
                self._diag["detections"] += 1
                continue

            miss_prob = 1.0
            covered = False
            for sensor in self.scenario.sensors:
                dist = th.distance_to(sensor.x, sensor.y)
                if dist <= sensor.range:
                    covered = True
                    p = sensor.detection_probability * max(
                        0.15,
                        1.0 - 0.45 * (dist / max(sensor.range, 1e-9)),
                    )
                    if th.threat_type == ThreatType.DECOY:
                        p *= 0.95
                    miss_prob *= 1.0 - p

            if not covered:
                continue

            self._diag["detection_opportunities"] += 1
            u = self.tape.uniform("detect", self.t, th.id)
            if u < (1.0 - miss_prob):
                th.detected = True
                th.first_detected_t = self.t
                self._diag["detections"] += 1

    def _move_threats(self):
        for th in self.scenario.threats:
            if not th.active:
                continue
            noise_x = 0.025 * self.tape.normal("motion", self.t, th.id, "x")
            noise_y = 0.025 * self.tape.normal("motion", self.t, th.id, "y")
            th.vx += float(noise_x)
            th.vy += float(noise_y)
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
            if (
                not d.available
                or d.remaining_uses <= 0
                or not th.active
                or not th.detected
            ):
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
            p_success = float(
                np.clip(
                    0.20 + 0.55 * d.capacity * distance_factor * type_factor,
                    0.05,
                    0.90,
                )
            )

            d.remaining_uses -= 1
            d.assigned_threat_id = th.id
            resources_used += 1

            if th.threat_type == ThreatType.DECOY:
                self._diag["decoy_interaction_attempts"] += 1
                self._diag["decoy_resource_uses"] += 1
            else:
                self._diag["real_interaction_attempts"] += 1

            success = self.deterministic_interactions
            if not success:
                u = self.tape.uniform(
                    "interaction",
                    self.t,
                    d.id,
                    th.id,
                )
                success = u < p_success

            if success:
                th.active = False
                th.contained_t = self.t
                if th.threat_type != ThreatType.DECOY:
                    contained_real += 1
            elif th.threat_type != ThreatType.DECOY:
                self._diag["real_interaction_failures"] += 1

        return contained_real, resources_used

    def _update_overload_diagnostic(self):
        defenders = [
            d
            for d in self.scenario.defenders
            if d.available and d.remaining_uses > 0
        ]
        if not defenders:
            return

        reachable_real = []
        usable_defenders = set()
        for th in self.scenario.threats:
            if not th.active or not th.detected or th.threat_type == ThreatType.DECOY:
                continue
            reachable = [
                d for d in defenders if th.distance_to(d.x, d.y) <= d.range
            ]
            if reachable:
                reachable_real.append(th.id)
                usable_defenders.update(d.id for d in reachable)

        if reachable_real and len(reachable_real) > len(usable_defenders):
            self._diag["overload_steps"] += 1

    def _resolve_penetrations(self) -> tuple[int, float]:
        penetrations = 0
        damage_added = 0.0
        assets_by_id = {a.id: a for a in self.scenario.assets}

        for th in self.scenario.threats:
            if not th.active:
                continue
            asset = assets_by_id[th.target_asset_id]
            if th.distance_to(asset.x, asset.y) > asset.radius:
                continue

            th.active = False
            if th.threat_type == ThreatType.DECOY:
                continue

            if not th.detected:
                self._diag["penetrations_undetected"] += 1

            in_range = [
                d
                for d in self.scenario.defenders
                if d.available and th.distance_to(d.x, d.y) <= d.range
            ]
            reachable = [d for d in in_range if d.remaining_uses > 0]
            if not in_range:
                self._diag["penetrations_no_in_range_defender"] += 1
            elif not reachable:
                self._diag["penetrations_in_range_no_resource"] += 1
            else:
                self._diag["penetrations_with_reachable_resource"] += 1

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
            th
            for th in self.scenario.threats
            if th.active and th.threat_type != ThreatType.DECOY
        ]
        return (not real_active) or self.t >= self.scenario.max_steps

    def sense(self):
        self._detect()

    def step(self, assignments: dict[int, int | None]) -> StepResult:
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
            self._update_overload_diagnostic()
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
            th for th in self.scenario.threats if th.threat_type != ThreatType.DECOY
        ]
        contained_real = [th for th in real_threats if th.contained_t is not None]
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
            mean_response_delay=(
                float(np.mean(delays)) if delays else float(self.scenario.max_steps)
            ),
            steps=self.t,
        )

    def diagnostics(self) -> dict:
        out = dict(self._diag)
        out["resource_uses_remaining"] = int(
            sum(d.remaining_uses for d in self.scenario.defenders)
        )
        out["resource_exhausted"] = bool(
            all(d.remaining_uses <= 0 for d in self.scenario.defenders)
        )
        return out

    @staticmethod
    def evaluate_policy(
        scenario: Scenario,
        policy,
        *,
        perfect_sensing: bool = False,
        deterministic_interactions: bool = False,
    ) -> Metrics:
        sim = SimulatorV2(
            scenario,
            perfect_sensing=perfect_sensing,
            deterministic_interactions=deterministic_interactions,
        )
        return sim.run(policy)

    @staticmethod
    def evaluate_policy_with_diagnostics(
        scenario: Scenario,
        policy,
        *,
        perfect_sensing: bool = False,
        deterministic_interactions: bool = False,
    ) -> tuple[Metrics, dict]:
        sim = SimulatorV2(
            scenario,
            perfect_sensing=perfect_sensing,
            deterministic_interactions=deterministic_interactions,
        )
        metrics = sim.run(policy)
        return metrics, sim.diagnostics()
