from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import torch

from .axplorer_v2 import (
    FitnessConditionedRuleTransformer,
    archive_training_arrays,
    canonicalize_program,
    sample_v2_programs,
    select_diverse_archive,
    train_v2_model,
)
from .hybrid_search import evaluate_hybrid_program
from .rule_program import crossover_program, mutate_program, random_program
from .scoring import EvalConfig


class HybridBudgetedOracle:
    """Budget/caching wrapper whose candidate score is measured through the optimizer."""

    def __init__(self, config: EvalConfig, budget: int, workers: int = 1):
        self.config = config
        self.budget = int(budget)
        self.workers = max(1, int(workers))
        self.evaluations = 0
        self.cache: dict[tuple[int, ...], dict] = {}
        self._executor = None

    def __enter__(self):
        if self.workers > 1:
            self._executor = ProcessPoolExecutor(
                max_workers=self.workers,
                mp_context=get_context("spawn"),
            )
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None

    @property
    def remaining(self) -> int:
        return max(0, self.budget - self.evaluations)

    def evaluate_many(self, programs) -> int:
        pending = []
        pending_keys = []
        seen_pending = set()
        for program in programs:
            canonical = canonicalize_program(program)
            key = tuple(int(x) for x in canonical)
            if key in self.cache or key in seen_pending:
                continue
            if len(pending) >= self.remaining:
                break
            seen_pending.add(key)
            pending_keys.append(key)
            pending.append(list(key))

        if not pending:
            return 0

        payloads = [(tokens, self.config) for tokens in pending]
        if self._executor is None:
            results = [_evaluate_hybrid_candidate(payload) for payload in payloads]
        else:
            results = list(self._executor.map(_evaluate_hybrid_candidate, payloads))

        for key, metrics in zip(pending_keys, results):
            self.cache[key] = metrics
        self.evaluations += len(results)
        return len(results)

    def rank(self, programs=None):
        if programs is None:
            keys = list(self.cache)
        else:
            keys = []
            seen = set()
            for program in programs:
                key = tuple(int(x) for x in canonicalize_program(program))
                if key in self.cache and key not in seen:
                    seen.add(key)
                    keys.append(key)
        ranked = [
            (float(self.cache[key]["fitness"]), np.asarray(key, dtype=np.int16), self.cache[key])
            for key in keys
        ]
        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked


def _evaluate_hybrid_candidate(payload):
    tokens, config = payload
    return evaluate_hybrid_program(np.asarray(tokens, dtype=np.int16), config)


def _seed_torch(seed: int, device: str):
    torch.manual_seed(int(seed))
    if device == "mps" and torch.backends.mps.is_available():
        torch.mps.manual_seed(int(seed))
    elif device == "cuda" and torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))


def _record(method, seed, round_index, oracle, started, archive_size=None):
    ranked = oracle.rank()
    if not ranked:
        raise RuntimeError(f"{method} has no evaluated candidates")
    _, program, metrics = ranked[0]
    row = {
        "round": int(round_index),
        "oracle_evaluations": int(oracle.evaluations),
        "fitness": float(metrics["fitness"]),
        "asset_survival_rate": float(metrics["asset_survival_rate"]),
        "containment_rate": float(metrics["containment_rate"]),
        "penetrations": float(metrics["penetrations"]),
        "cumulative_damage": float(metrics["cumulative_damage"]),
        "defenders_consumed": float(metrics["defenders_consumed"]),
        "elapsed_seconds": float(time.perf_counter() - started),
        "best_program": [int(x) for x in program],
    }
    if archive_size is not None:
        row["archive_size"] = int(archive_size)
    return row


