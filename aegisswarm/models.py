from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List
import math


class ThreatType(str, Enum):
    DIRECT = "direct"
    FAST = "fast"
    DECOY = "decoy"


@dataclass
class Threat:
    id: int
    x: float
    y: float
    vx: float
    vy: float
    threat_type: ThreatType
    target_asset_id: int
    active: bool = True
    detected: bool = False
    age: int = 0
    first_detected_t: Optional[int] = None
    contained_t: Optional[int] = None

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)


@dataclass
class Defender:
    id: int
    x: float
    y: float
    capacity: float
    range: float
    remaining_uses: int
    available: bool = True
    assigned_threat_id: Optional[int] = None


@dataclass
class ProtectedAsset:
    id: int
    x: float
    y: float
    value: float
    radius: float
    alive: bool = True
    damage: float = 0.0


@dataclass
class Sensor:
    id: int
    x: float
    y: float
    range: float
    detection_probability: float


@dataclass
class Scenario:
    threats: List[Threat]
    defenders: List[Defender]
    assets: List[ProtectedAsset]
    sensors: List[Sensor]
    dt: float = 1.0
    max_steps: int = 150
    world_size: float = 100.0
    seed: int = 0
    metadata: Dict[str, float] = field(default_factory=dict)


@dataclass
class StepResult:
    contained_real: int = 0
    penetrations: int = 0
    damage_added: float = 0.0
    resources_used: int = 0
    done: bool = False


@dataclass
class Metrics:
    seed: int
    policy: str
    total_threats: int
    real_threats: int
    contained_real_threats: int
    penetrations: int
    assets_total: int
    assets_survived: int
    defenders_consumed: int
    cumulative_damage: float
    mean_response_delay: float
    steps: int

    @property
    def containment_rate(self) -> float:
        return self.contained_real_threats / self.real_threats if self.real_threats else 1.0

    @property
    def asset_survival_rate(self) -> float:
        return self.assets_survived / self.assets_total if self.assets_total else 1.0

    def as_dict(self) -> dict:
        return {
            "seed": self.seed,
            "policy": self.policy,
            "total_threats": self.total_threats,
            "real_threats": self.real_threats,
            "contained_real_threats": self.contained_real_threats,
            "containment_rate": self.containment_rate,
            "penetrations": self.penetrations,
            "assets_total": self.assets_total,
            "assets_survived": self.assets_survived,
            "asset_survival_rate": self.asset_survival_rate,
            "defenders_consumed": self.defenders_consumed,
            "cumulative_damage": self.cumulative_damage,
            "mean_response_delay": self.mean_response_delay,
            "steps": self.steps,
        }
