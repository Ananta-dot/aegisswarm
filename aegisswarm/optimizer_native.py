from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
import time

import numpy as np
from scipy.optimize import linear_sum_assignment

from .models import ThreatType
from .policies import Policy, distance_to_target
from .scenarios import ScenarioGenerator
from .scoring import EvalConfig
from .simulator import Simulator


PARAM_NAMES = (
    "urgency_weight",
    "asset_value_weight",
    "fast_weight",
    "direct_weight",
    "decoy_weight",
    "distance_weight",
    "resource_scarcity_weight",
    "reserve_threshold",
    "stickiness_weight",
    "speed_weight",
)
OBJECTIVE_DIM = len(PARAM_NAMES)

LOWER_BOUNDS = np.asarray([0.0, 0.0, -1.0, -1.0, -4.0, 0.0, 0.0, 0.0, 0.0, 0.0])
UPPER_BOUNDS = np.asarray([8.0, 4.0, 4.0, 4.0, 1.0, 4.0, 4.0, 0.8, 4.0, 4.0])

# A hand-written starting point only. Search is free to move anywhere inside the
# abstract bounds. This is not intended to encode real-world doctrine.
DEFAULT_NATIVE_OBJECTIVE = np.asarray(
    [3.0, 1.0, 1.0, 0.8, -1.5, 1.5, 1.0, 0.20, 0.5, 0.5],
    dtype=float,
)


def canonicalize_objective(vector) -> np.ndarray:
    arr = np.asarray(vector, dtype=float)
    if arr.shape != (OBJECTIVE_DIM,):
        raise ValueError(f"Expected objective shape {(OBJECTIVE_DIM,)}, got {arr.shape}")
    return np.round(np.clip(arr, LOWER_BOUNDS, UPPER_BOUNDS), 4)


def random_objective(rng: np.random.Generator) -> np.ndarray:
    return canonicalize_objective(rng.uniform(LOWER_BOUNDS, UPPER_BOUNDS))


def mutate_objective(vector, rng: np.random.Generator, scale: float = 0.12) -> np.ndarray:
    base = canonicalize_objective(vector)
    width = UPPER_BOUNDS - LOWER_BOUNDS
    mask = rng.random(OBJECTIVE_DIM) < 0.45
    if not np.any(mask):
        mask[int(rng.integers(0, OBJECTIVE_DIM))] = True
    noise = rng.normal(0.0, float(scale), size=OBJECTIVE_DIM) * width
    out = base.copy()
    out[mask] += noise[mask]
    return canonicalize_objective(out)


def crossover_objective(a, b, rng: np.random.Generator) -> np.ndarray:
    a = canonicalize_objective(a)
    b = canonicalize_objective(b)
    alpha = rng.uniform(0.0, 1.0, size=OBJECTIVE_DIM)
    child = alpha * a + (1.0 - alpha) * b
    return canonicalize_objective(child)


