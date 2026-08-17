from __future__ import annotations

import numpy as np

from .hybrid import RuleGuidedHungarianPolicy
from .scenarios import ScenarioGenerator
from .scoring import EvalConfig
from .simulator import Simulator


def evaluate_hybrid_program(tokens, config: EvalConfig):
    """Evaluate a strategic rule program executed through the optimizer layer.

    Uses the exact same scalar fitness definition as the existing rule-program
    evaluator so greedy and hybrid execution remain directly comparable.
    """
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
                RuleGuidedHungarianPolicy(tokens),
            ).as_dict()
        )

    survival = float(np.mean([r["asset_survival_rate"] for r in rows]))
    containment = float(np.mean([r["containment_rate"] for r in rows]))
    penetrations = float(np.mean([r["penetrations"] for r in rows]))
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
        "penetrations": penetrations,
        "cumulative_damage": damage,
        "defenders_consumed": resources,
        "mean_response_delay": response,
    }
