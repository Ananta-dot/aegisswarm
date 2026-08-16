from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .strategy import GenomePolicy


@dataclass(frozen=True)
class EvalConfig:
    seeds: tuple[int, ...]
    n_threats: int = 30
    n_defenders: int = 8
    n_assets: int = 2
    n_sensors: int = 3
    max_steps: int = 150
    decoy_fraction: float = 0.20
    fast_fraction: float = 0.25
    sensor_quality: float = 1.0


def evaluate_genome(genes, config: EvalConfig):
    gen = ScenarioGenerator(max_steps=config.max_steps)
    rows = []

    for seed in config.seeds:
        scenario = gen.generate(
            seed=int(seed),
            n_threats=config.n_threats,
            n_defenders=config.n_defenders,
            n_assets=config.n_assets,
            n_sensors=config.n_sensors,
            decoy_fraction=config.decoy_fraction,
            fast_fraction=config.fast_fraction,
            sensor_quality=config.sensor_quality,
        )
        rows.append(
            Simulator.evaluate_policy(
                scenario,
                GenomePolicy(genes),
            ).as_dict()
        )

    survival = float(np.mean([r["asset_survival_rate"] for r in rows]))
    containment = float(np.mean([r["containment_rate"] for r in rows]))
    damage = float(np.mean([r["cumulative_damage"] for r in rows]))
    resources = float(np.mean([r["defenders_consumed"] for r in rows]))
    response = float(np.mean([r["mean_response_delay"] for r in rows]))

    loss = (
        100.0 * (1.0 - survival)
        + 40.0 * (1.0 - containment)
        + 3.0 * damage
        + 0.15 * resources
        + 0.05 * response
    )
    fitness = max(0.0, 200.0 - loss)

    return {
        "fitness": float(fitness),
        "loss": float(loss),
        "asset_survival_rate": survival,
        "containment_rate": containment,
        "cumulative_damage": damage,
        "defenders_consumed": resources,
        "mean_response_delay": response,
    }