class OptimizerNativePolicy(Policy):
    """Compact strategic objective + exact per-step assignment.

    The vector controls abstract utility terms. Feasibility and one-to-one
    assignment remain the responsibility of the Hungarian optimizer.
    """

    name = "optimizer_native"

    def __init__(self, vector, name="optimizer_native"):
        self.vector = canonicalize_objective(vector)
        self.name = name

    def _pair_utility(self, scenario, defender, threat):
        d_def = threat.distance_to(defender.x, defender.y)
        if d_def > defender.range:
            return None

        asset = next(a for a in scenario.assets if a.id == threat.target_asset_id)
        d_asset = distance_to_target(scenario, threat)

        urgency = 1.0 - min(d_asset / max(scenario.world_size, 1.0), 1.0)
        max_asset_value = max((a.value for a in scenario.assets), default=1.0)
        asset_value = asset.value / max(max_asset_value, 1e-9)
        distance_closeness = 1.0 - min(d_def / max(defender.range, 1e-9), 1.0)

        initial_total = float(scenario.metadata.get("initial_defender_uses", 0.0))
        if initial_total > 0.0:
            initial_per_defender = initial_total / max(len(scenario.defenders), 1)
        else:
            initial_per_defender = max(float(defender.remaining_uses), 1.0)
        resource_fraction = float(
            np.clip(defender.remaining_uses / max(initial_per_defender, 1e-9), 0.0, 1.0)
        )
        scarcity = 1.0 - resource_fraction

        max_speed = max((th.speed for th in scenario.threats if th.active), default=1.0)
        speed = threat.speed / max(max_speed, 1e-9)
        sticky = 1.0 if defender.assigned_threat_id == threat.id else 0.0

        (
            w_urgency,
            w_asset,
            w_fast,
            w_direct,
            w_decoy,
            w_distance,
            w_scarcity,
            reserve_threshold,
            w_sticky,
            w_speed,
        ) = self.vector

        # Reserve is a strategic gate, not a feasibility constraint. Urgent
        # threats can still release reserved capacity automatically.
        if resource_fraction <= reserve_threshold and urgency < 0.75:
            return None

        type_term = 0.0
        if threat.threat_type == ThreatType.FAST:
            type_term = w_fast
        elif threat.threat_type == ThreatType.DIRECT:
            type_term = w_direct
        elif threat.threat_type == ThreatType.DECOY:
            type_term = w_decoy

        utility = (
            w_urgency * urgency
            + w_asset * asset_value
            + type_term
            + w_distance * distance_closeness
            - w_scarcity * scarcity
            + w_sticky * sticky
            + w_speed * speed
        )
        return float(utility)

    def assign(self, scenario, t):
        defenders = [
            d for d in scenario.defenders if d.available and d.remaining_uses > 0
        ]
        threats = [th for th in scenario.threats if th.active and th.detected]
        out = {d.id: None for d in scenario.defenders}
        if not defenders or not threats:
            return out

        n_d = len(defenders)
        n_t = len(threats)
        utility = np.zeros((n_d, n_t + n_d), dtype=float)
        utility[:, :n_t] = -1e9

        for i, defender in enumerate(defenders):
            for j, threat in enumerate(threats):
                value = self._pair_utility(scenario, defender, threat)
                if value is not None:
                    utility[i, j] = value

        row_ind, col_ind = linear_sum_assignment(-utility)
        for i, j in zip(row_ind, col_ind):
            if j >= n_t or utility[i, j] <= 0.0:
                continue
            out[defenders[i].id] = threats[j].id
        return out


def evaluate_native_objective(vector, config: EvalConfig):
    vector = canonicalize_objective(vector)
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
        rows.append(Simulator.evaluate_policy(scenario, OptimizerNativePolicy(vector)).as_dict())

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
    return {
        "fitness": float(max(0.0, 200.0 - loss)),
        "loss": float(loss),
        "asset_survival_rate": survival,
        "containment_rate": containment,
        "penetrations": penetrations,
        "cumulative_damage": damage,
        "defenders_consumed": resources,
        "mean_response_delay": response,
    }


def _native_eval_worker(payload):
    vector, config = payload
    return evaluate_native_objective(np.asarray(vector, dtype=float), config)


