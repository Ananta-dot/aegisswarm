from __future__ import annotations

import time
import numpy as np

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .policies import BASELINE_POLICIES
from .optimization import HungarianPolicy
from .strategy import GenomePolicy
from .rl import QLearningPolicy


def bootstrap_ci(values, seed=1234, n_boot=2000, alpha=0.05):
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        means.append(float(np.mean(sample)))
    return [
        float(np.quantile(means, alpha / 2)),
        float(np.quantile(means, 1 - alpha / 2)),
    ]


def evaluate_policies(
    seeds,
    scenario_kwargs=None,
    qtable=None,
    genome=None,
):
    scenario_kwargs = dict(scenario_kwargs or {})
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.pop("max_steps", 150)))

    factories = dict(BASELINE_POLICIES)
    factories["hungarian"] = HungarianPolicy

    policies = {name: factory() for name, factory in factories.items()}
    if qtable is not None:
        policies["q_learning"] = QLearningPolicy(qtable)
    if genome is not None:
        policies["axplorer"] = GenomePolicy(genome, name="axplorer")

    raw = {name: [] for name in policies}
    runtime = {name: [] for name in policies}

    for seed in seeds:
        base = gen.generate(seed=int(seed), **scenario_kwargs)

        for name, policy in policies.items():
            start = time.perf_counter()
            metrics = Simulator.evaluate_policy(gen.clone(base), policy)
            runtime[name].append(time.perf_counter() - start)
            raw[name].append(metrics.as_dict())

    summary = {}
    keys = [
        "asset_survival_rate",
        "containment_rate",
        "penetrations",
        "cumulative_damage",
        "defenders_consumed",
        "mean_response_delay",
    ]

    for name, rows in raw.items():
        stats = {}
        for key in keys:
            vals = [float(r[key]) for r in rows]
            stats[key] = {
                "mean": float(np.mean(vals)),
                "std": float(np.std(vals)),
                "ci95": bootstrap_ci(vals, seed=777 + len(name)),
            }
        stats["runtime_seconds"] = {
            "mean": float(np.mean(runtime[name])),
            "std": float(np.std(runtime[name])),
        }
        summary[name] = stats

    return {"summary": summary, "raw": raw}


def format_summary(result):
    lines = []
    lines.append(
        f"{'policy':<18} {'survival':>9} {'contain':>9} "
        f"{'penetr.':>9} {'damage':>9} {'resources':>10} {'runtime':>9}"
    )
    lines.append("-" * 82)
    for name, s in result["summary"].items():
        lines.append(
            f"{name:<18} "
            f"{s['asset_survival_rate']['mean']:>9.3f} "
            f"{s['containment_rate']['mean']:>9.3f} "
            f"{s['penetrations']['mean']:>9.2f} "
            f"{s['cumulative_damage']['mean']:>9.3f} "
            f"{s['defenders_consumed']['mean']:>10.2f} "
            f"{s['runtime_seconds']['mean']:>9.4f}"
        )
    return "\n".join(lines)
