from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .models import ThreatType
from .policies import Policy, distance_to_target
from .strategy import GENE_LEVELS, GENOME_LENGTH, GenomeSpec, decode_genome

GENOME_V2_LENGTH = 20


@dataclass(frozen=True)
class AdaptiveGenomeSpec:
    base: GenomeSpec
    high_density_threshold: float
    high_density_urgency_boost: float
    high_density_speed_boost: float
    low_resource_threshold: float
    low_resource_conservation_boost: float
    low_resource_reserve_boost: int
    imminent_distance_threshold: float
    imminent_urgency_boost: float
    damage_threshold: float
    damaged_asset_urgency_boost: float
    damaged_asset_stickiness_boost: float
    assignment_bias: float


def _scale(g: int, lo: float, hi: float) -> float:
    g = int(np.clip(g, 0, GENE_LEVELS - 1))
    return lo + (hi - lo) * g / (GENE_LEVELS - 1)


def decode_genome_v2(genes) -> AdaptiveGenomeSpec:
    genes = [int(np.clip(x, 0, GENE_LEVELS - 1)) for x in genes]
    if len(genes) != GENOME_V2_LENGTH:
        raise ValueError(f"Expected {GENOME_V2_LENGTH} genes")

    return AdaptiveGenomeSpec(
        base=decode_genome(genes[:GENOME_LENGTH]),
        high_density_threshold=_scale(genes[8], 0.75, 3.0),
        high_density_urgency_boost=_scale(genes[9], 0.0, 4.0),
        high_density_speed_boost=_scale(genes[10], 0.0, 2.0),
        low_resource_threshold=_scale(genes[11], 0.15, 0.70),
        low_resource_conservation_boost=_scale(genes[12], 0.0, 3.0),
        low_resource_reserve_boost=int(round(_scale(genes[13], 0.0, 2.0))),
        imminent_distance_threshold=_scale(genes[14], 8.0, 30.0),
        imminent_urgency_boost=_scale(genes[15], 0.0, 5.0),
        damage_threshold=_scale(genes[16], 0.05, 0.75),
        damaged_asset_urgency_boost=_scale(genes[17], 0.0, 4.0),
        damaged_asset_stickiness_boost=_scale(genes[18], 0.0, 2.0),
        assignment_bias=_scale(genes[19], -1.0, 1.0),
    )


def random_genome_v2(rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, GENE_LEVELS, size=GENOME_V2_LENGTH, dtype=np.int16)


def mutate_genome_v2(genes, rng, n_mutations=1, radius=3):
    out = np.asarray(genes, dtype=np.int16).copy()
    if out.shape != (GENOME_V2_LENGTH,):
        raise ValueError(f"Expected genome shape ({GENOME_V2_LENGTH},)")
    for _ in range(max(1, int(n_mutations))):
        idx = int(rng.integers(0, GENOME_V2_LENGTH))
        delta = int(rng.integers(-radius, radius + 1))
        if delta == 0:
            delta = 1
        out[idx] = int(np.clip(int(out[idx]) + delta, 0, GENE_LEVELS - 1))
    return out


class AdaptiveGenomePolicy(Policy):
    """Adaptive policy encoded by a 20-token discrete genome.

    The first eight genes preserve the v1 policy semantics. The remaining genes
    learn when and how to alter those weights as the observable scenario state
    changes (density, resource pressure, imminence, and asset damage).
    """

    name = "adaptive_v2"

    def __init__(self, genes, name="adaptive_v2"):
        self.genes = np.asarray(genes, dtype=np.int16).copy()
        self.spec = decode_genome_v2(self.genes)
        self.name = name

    def reset(self, seed: int):
        self.seed = int(seed)

    @staticmethod
    def _type_prior(th):
        if th.threat_type == ThreatType.FAST:
            return 1.25
        if th.threat_type == ThreatType.DIRECT:
            return 1.00
        return 0.20

    def assign(self, scenario, t):
        detected = [th for th in scenario.threats if th.active and th.detected]
        defenders = [
            d for d in scenario.defenders
            if d.available and d.remaining_uses > 0
        ]
        out = {d.id: None for d in scenario.defenders}
        if not detected or not defenders:
            return out

        density = len(detected) / max(len(defenders), 1)
        high_density = density >= self.spec.high_density_threshold

        remaining_uses = sum(max(0, d.remaining_uses) for d in scenario.defenders)
        initial_uses = max(
            1,
            int(scenario.metadata.get("initial_defender_uses", remaining_uses)),
        )
        resource_ratio = remaining_uses / initial_uses
        low_resources = resource_ratio <= self.spec.low_resource_threshold

        base = self.spec.base
        pairs = []

        for d in defenders:
            reserve_threshold = base.reserve_threshold
            if low_resources:
                reserve_threshold += self.spec.low_resource_reserve_boost

            for th in detected:
                dist = th.distance_to(d.x, d.y)
                if dist > d.range:
                    continue

                target = next(a for a in scenario.assets if a.id == th.target_asset_id)
                target_damage = target.damage / max(target.value, 1e-9)
                damaged_target = target_damage >= self.spec.damage_threshold

                d_asset = distance_to_target(scenario, th)
                imminent = d_asset <= self.spec.imminent_distance_threshold

                if d.remaining_uses <= reserve_threshold:
                    if th.threat_type == ThreatType.DECOY or not imminent:
                        continue

                urgency_weight = base.urgency_weight
                speed_weight = base.speed_weight
                stickiness_weight = base.assignment_stickiness
                conservation_weight = base.resource_preservation_weight

                if high_density:
                    urgency_weight += self.spec.high_density_urgency_boost
                    speed_weight += self.spec.high_density_speed_boost
                if low_resources:
                    conservation_weight += self.spec.low_resource_conservation_boost
                if imminent:
                    urgency_weight += self.spec.imminent_urgency_boost
                if damaged_target:
                    urgency_weight += self.spec.damaged_asset_urgency_boost
                    stickiness_weight += self.spec.damaged_asset_stickiness_boost

                urgency = 1.0 / max(d_asset, 1.0)
                closeness = 1.0 / max(dist, 1.0)
                type_prior = self._type_prior(th)
                speed = min(th.speed / 2.0, 1.5)
                sticky = 1.0 if d.assigned_threat_id == th.id else 0.0
                scarcity = 1.0 / max(d.remaining_uses, 1)
                decoy = 1.0 if th.threat_type == ThreatType.DECOY else 0.0

                score = (
                    urgency_weight * urgency
                    + base.defender_distance_weight * closeness
                    + base.type_priority_weight * type_prior
                    + speed_weight * speed
                    + stickiness_weight * sticky
                    - conservation_weight * scarcity
                    - base.decoy_penalty * decoy
                    + self.spec.assignment_bias
                )
                pairs.append((score, d.id, th.id))

        pairs.sort(reverse=True)
        used_d, used_t = set(), set()
        for score, did, tid in pairs:
            if score <= 0.0 or did in used_d or tid in used_t:
                continue
            out[did] = tid
            used_d.add(did)
            used_t.add(tid)

        return out
