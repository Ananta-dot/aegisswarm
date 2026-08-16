from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .models import ThreatType
from .policies import Policy, distance_to_target


GENE_LEVELS = 16
GENOME_LENGTH = 8


@dataclass(frozen=True)
class GenomeSpec:
    urgency_weight: float
    defender_distance_weight: float
    type_priority_weight: float
    speed_weight: float
    assignment_stickiness: float
    resource_preservation_weight: float
    decoy_penalty: float
    reserve_threshold: int


def _scale(g: int, lo: float, hi: float) -> float:
    g = int(np.clip(g, 0, GENE_LEVELS - 1))
    return lo + (hi - lo) * g / (GENE_LEVELS - 1)


def decode_genome(genes) -> GenomeSpec:
    genes = [int(np.clip(x, 0, GENE_LEVELS - 1)) for x in genes]
    if len(genes) != GENOME_LENGTH:
        raise ValueError(f"Expected {GENOME_LENGTH} genes")
    return GenomeSpec(
        urgency_weight=_scale(genes[0], 0.0, 4.0),
        defender_distance_weight=_scale(genes[1], 0.0, 3.0),
        type_priority_weight=_scale(genes[2], 0.0, 3.0),
        speed_weight=_scale(genes[3], 0.0, 2.0),
        assignment_stickiness=_scale(genes[4], 0.0, 2.0),
        resource_preservation_weight=_scale(genes[5], 0.0, 2.0),
        decoy_penalty=_scale(genes[6], 0.0, 4.0),
        reserve_threshold=int(round(_scale(genes[7], 0.0, 2.0))),
    )


def random_genome(rng: np.random.Generator) -> np.ndarray:
    return rng.integers(0, GENE_LEVELS, size=GENOME_LENGTH, dtype=np.int16)


def mutate_genome(genes, rng, n_mutations=1, radius=3):
    out = np.asarray(genes, dtype=np.int16).copy()
    for _ in range(max(1, int(n_mutations))):
        idx = int(rng.integers(0, GENOME_LENGTH))
        delta = int(rng.integers(-radius, radius + 1))
        if delta == 0:
            delta = 1
        out[idx] = int(np.clip(int(out[idx]) + delta, 0, GENE_LEVELS - 1))
    return out


class GenomePolicy(Policy):
    name = "genome"

    def __init__(self, genes, name="genome"):
        self.genes = np.asarray(genes, dtype=np.int16).copy()
        self.spec = decode_genome(self.genes)
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
        out = {d.id: None for d in scenario.defenders}
        pairs = []

        for d in scenario.defenders:
            if not d.available or d.remaining_uses <= 0:
                continue

            for th in detected:
                dist = th.distance_to(d.x, d.y)
                if dist > d.range:
                    continue

                d_asset = distance_to_target(scenario, th)
                urgency = 1.0 / max(d_asset, 1.0)
                closeness = 1.0 / max(dist, 1.0)
                type_prior = self._type_prior(th)
                speed = min(th.speed / 2.0, 1.5)
                sticky = 1.0 if d.assigned_threat_id == th.id else 0.0
                scarcity = 1.0 / max(d.remaining_uses, 1)
                decoy = 1.0 if th.threat_type == ThreatType.DECOY else 0.0

                if d.remaining_uses <= self.spec.reserve_threshold:
                    if th.threat_type == ThreatType.DECOY or d_asset > 12.0:
                        continue

                score = (
                    self.spec.urgency_weight * urgency
                    + self.spec.defender_distance_weight * closeness
                    + self.spec.type_priority_weight * type_prior
                    + self.spec.speed_weight * speed
                    + self.spec.assignment_stickiness * sticky
                    - self.spec.resource_preservation_weight * scarcity
                    - self.spec.decoy_penalty * decoy
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
