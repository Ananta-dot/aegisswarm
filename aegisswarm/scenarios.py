from __future__ import annotations

import copy
import math
import numpy as np

from .models import Threat, ThreatType, Defender, ProtectedAsset, Sensor, Scenario


class ScenarioGenerator:
    """
    Synthetic, normalized scenario generator.

    Parameters are dimensionless research values and are intentionally not tied to
    real-world sensors, interceptors, or weapon systems.
    """

    def __init__(self, world_size: float = 100.0, max_steps: int = 150):
        self.world_size = float(world_size)
        self.max_steps = int(max_steps)

    def generate(
        self,
        seed: int,
        n_threats: int = 30,
        n_defenders: int = 8,
        n_assets: int = 2,
        n_sensors: int = 3,
        decoy_fraction: float = 0.20,
        fast_fraction: float = 0.25,
        sensor_quality: float = 1.0,
    ) -> Scenario:
        rng = np.random.default_rng(seed)

        assets = []
        for i in range(n_assets):
            x = self.world_size * (0.38 + 0.24 * rng.random())
            y = self.world_size * (0.38 + 0.24 * rng.random())
            assets.append(
                ProtectedAsset(
                    id=i,
                    x=float(x),
                    y=float(y),
                    value=float(rng.uniform(1.0, 2.0)),
                    radius=float(rng.uniform(3.0, 5.0)),
                )
            )

        sensors = []
        for i in range(n_sensors):
            anchor = assets[i % len(assets)]
            base_detection = rng.uniform(0.72, 0.92) * sensor_quality
            sensors.append(
                Sensor(
                    id=i,
                    x=float(anchor.x + rng.uniform(-12, 12)),
                    y=float(anchor.y + rng.uniform(-12, 12)),
                    range=float(rng.uniform(35, 55)),
                    detection_probability=float(np.clip(base_detection, 0.20, 0.98)),
                )
            )

        defenders = []
        for i in range(n_defenders):
            anchor = assets[i % len(assets)]
            defenders.append(
                Defender(
                    id=i,
                    x=float(anchor.x + rng.uniform(-10, 10)),
                    y=float(anchor.y + rng.uniform(-10, 10)),
                    capacity=float(rng.uniform(0.75, 1.15)),
                    range=float(rng.uniform(18, 28)),
                    remaining_uses=int(rng.integers(3, 6)),
                )
            )

        threats = []
        for i in range(n_threats):
            r = rng.random()
            if r < decoy_fraction:
                ttype = ThreatType.DECOY
            elif r < decoy_fraction + fast_fraction:
                ttype = ThreatType.FAST
            else:
                ttype = ThreatType.DIRECT

            side = int(rng.integers(0, 4))
            if side == 0:
                x, y = 0.0, float(rng.uniform(0, self.world_size))
            elif side == 1:
                x, y = self.world_size, float(rng.uniform(0, self.world_size))
            elif side == 2:
                x, y = float(rng.uniform(0, self.world_size)), 0.0
            else:
                x, y = float(rng.uniform(0, self.world_size)), self.world_size

            target = assets[int(rng.integers(0, len(assets)))]
            dx, dy = target.x - x, target.y - y
            norm = max(math.hypot(dx, dy), 1e-9)

            base_speed = {
                ThreatType.DIRECT: 1.05,
                ThreatType.FAST: 1.50,
                ThreatType.DECOY: 0.95,
            }[ttype]

            jitter = rng.normal(0.0, 0.10, size=2)
            vx = base_speed * dx / norm + jitter[0]
            vy = base_speed * dy / norm + jitter[1]

            threats.append(
                Threat(
                    id=i,
                    x=float(x),
                    y=float(y),
                    vx=float(vx),
                    vy=float(vy),
                    threat_type=ttype,
                    target_asset_id=target.id,
                )
            )

        return Scenario(
            threats=threats,
            defenders=defenders,
            assets=assets,
            sensors=sensors,
            max_steps=self.max_steps,
            world_size=self.world_size,
            seed=int(seed),
            metadata={
                "initial_defender_uses": int(sum(d.remaining_uses for d in defenders)),
                "n_threats": int(n_threats),
                "n_defenders": int(n_defenders),
                "n_assets": int(n_assets),
                "n_sensors": int(n_sensors),
                "decoy_fraction": float(decoy_fraction),
                "fast_fraction": float(fast_fraction),
                "sensor_quality": float(sensor_quality),
            },
        )

    @staticmethod
    def clone(scenario: Scenario) -> Scenario:
        return copy.deepcopy(scenario)
