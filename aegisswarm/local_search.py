from __future__ import annotations

import numpy as np

from .strategy import mutate_genome
from .scoring import evaluate_genome, EvalConfig


def hill_climb(genes, config: EvalConfig, trials: int = 8, seed: int | None = None):
    base = np.asarray(genes, dtype=np.int16).copy()
    if seed is None:
        seed = int(sum((i + 1) * int(v) for i, v in enumerate(base)) + 17)
    rng = np.random.default_rng(seed)

    best = base
    best_metrics = evaluate_genome(best, config)

    for _ in range(int(trials)):
        candidate = mutate_genome(best, rng, n_mutations=1, radius=3)
        metrics = evaluate_genome(candidate, config)
        if metrics["fitness"] > best_metrics["fitness"]:
            best = candidate
            best_metrics = metrics

    return best, best_metrics


def evolutionary_search(
    config: EvalConfig,
    seed: int = 0,
    population: int = 64,
    generations: int = 10,
    elite_fraction: float = 0.20,
):
    from .strategy import random_genome

    rng = np.random.default_rng(seed)
    genomes = [random_genome(rng) for _ in range(population)]
    history = []

    for generation in range(generations):
        scored = [(evaluate_genome(g, config)["fitness"], g) for g in genomes]
        scored.sort(key=lambda x: x[0], reverse=True)
        elite_n = max(2, int(population * elite_fraction))
        elites = [g.copy() for _, g in scored[:elite_n]]

        improved = []
        for g in elites:
            ig, im = hill_climb(g, config, trials=4)
            improved.append((im["fitness"], ig))

        merged = scored + improved
        merged.sort(key=lambda x: x[0], reverse=True)
        best_fitness, best_genome = merged[0]
        best_metrics = evaluate_genome(best_genome, config)

        history.append({
            "generation": generation,
            "best_fitness": float(best_fitness),
            "best_genome": [int(x) for x in best_genome],
            **{k: float(v) for k, v in best_metrics.items()},
        })

        parents = [g for _, g in merged[:elite_n]]
        next_gen = [g.copy() for g in parents]
        while len(next_gen) < population:
            p = parents[int(rng.integers(0, len(parents)))]
            child = mutate_genome(
                p,
                rng,
                n_mutations=int(rng.integers(1, 3)),
                radius=3,
            )
            next_gen.append(child)
        genomes = next_gen[:population]

    return history[-1], history