def train_hybrid_local(
    config: EvalConfig,
    search_seed: int,
    oracle_budget: int,
    population: int,
    local_refinement_rounds: int,
    workers: int,
    verbose: bool = True,
):
    """Conventional search over strategies whose fitness is measured through the optimizer."""
    rng = np.random.default_rng(int(search_seed))
    programs = [canonicalize_program(random_program(rng)) for _ in range(int(population))]
    history = []
    started = time.perf_counter()

    with HybridBudgetedOracle(config, oracle_budget, workers=workers) as oracle:
        oracle.evaluate_many(programs)
        round_index = 0
        while oracle.remaining > 0:
            ranked = oracle.rank(programs)
            if not ranked:
                raise RuntimeError("Hybrid local search has no evaluated population")
            elite_n = max(4, min(len(ranked), max(4, population // 5)))
            elites = [p.copy() for _, p, _ in ranked[:elite_n]]
            pool = [p.copy() for _, p, _ in ranked[:population]]

            children = []
            for _ in range(int(population)):
                a = elites[int(rng.integers(0, len(elites)))]
                b = elites[int(rng.integers(0, len(elites)))]
                child = canonicalize_program(crossover_program(a, b, rng))
                child = canonicalize_program(
                    mutate_program(child, rng, n_mutations=int(rng.integers(1, 5)), radius=4)
                )
                children.append(child)

            before = oracle.evaluations
            oracle.evaluate_many(children)
            pool.extend(children)

            for _ in range(int(local_refinement_rounds)):
                if oracle.remaining <= 0:
                    break
                top = oracle.rank(pool)[:elite_n]
                neighbors = [
                    canonicalize_program(
                        mutate_program(
                            p,
                            rng,
                            n_mutations=int(rng.integers(1, 4)),
                            radius=4,
                        )
                    )
                    for _, p, _ in top
                ]
                oracle.evaluate_many(neighbors)
                pool.extend(neighbors)

            programs = [p.copy() for _, p, _ in oracle.rank(pool)[:population]]
            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [
                    canonicalize_program(random_program(rng))
                    for _ in range(min(population, oracle.remaining))
                ]
                oracle.evaluate_many(fresh)
                programs.extend(fresh)
                programs = [p.copy() for _, p, _ in oracle.rank(programs)[:population]]

            row = _record("hybrid_local", search_seed, round_index, oracle, started)
            history.append(row)
            if verbose:
                print(
                    f"[hybrid-local seed={search_seed}] round={round_index} "
                    f"evals={oracle.evaluations}/{oracle_budget} "
                    f"fitness={row['fitness']:.3f} survival={row['asset_survival_rate']:.3f}",
                    flush=True,
                )
            round_index += 1

        _, best_program, best_metrics = oracle.rank()[0]

    return {
        "method": "hybrid_local",
        "search_seed": int(search_seed),
        "best_program": [int(x) for x in best_program],
        "train_metrics": {k: float(v) for k, v in best_metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }


def train_hybrid_axplorer(
    config: EvalConfig,
    search_seed: int,
    oracle_budget: int,
    population: int,
    samples_per_round: int,
    local_refinement_rounds: int,
    train_steps: int,
    sample_temperature: float,
    weight_temperature: float,
    archive_size: int,
    workers: int,
    device: str,
    verbose: bool = True,
):
    """Axplorer V2 search where every candidate is scored through optimized execution."""
    rng = np.random.default_rng(int(search_seed))
    _seed_torch(search_seed, device)
    model = FitnessConditionedRuleTransformer().to(device)
    programs = [canonicalize_program(random_program(rng)) for _ in range(int(population))]
    history = []
    started = time.perf_counter()

    with HybridBudgetedOracle(config, oracle_budget, workers=workers) as oracle:
        oracle.evaluate_many(programs)
        round_index = 0
        while oracle.remaining > 0:
            archive = select_diverse_archive(oracle.cache, max_size=archive_size)
            train_programs, train_fitnesses = archive_training_arrays(archive)
            train_v2_model(
                model,
                train_programs,
                train_fitnesses,
                steps=train_steps,
                batch_size=min(32, len(train_programs)),
                weight_temperature=weight_temperature,
                device=device,
                seed=search_seed + round_index,
            )

            sampled = sample_v2_programs(
                model,
                min(samples_per_round, max(1, oracle.remaining)),
                temperature=sample_temperature,
                quality_level=3,
                device=device,
                seed=search_seed + 10000 + round_index,
            )
            before = oracle.evaluations
            oracle.evaluate_many(sampled)
            bases = [p for _, p, _ in oracle.rank(sampled)]

            for _ in range(int(local_refinement_rounds)):
                if oracle.remaining <= 0 or not bases:
                    break
                neighbors = [
                    canonicalize_program(
                        mutate_program(
                            p,
                            rng,
                            n_mutations=int(rng.integers(1, 4)),
                            radius=4,
                        )
                    )
                    for p in bases
                ]
                oracle.evaluate_many(neighbors)
                improved = []
                for base, neighbor in zip(bases, neighbors):
                    bkey = tuple(int(x) for x in canonicalize_program(base))
                    nkey = tuple(int(x) for x in canonicalize_program(neighbor))
                    bm = oracle.cache.get(bkey)
                    nm = oracle.cache.get(nkey)
                    if nm is not None and (bm is None or nm["fitness"] > bm["fitness"]):
                        improved.append(neighbor)
                    else:
                        improved.append(base)
                bases = improved

            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [
                    canonicalize_program(random_program(rng))
                    for _ in range(min(population, oracle.remaining))
                ]
                oracle.evaluate_many(fresh)

            row = _record(
                "hybrid_axplorer",
                search_seed,
                round_index,
                oracle,
                started,
                archive_size=len(archive),
            )
            history.append(row)
            if verbose:
                print(
                    f"[hybrid-axplorer seed={search_seed}] round={round_index} "
                    f"evals={oracle.evaluations}/{oracle_budget} archive={len(archive)} "
                    f"fitness={row['fitness']:.3f} survival={row['asset_survival_rate']:.3f}",
                    flush=True,
                )
            round_index += 1

        _, best_program, best_metrics = oracle.rank()[0]

    return {
        "method": "hybrid_axplorer",
        "search_seed": int(search_seed),
        "device": str(device),
        "best_program": [int(x) for x in best_program],
        "train_metrics": {k: float(v) for k, v in best_metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }


def save_run(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
