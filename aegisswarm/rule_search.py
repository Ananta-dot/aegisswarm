from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .scoring import EvalConfig
from .rule_program import RuleProgramPolicy, random_program, mutate_program, crossover_program


def evaluate_rule_program(tokens, config: EvalConfig):
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
                RuleProgramPolicy(tokens),
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


def hill_climb_rule_program(tokens, config: EvalConfig, trials=12, seed=0):
    rng = np.random.default_rng(seed)
    best = np.asarray(tokens, dtype=np.int16).copy()
    best_metrics = evaluate_rule_program(best, config)

    for _ in range(int(trials)):
        candidate = mutate_program(
            best,
            rng,
            n_mutations=int(rng.integers(1, 4)),
            radius=4,
        )
        metrics = evaluate_rule_program(candidate, config)
        if metrics["fitness"] > best_metrics["fitness"]:
            best = candidate
            best_metrics = metrics
    return best, best_metrics


def evolutionary_rule_search(
    config: EvalConfig,
    seed=0,
    population=96,
    generations=12,
    elite_fraction=0.20,
    local_trials=6,
):
    rng = np.random.default_rng(seed)
    programs = [random_program(rng) for _ in range(int(population))]
    history = []

    for generation in range(int(generations)):
        scored = [(evaluate_rule_program(p, config)["fitness"], p) for p in programs]
        scored.sort(key=lambda x: x[0], reverse=True)
        elite_n = max(4, int(population * elite_fraction))
        elites = [p.copy() for _, p in scored[:elite_n]]

        improved = []
        for i, p in enumerate(elites):
            ip, im = hill_climb_rule_program(
                p,
                config,
                trials=local_trials,
                seed=seed + generation * 10000 + i,
            )
            improved.append((im["fitness"], ip))

        merged = scored + improved
        merged.sort(key=lambda x: x[0], reverse=True)
        best_fitness, best_program = merged[0]
        best_metrics = evaluate_rule_program(best_program, config)
        history.append({
            "generation": generation,
            "best_fitness": float(best_fitness),
            "best_program": [int(x) for x in best_program],
            **{k: float(v) for k, v in best_metrics.items()},
        })

        parents = [p for _, p in merged[:elite_n]]
        next_gen = [p.copy() for p in parents]
        while len(next_gen) < population:
            a = parents[int(rng.integers(0, len(parents)))]
            b = parents[int(rng.integers(0, len(parents)))]
            child = crossover_program(a, b, rng)
            child = mutate_program(child, rng, n_mutations=int(rng.integers(1, 5)))
            next_gen.append(child)
        programs = next_gen[:population]

    return history[-1], history


def save_rule_result(best, history, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"best": best, "history": history}, indent=2))


def load_best_program(path):
    data = json.loads(Path(path).read_text())
    key = "best_program"
    return np.asarray(data["best"][key], dtype=np.int16)