class NativeBudgetedOracle:
    def __init__(self, config: EvalConfig, budget: int, workers: int = 1):
        self.config = config
        self.budget = int(budget)
        self.workers = max(1, int(workers))
        self.evaluations = 0
        self.cache: dict[tuple[float, ...], dict] = {}
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
    def remaining(self):
        return max(0, self.budget - self.evaluations)

    def evaluate_many(self, vectors):
        pending = []
        keys = []
        seen = set()
        for vector in vectors:
            canonical = canonicalize_objective(vector)
            key = tuple(float(x) for x in canonical)
            if key in self.cache or key in seen:
                continue
            if len(pending) >= self.remaining:
                break
            seen.add(key)
            keys.append(key)
            pending.append((canonical.tolist(), self.config))
        if not pending:
            return 0

        if self._executor is None:
            results = [_native_eval_worker(payload) for payload in pending]
        else:
            results = list(self._executor.map(_native_eval_worker, pending))
        for key, metrics in zip(keys, results):
            self.cache[key] = metrics
        self.evaluations += len(results)
        return len(results)

    def rank(self, vectors=None):
        if vectors is None:
            keys = list(self.cache)
        else:
            keys = []
            seen = set()
            for vector in vectors:
                key = tuple(float(x) for x in canonicalize_objective(vector))
                if key in self.cache and key not in seen:
                    seen.add(key)
                    keys.append(key)
        ranked = [
            (float(self.cache[key]["fitness"]), np.asarray(key, dtype=float), self.cache[key])
            for key in keys
        ]
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked


def train_native_local(
    config: EvalConfig,
    search_seed: int,
    oracle_budget: int,
    population: int,
    local_refinement_rounds: int,
    workers: int,
    verbose: bool = True,
):
    rng = np.random.default_rng(int(search_seed))
    population = int(population)
    vectors = [DEFAULT_NATIVE_OBJECTIVE.copy()]
    vectors += [random_objective(rng) for _ in range(max(0, population - 1))]
    started = time.perf_counter()
    history = []

    with NativeBudgetedOracle(config, oracle_budget, workers=workers) as oracle:
        oracle.evaluate_many(vectors)
        round_index = 0
        while oracle.remaining > 0:
            ranked = oracle.rank(vectors)
            if not ranked:
                raise RuntimeError("Native objective search has no evaluated population")
            elite_n = max(4, min(len(ranked), max(4, population // 5)))
            elites = [v.copy() for _, v, _ in ranked[:elite_n]]
            pool = [v.copy() for _, v, _ in ranked[:population]]

            children = []
            for _ in range(population):
                a = elites[int(rng.integers(0, len(elites)))]
                b = elites[int(rng.integers(0, len(elites)))]
                child = crossover_objective(a, b, rng)
                children.append(mutate_objective(child, rng, scale=0.12))
            before = oracle.evaluations
            oracle.evaluate_many(children)
            pool.extend(children)

            for _ in range(int(local_refinement_rounds)):
                if oracle.remaining <= 0:
                    break
                top = oracle.rank(pool)[:elite_n]
                neighbors = [mutate_objective(v, rng, scale=0.06) for _, v, _ in top]
                oracle.evaluate_many(neighbors)
                pool.extend(neighbors)

            vectors = [v.copy() for _, v, _ in oracle.rank(pool)[:population]]
            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [random_objective(rng) for _ in range(min(population, oracle.remaining))]
                oracle.evaluate_many(fresh)
                vectors.extend(fresh)
                vectors = [v.copy() for _, v, _ in oracle.rank(vectors)[:population]]

            _, best, metrics = oracle.rank()[0]
            row = {
                "round": int(round_index),
                "oracle_evaluations": int(oracle.evaluations),
                "fitness": float(metrics["fitness"]),
                "asset_survival_rate": float(metrics["asset_survival_rate"]),
                "containment_rate": float(metrics["containment_rate"]),
                "penetrations": float(metrics["penetrations"]),
                "best_objective": [float(x) for x in best],
                "elapsed_seconds": float(time.perf_counter() - started),
            }
            history.append(row)
            if verbose:
                print(
                    f"[native-local seed={search_seed}] round={round_index} "
                    f"evals={oracle.evaluations}/{oracle_budget} "
                    f"fitness={row['fitness']:.3f} survival={row['asset_survival_rate']:.3f}",
                    flush=True,
                )
            round_index += 1

        _, best, metrics = oracle.rank()[0]

    return {
        "method": "optimizer_native_local",
        "search_seed": int(search_seed),
        "best_objective": [float(x) for x in best],
        "parameter_names": list(PARAM_NAMES),
        "train_metrics": {k: float(v) for k, v in metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }
