from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
import torch

from .archive import PolicyArchive
from .axplorer_lite import GenomeTransformer, device_auto, sample_genomes, train_model, unique_genomes
from .scoring_v2 import EvalConfigV2, evaluate_genome_v2
from .strategy_v2 import (
    GENOME_V2_LENGTH,
    decode_genome_v2,
    mutate_genome_v2,
    random_genome_v2,
)


class EvaluationCache:
    """Memoize deterministic genome evaluations for one fixed EvalConfigV2."""

    def __init__(self, config: EvalConfigV2):
        self.config = config
        self.data: dict[tuple[int, ...], dict] = {}
        self.calls = 0
        self.hits = 0

    def evaluate(self, genes):
        key = tuple(int(x) for x in genes)
        if key in self.data:
            self.hits += 1
            return self.data[key]
        self.calls += 1
        metrics = evaluate_genome_v2(genes, self.config)
        self.data[key] = metrics
        return metrics


def hill_climb_v2(genes, evaluator, trials: int = 8, seed: int | None = None):
    base = np.asarray(genes, dtype=np.int16).copy()
    if seed is None:
        seed = int(sum((i + 1) * int(v) for i, v in enumerate(base)) + 29)
    rng = np.random.default_rng(seed)
    best = base
    best_metrics = evaluator.evaluate(best)

    for _ in range(int(trials)):
        candidate = mutate_genome_v2(best, rng, n_mutations=1, radius=3)
        metrics = evaluator.evaluate(candidate)
        if metrics["fitness"] > best_metrics["fitness"]:
            best = candidate
            best_metrics = metrics

    return best, best_metrics


def _rank(genomes, evaluator):
    scored = [(evaluator.evaluate(g), g) for g in genomes]
    scored.sort(key=lambda x: x[0]["fitness"], reverse=True)
    return scored


def train_policy_search_v2(
    screen_config: EvalConfigV2,
    train_config: EvalConfigV2,
    validation_config: EvalConfigV2,
    seed: int = 123,
    epochs: int = 20,
    population: int = 256,
    samples_per_epoch: int = 256,
    train_steps: int = 500,
    elite_fraction: float = 0.25,
    promotion_fraction: float = 0.50,
    validation_candidates: int = 12,
    local_search_trials: int = 4,
    archive_size: int = 32,
    temperature: float = 0.8,
    device: str | None = None,
):
    """Search adaptive policies with progressively more expensive evaluation.

    Candidate generation and local refinement use training seeds only. A small
    screen set eliminates weak proposals, a larger training set ranks survivors,
    and validation seeds are used only to rank the persistent hall of fame.
    Test seeds are deliberately absent from this function.
    """

    rng = np.random.default_rng(seed)
    device = device or device_auto()
    model = GenomeTransformer(max_genome_length=GENOME_V2_LENGTH).to(device)
    archive = PolicyArchive(max_size=archive_size)
    population_data = [random_genome_v2(rng) for _ in range(population)]
    history = []

    screen_eval = EvaluationCache(screen_config)
    train_eval = EvaluationCache(train_config)
    validation_eval = EvaluationCache(validation_config)

    for epoch in range(int(epochs)):
        screen_ranked = _rank(population_data, screen_eval)
        elite_n = max(8, int(population * elite_fraction))
        promote_n = max(elite_n, int(population * promotion_fraction))
        promoted = [g.copy() for _, g in screen_ranked[:promote_n]]

        train_ranked = _rank(promoted, train_eval)
        elites = [g.copy() for _, g in train_ranked[:elite_n]]

        train_model(
            model,
            elites,
            steps=train_steps,
            batch_size=min(32, len(elites)),
            device=device,
            seed=seed + epoch,
        )

        sampled = sample_genomes(
            model,
            samples_per_epoch,
            temperature=temperature,
            device=device,
            seed=seed + 10_000 + epoch,
            genome_length=GENOME_V2_LENGTH,
        )

        improved = []
        for i, genome in enumerate(sampled):
            candidate, _ = hill_climb_v2(
                genome,
                screen_eval,
                trials=local_search_trials,
                seed=seed + epoch * 100_000 + i,
            )
            improved.append(candidate)

        archive_genomes = [np.asarray(e["genes"], dtype=np.int16) for e in archive.ranked()]
        candidates = unique_genomes(elites + sampled + improved + archive_genomes)

        candidate_screen = _rank(candidates, screen_eval)
        candidate_promote_n = max(elite_n, int(len(candidate_screen) * promotion_fraction))
        candidate_promote_n = min(max(candidate_promote_n, population // 2), len(candidate_screen))
        train_candidates = [g for _, g in candidate_screen[:candidate_promote_n]]
        candidate_train = _rank(train_candidates, train_eval)

        val_n = min(max(1, int(validation_candidates)), len(candidate_train))
        for train_metrics, genome in candidate_train[:val_n]:
            validation_metrics = validation_eval.evaluate(genome)
            archive.add(
                genome,
                train_metrics=train_metrics,
                validation_metrics=validation_metrics,
                source="axplorer_v2",
                epoch=epoch,
            )

        next_population = []
        seen = set()
        for _metrics, genome in candidate_train:
            key = tuple(int(x) for x in genome)
            if key not in seen:
                next_population.append(genome.copy())
                seen.add(key)
            if len(next_population) >= population:
                break
        for entry in archive.ranked():
            genome = np.asarray(entry["genes"], dtype=np.int16)
            key = tuple(int(x) for x in genome)
            if key not in seen and len(next_population) < population:
                next_population.append(genome)
                seen.add(key)
        while len(next_population) < population:
            next_population.append(random_genome_v2(rng))
        population_data = next_population[:population]

        champion = archive.best
        history.append({
            "epoch": int(epoch),
            "device": device,
            "screen_candidates": len(candidate_screen),
            "full_train_candidates": len(candidate_train),
            "validation_candidates": val_n,
            "best_genome": champion["genes"],
            "train_fitness": champion["train"]["fitness"],
            "validation_fitness": champion["validation"]["fitness"],
            "validation_asset_survival_rate": champion["validation"]["asset_survival_rate"],
            "validation_containment_rate": champion["validation"]["containment_rate"],
            "cache": {
                "screen_unique": screen_eval.calls,
                "screen_hits": screen_eval.hits,
                "train_unique": train_eval.calls,
                "train_hits": train_eval.hits,
                "validation_unique": validation_eval.calls,
                "validation_hits": validation_eval.hits,
            },
        })

    return archive.best, history, model, archive


def save_policy_search_v2(best, history, archive: PolicyArchive, path, model=None, metadata=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 2,
        "selection_metric": "validation.fitness",
        "best": best,
        "best_decoded": asdict(decode_genome_v2(best["genes"])) if best else None,
        "history": history,
        "archive": archive.as_dict(),
        "metadata": metadata or {},
    }
    path.write_text(json.dumps(payload, indent=2))
    if model is not None:
        torch.save(model.state_dict(), path.with_suffix(".pt"))


def load_best_genome_v2(path):
    data = json.loads(Path(path).read_text())
    genes = data["best"]["genes"]
    return np.asarray(genes, dtype=np.int16)
