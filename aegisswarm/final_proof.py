from __future__ import annotations

import csv
import itertools
import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np
import torch

from .benchmark import evaluate_policies
from .rl import load_qtable, save_qtable, train_q_learning
from .rule_axplorer import (
    RuleProgramTransformer,
    device_auto,
    sample_programs,
    train_model,
)
from .rule_program import (
    RuleProgramPolicy,
    crossover_program,
    mutate_program,
    random_program,
)
from .rule_search import evaluate_rule_program
from .scenarios import ScenarioGenerator
from .scoring import EvalConfig
from .simulator import Simulator
from .splits import FINAL_HOLDOUT_SEEDS, TRAIN_SEEDS, VALIDATION_SEEDS
from .stress import STRESS_FAMILIES
from .axplorer_lite import load_best_genome


PROTOCOL_ID = "aegisswarm-final-v1"
FORMAL_SEARCH_SEEDS = (41001, 41002, 41003, 41004, 41005)
FORMAL_TRAIN_SCENARIOS = 16
FORMAL_ORACLE_BUDGET = 1800
FORMAL_POPULATION = 64
FORMAL_LOCAL_REFINEMENT_ROUNDS = 2
FORMAL_AXPLORER_TRAIN_STEPS = 200
FORMAL_AXPLORER_SAMPLES = 64
FORMAL_AXPLORER_TEMPERATURE = 0.9
FORMAL_STRESS_EPISODES = 200

QUICK_SEARCH_SEEDS = (91001, 91002)
QUICK_TRAIN_SCENARIOS = 4
QUICK_ORACLE_BUDGET = 96
QUICK_POPULATION = 16
QUICK_LOCAL_REFINEMENT_ROUNDS = 1
QUICK_AXPLORER_TRAIN_STEPS = 8
QUICK_AXPLORER_SAMPLES = 16
QUICK_VALIDATION_SEEDS = tuple(VALIDATION_SEEDS[-20:])
QUICK_STRESS_EPISODES = 8

METRICS = (
    "asset_survival_rate",
    "containment_rate",
    "penetrations",
    "cumulative_damage",
    "defenders_consumed",
    "mean_response_delay",
)

# +1 means larger is better, -1 means smaller is better.
METRIC_DIRECTION = {
    "asset_survival_rate": 1.0,
    "containment_rate": 1.0,
    "penetrations": -1.0,
    "cumulative_damage": -1.0,
    "defenders_consumed": -1.0,
    "mean_response_delay": -1.0,
}


def _program_key(program) -> tuple[int, ...]:
    return tuple(int(x) for x in np.asarray(program, dtype=np.int16))


def _unique_programs(programs):
    seen = set()
    out = []
    for program in programs:
        key = _program_key(program)
        if key in seen:
            continue
        seen.add(key)
        out.append(np.asarray(program, dtype=np.int16).copy())
    return out


def _evaluate_program_worker(tokens, config: EvalConfig):
    return evaluate_rule_program(np.asarray(tokens, dtype=np.int16), config)


class BudgetedRuleOracle:
    """Count and cache unique full-program evaluations.

    Both structured local search and structured Axplorer receive the same oracle
    budget. One oracle evaluation scores one candidate policy over the same fixed
    training-scenario bundle.
    """

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
            key = _program_key(program)
            if key in self.cache or key in seen_pending:
                continue
            if len(pending) >= self.remaining:
                break
            seen_pending.add(key)
            pending_keys.append(key)
            pending.append(list(key))

        if not pending:
            return 0

        if self._executor is None:
            results = [
                _evaluate_program_worker(tokens, self.config)
                for tokens in pending
            ]
        else:
            results = list(
                self._executor.map(
                    _evaluate_program_worker,
                    pending,
                    itertools.repeat(self.config),
                )
            )

        for key, metrics in zip(pending_keys, results):
            self.cache[key] = metrics
        self.evaluations += len(results)
        return len(results)

    def rank(self, programs):
        ranked = []
        for program in _unique_programs(programs):
            metrics = self.cache.get(_program_key(program))
            if metrics is not None:
                ranked.append((float(metrics["fitness"]), program, metrics))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked


def _search_record(round_index, oracle, ranked, elapsed, device=None):
    if not ranked:
        return None
    _, program, metrics = ranked[0]
    row = {
        "round": int(round_index),
        "oracle_evaluations": int(oracle.evaluations),
        "elapsed_seconds": float(elapsed),
        "best_program": [int(x) for x in program],
    }
    if device is not None:
        row["device"] = str(device)
    row.update({k: float(v) for k, v in metrics.items()})
    return row


def train_budgeted_local(
    config: EvalConfig,
    search_seed: int,
    oracle_budget: int,
    population: int,
    local_refinement_rounds: int,
    workers: int,
    verbose: bool = True,
):
    rng = np.random.default_rng(search_seed)
    programs = [random_program(rng) for _ in range(population)]
    history = []
    started = time.perf_counter()

    with BudgetedRuleOracle(config, oracle_budget, workers=workers) as oracle:
        oracle.evaluate_many(programs)
        round_index = 0

        while oracle.remaining > 0:
            ranked = oracle.rank(programs)
            if not ranked:
                raise RuntimeError("Local search has no evaluated population.")

            elite_n = max(4, min(len(ranked), population // 5))
            elites = [p.copy() for _, p, _ in ranked[:elite_n]]
            pool = [p.copy() for _, p, _ in ranked[:population]]

            children = []
            for _ in range(population):
                a = elites[int(rng.integers(0, len(elites)))]
                b = elites[int(rng.integers(0, len(elites)))]
                child = crossover_program(a, b, rng)
                child = mutate_program(
                    child,
                    rng,
                    n_mutations=int(rng.integers(1, 5)),
                    radius=4,
                )
                children.append(child)

            before = oracle.evaluations
            oracle.evaluate_many(children)
            pool.extend(children)

            for _ in range(local_refinement_rounds):
                if oracle.remaining <= 0:
                    break
                top = oracle.rank(pool)[:elite_n]
                neighbors = [
                    mutate_program(
                        p,
                        rng,
                        n_mutations=int(rng.integers(1, 4)),
                        radius=4,
                    )
                    for _, p, _ in top
                ]
                oracle.evaluate_many(neighbors)
                pool.extend(neighbors)

            ranked_pool = oracle.rank(pool)
            programs = [p.copy() for _, p, _ in ranked_pool[:population]]

            # Extremely unlikely duplicate-only rounds should not strand budget.
            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [
                    random_program(rng)
                    for _ in range(min(population, oracle.remaining))
                ]
                oracle.evaluate_many(fresh)
                programs.extend(fresh)
                programs = [
                    p.copy()
                    for _, p, _ in oracle.rank(programs)[:population]
                ]

            row = _search_record(
                round_index,
                oracle,
                oracle.rank(programs),
                time.perf_counter() - started,
            )
            if row is not None:
                history.append(row)
                if verbose:
                    print(
                        f"[local seed={search_seed}] round={round_index} "
                        f"evals={oracle.evaluations}/{oracle_budget} "
                        f"fitness={row['fitness']:.3f} "
                        f"survival={row['asset_survival_rate']:.3f}",
                        flush=True,
                    )
            round_index += 1

        final_ranked = oracle.rank(programs)
        if not final_ranked:
            raise RuntimeError("Local search finished without a valid program.")
        _, best_program, best_metrics = final_ranked[0]

    return {
        "method": "rule_local",
        "search_seed": int(search_seed),
        "best_program": [int(x) for x in best_program],
        "train_metrics": {k: float(v) for k, v in best_metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }


def _seed_torch(seed: int, device: str):
    torch.manual_seed(int(seed))
    if device == "mps" and torch.backends.mps.is_available():
        torch.mps.manual_seed(int(seed))
    elif device == "cuda" and torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))


def train_budgeted_axplorer(
    config: EvalConfig,
    search_seed: int,
    oracle_budget: int,
    population: int,
    samples_per_round: int,
    train_steps: int,
    local_refinement_rounds: int,
    temperature: float,
    workers: int,
    device: str | None = None,
    verbose: bool = True,
):
    rng = np.random.default_rng(search_seed)
    device = device or device_auto()
    _seed_torch(search_seed, device)

    model = RuleProgramTransformer().to(device)
    programs = [random_program(rng) for _ in range(population)]
    history = []
    started = time.perf_counter()

    with BudgetedRuleOracle(config, oracle_budget, workers=workers) as oracle:
        oracle.evaluate_many(programs)
        round_index = 0

        while oracle.remaining > 0:
            ranked = oracle.rank(programs)
            if not ranked:
                raise RuntimeError("Axplorer search has no evaluated population.")

            elite_n = max(8, min(len(ranked), population // 4))
            elites = [p.copy() for _, p, _ in ranked[:elite_n]]

            train_model(
                model,
                elites,
                steps=train_steps,
                batch_size=min(32, elite_n),
                device=device,
                seed=search_seed + round_index,
            )

            sampled = sample_programs(
                model,
                min(samples_per_round, max(1, oracle.remaining)),
                temperature=temperature,
                device=device,
                seed=search_seed + 10000 + round_index,
            )

            before = oracle.evaluations
            oracle.evaluate_many(sampled)
            pool = [p.copy() for _, p, _ in ranked[:population]] + sampled

            bases = [p for _, p, _ in oracle.rank(sampled)]
            for _ in range(local_refinement_rounds):
                if oracle.remaining <= 0 or not bases:
                    break
                neighbors = [
                    mutate_program(
                        p,
                        rng,
                        n_mutations=int(rng.integers(1, 4)),
                        radius=4,
                    )
                    for p in bases
                ]
                oracle.evaluate_many(neighbors)

                improved_bases = []
                for base, neighbor in zip(bases, neighbors):
                    bm = oracle.cache.get(_program_key(base))
                    nm = oracle.cache.get(_program_key(neighbor))
                    if nm is not None and (
                        bm is None or nm["fitness"] > bm["fitness"]
                    ):
                        improved_bases.append(neighbor)
                    else:
                        improved_bases.append(base)
                bases = improved_bases
                pool.extend(neighbors)

            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [
                    random_program(rng)
                    for _ in range(min(population, oracle.remaining))
                ]
                oracle.evaluate_many(fresh)
                pool.extend(fresh)

            ranked_pool = oracle.rank(pool)
            programs = [p.copy() for _, p, _ in ranked_pool[:population]]
            while len(programs) < population:
                programs.append(random_program(rng))
                if oracle.remaining > 0:
                    oracle.evaluate_many(programs[-1:])

            row = _search_record(
                round_index,
                oracle,
                oracle.rank(programs),
                time.perf_counter() - started,
                device=device,
            )
            if row is not None:
                history.append(row)
                if verbose:
                    print(
                        f"[axplorer seed={search_seed}] round={round_index} "
                        f"evals={oracle.evaluations}/{oracle_budget} "
                        f"fitness={row['fitness']:.3f} "
                        f"survival={row['asset_survival_rate']:.3f}",
                        flush=True,
                    )
            round_index += 1

        final_ranked = oracle.rank(programs)
        if not final_ranked:
            raise RuntimeError("Axplorer search finished without a valid program.")
        _, best_program, best_metrics = final_ranked[0]

    # The discovered rule program is the deployable/evaluable artifact. Model
    # weights are not required for final policy evaluation.
    return {
        "method": "rule_axplorer",
        "search_seed": int(search_seed),
        "device": str(device),
        "best_program": [int(x) for x in best_program],
        "train_metrics": {k: float(v) for k, v in best_metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _load_or_train(
    method: str,
    search_seed: int,
    run_path: Path,
    train_fn,
    force: bool,
    **kwargs,
):
    if run_path.exists() and not force:
        data = json.loads(run_path.read_text())
        if data.get("method") == method and int(data.get("search_seed", -1)) == int(search_seed):
            print(f"[resume] {method} seed={search_seed}: {run_path}", flush=True)
            return data

    data = train_fn(search_seed=search_seed, **kwargs)
    _save_json(run_path, data)
    return data


def _evaluate_program_on_seeds(program, seeds, scenario_kwargs):
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.get("max_steps", 150)))
    kwargs = dict(scenario_kwargs)
    kwargs.pop("max_steps", None)
    rows = []
    runtimes = []

    for seed in seeds:
        scenario = gen.generate(seed=int(seed), **kwargs)
        started = time.perf_counter()
        metrics = Simulator.evaluate_policy(
            scenario,
            RuleProgramPolicy(program),
        )
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())

    return {
        "rows": rows,
        "runtime_mean": float(np.mean(runtimes)) if runtimes else 0.0,
    }


def _evaluate_program_worker(payload):
    program, seeds, scenario_kwargs = payload
    return _evaluate_program_on_seeds(program, seeds, scenario_kwargs)


def evaluate_program_runs(programs, seeds, scenario_kwargs, workers=1):
    payloads = [
        ([int(x) for x in program], [int(s) for s in seeds], dict(scenario_kwargs))
        for program in programs
    ]

    if workers <= 1 or len(payloads) <= 1:
        results = [_evaluate_program_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=min(int(workers), len(payloads)),
            mp_context=get_context("spawn"),
        ) as executor:
            results = list(executor.map(_evaluate_program_worker, payloads))

    matrices = {}
    for metric in METRICS:
        matrices[metric] = np.asarray(
            [[float(row[metric]) for row in result["rows"]] for result in results],
            dtype=float,
        )

    return {
        "matrices": matrices,
        "runtime_by_run": [float(result["runtime_mean"]) for result in results],
        "raw_by_run": [result["rows"] for result in results],
    }


def hierarchical_bootstrap_ci(matrix, seed=12345, n_boot=5000, alpha=0.05):
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.size == 0:
        return [float("nan"), float("nan")]

    rng = np.random.default_rng(seed)
    n_runs, n_scenarios = matrix.shape
    draws = np.empty(n_boot, dtype=float)

    for i in range(n_boot):
        r = rng.integers(0, n_runs, size=n_runs)
        s = rng.integers(0, n_scenarios, size=n_scenarios)
        draws[i] = float(matrix[np.ix_(r, s)].mean())

    return [
        float(np.quantile(draws, alpha / 2)),
        float(np.quantile(draws, 1.0 - alpha / 2)),
    ]


def paired_hierarchical_bootstrap(
    local_matrix,
    axplorer_matrix,
    metric,
    seed=54321,
    n_boot=5000,
    alpha=0.05,
):
    local_matrix = np.asarray(local_matrix, dtype=float)
    axplorer_matrix = np.asarray(axplorer_matrix, dtype=float)
    if local_matrix.shape != axplorer_matrix.shape:
        raise ValueError("Paired matrices must have identical shape.")

    direction = METRIC_DIRECTION[metric]
    diff = axplorer_matrix - local_matrix
    rng = np.random.default_rng(seed)
    n_runs, n_scenarios = diff.shape
    draws = np.empty(n_boot, dtype=float)

    for i in range(n_boot):
        r = rng.integers(0, n_runs, size=n_runs)
        s = rng.integers(0, n_scenarios, size=n_scenarios)
        draws[i] = float(diff[np.ix_(r, s)].mean())

    return {
        "axplorer_minus_local": float(diff.mean()),
        "ci95": [
            float(np.quantile(draws, alpha / 2)),
            float(np.quantile(draws, 1.0 - alpha / 2)),
        ],
        "probability_axplorer_better": float(np.mean(direction * draws > 0.0)),
        "paired_training_run_win_rate": float(
            np.mean(direction * diff.mean(axis=1) > 0.0)
        ),
        "paired_scenario_win_rate": float(
            np.mean(direction * diff.mean(axis=0) > 0.0)
        ),
    }


def paired_sign_flip_pvalue(local_matrix, axplorer_matrix, seed=777, n_perm=20000):
    """Two-sided paired randomization test on scenario-level mean differences."""
    local_matrix = np.asarray(local_matrix, dtype=float)
    axplorer_matrix = np.asarray(axplorer_matrix, dtype=float)
    scenario_diff = (axplorer_matrix - local_matrix).mean(axis=0)
    observed = abs(float(scenario_diff.mean()))
    if observed == 0.0:
        return 1.0

    rng = np.random.default_rng(seed)
    exceed = 0
    done = 0
    batch = 1000

    while done < n_perm:
        k = min(batch, n_perm - done)
        signs = rng.choice((-1.0, 1.0), size=(k, len(scenario_diff)))
        permuted = np.abs((signs * scenario_diff[None, :]).mean(axis=1))
        exceed += int(np.sum(permuted >= observed - 1e-15))
        done += k

    return float((exceed + 1) / (n_perm + 1))


def summarize_method(evaluation, bootstrap_seed):
    summary = {}
    for i, metric in enumerate(METRICS):
        matrix = evaluation["matrices"][metric]
        run_means = matrix.mean(axis=1)
        summary[metric] = {
            "mean": float(matrix.mean()),
            "ci95": hierarchical_bootstrap_ci(
                matrix,
                seed=bootstrap_seed + i,
            ),
            "training_run_mean_std": float(np.std(run_means)),
            "training_run_means": [float(x) for x in run_means],
        }
    summary["runtime_seconds"] = {
        "mean": float(np.mean(evaluation["runtime_by_run"])),
        "training_run_mean_std": float(np.std(evaluation["runtime_by_run"])),
    }
    return summary


def compare_structured(local_eval, ax_eval):
    comparison = {}
    for i, metric in enumerate(METRICS):
        local_matrix = local_eval["matrices"][metric]
        ax_matrix = ax_eval["matrices"][metric]
        stats = paired_hierarchical_bootstrap(
            local_matrix,
            ax_matrix,
            metric,
            seed=60000 + i,
        )
        stats["paired_sign_flip_pvalue"] = paired_sign_flip_pvalue(
            local_matrix,
            ax_matrix,
            seed=70000 + i,
        )
        comparison[metric] = stats
    return comparison


def _load_optional_legacy_artifacts(out_dir: Path):
    legacy_local = None
    legacy_axplorer = None
    artifact_root = out_dir.parent

    local_path = artifact_root / "local_search.json"
    if local_path.exists():
        try:
            legacy_local = load_best_genome(local_path)
        except Exception:
            legacy_local = None

    ax_path = artifact_root / "axplorer_best.json"
    if ax_path.exists():
        try:
            legacy_axplorer = load_best_genome(ax_path)
        except Exception:
            legacy_axplorer = None

    return legacy_local, legacy_axplorer


def _write_summary_csv(path, baseline_summary, local_summary, ax_summary):
    fields = [
        "method",
        "survival_mean",
        "survival_ci_low",
        "survival_ci_high",
        "containment_mean",
        "containment_ci_low",
        "containment_ci_high",
        "penetrations_mean",
        "damage_mean",
        "resources_mean",
        "runtime_seconds",
    ]

    rows = []
    for name, stats in baseline_summary.items():
        rows.append({
            "method": name,
            "survival_mean": stats["asset_survival_rate"]["mean"],
            "survival_ci_low": stats["asset_survival_rate"]["ci95"][0],
            "survival_ci_high": stats["asset_survival_rate"]["ci95"][1],
            "containment_mean": stats["containment_rate"]["mean"],
            "containment_ci_low": stats["containment_rate"]["ci95"][0],
            "containment_ci_high": stats["containment_rate"]["ci95"][1],
            "penetrations_mean": stats["penetrations"]["mean"],
            "damage_mean": stats["cumulative_damage"]["mean"],
            "resources_mean": stats["defenders_consumed"]["mean"],
            "runtime_seconds": stats["runtime_seconds"]["mean"],
        })

    for name, stats in (("rule_local", local_summary), ("rule_axplorer", ax_summary)):
        rows.append({
            "method": name,
            "survival_mean": stats["asset_survival_rate"]["mean"],
            "survival_ci_low": stats["asset_survival_rate"]["ci95"][0],
            "survival_ci_high": stats["asset_survival_rate"]["ci95"][1],
            "containment_mean": stats["containment_rate"]["mean"],
            "containment_ci_low": stats["containment_rate"]["ci95"][0],
            "containment_ci_high": stats["containment_rate"]["ci95"][1],
            "penetrations_mean": stats["penetrations"]["mean"],
            "damage_mean": stats["cumulative_damage"]["mean"],
            "resources_mean": stats["defenders_consumed"]["mean"],
            "runtime_seconds": stats["runtime_seconds"]["mean"],
        })

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _pct(x):
    return f"{100.0 * x:.1f}%"


def _write_report(
    path,
    protocol,
    baseline_summary,
    local_summary,
    ax_summary,
    comparison,
    stress_summary,
):
    local_survival = local_summary["asset_survival_rate"]["mean"]
    ax_survival = ax_summary["asset_survival_rate"]["mean"]
    survival_cmp = comparison["asset_survival_rate"]

    lines = [
        "# AegisSwarm Final Proof Report",
        "",
        f"Protocol: `{protocol['protocol_id']}`",
        "",
        "## Frozen holdout",
        "",
        f"- Final scenarios: {protocol['final_holdout']['count']}",
        f"- Seed range: {protocol['final_holdout']['first_seed']}–{protocol['final_holdout']['last_seed']}",
        f"- Independent search runs per structured method: {protocol['search_runs']}",
        f"- Search-oracle budget per run: {protocol['oracle_budget']} candidate programs",
        "",
        "## Primary result",
        "",
        f"- Structured local survival: **{_pct(local_survival)}**",
        f"- Structured Axplorer survival: **{_pct(ax_survival)}**",
        f"- Axplorer advantage: **{100.0 * survival_cmp['axplorer_minus_local']:+.1f} percentage points**",
        f"- 95% paired hierarchical bootstrap CI on difference: "
        f"[{100.0 * survival_cmp['ci95'][0]:+.1f}, {100.0 * survival_cmp['ci95'][1]:+.1f}] pp",
        f"- Paired sign-flip p-value: **{survival_cmp['paired_sign_flip_pvalue']:.6f}**",
        "",
        "## Final holdout table",
        "",
        "| Method | Survival | Containment | Penetrations | Damage | Resources |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for name, stats in baseline_summary.items():
        lines.append(
            f"| {name} | {_pct(stats['asset_survival_rate']['mean'])} | "
            f"{_pct(stats['containment_rate']['mean'])} | "
            f"{stats['penetrations']['mean']:.2f} | "
            f"{stats['cumulative_damage']['mean']:.3f} | "
            f"{stats['defenders_consumed']['mean']:.2f} |"
        )

    for name, stats in (("rule_local", local_summary), ("rule_axplorer", ax_summary)):
        lines.append(
            f"| **{name}** | **{_pct(stats['asset_survival_rate']['mean'])}** | "
            f"{_pct(stats['containment_rate']['mean'])} | "
            f"{stats['penetrations']['mean']:.2f} | "
            f"{stats['cumulative_damage']['mean']:.3f} | "
            f"{stats['defenders_consumed']['mean']:.2f} |"
        )

    lines.extend([
        "",
        "## Stress tests",
        "",
        "| Family | Local survival | Axplorer survival | Difference |",
        "|---|---:|---:|---:|",
    ])

    for family, data in stress_summary.items():
        ls = data["rule_local"]["asset_survival_rate"]["mean"]
        axs = data["rule_axplorer"]["asset_survival_rate"]["mean"]
        lines.append(
            f"| {family} | {_pct(ls)} | {_pct(axs)} | {100.0 * (axs - ls):+.1f} pp |"
        )

    lines.extend([
        "",
        "## Interpretation rule",
        "",
        "This holdout is frozen. Do not alter the algorithm using these results and rerun "
        "the same seeds as if they were still unseen. Any post-holdout algorithm change "
        "requires a new confirmation seed block.",
        "",
    ])
    path.write_text("\n".join(lines))


def _protocol_dict(
    quick,
    search_seeds,
    train_scenarios,
    oracle_budget,
    population,
    local_rounds,
    final_seeds,
    stress_episodes,
    device,
    workers,
):
    return {
        "protocol_id": PROTOCOL_ID + ("-quick-validation" if quick else ""),
        "mode": "quick_validation" if quick else "formal_final_holdout",
        "search_seeds": [int(x) for x in search_seeds],
        "search_runs": int(len(search_seeds)),
        "training_scenario_seeds": [int(x) for x in TRAIN_SEEDS[:train_scenarios]],
        "train_scenarios": int(train_scenarios),
        "oracle_budget": int(oracle_budget),
        "oracle_unit": "one unique candidate program scored over the fixed training scenario bundle",
        "population": int(population),
        "local_refinement_rounds": int(local_rounds),
        "axplorer_train_steps_per_round": int(
            QUICK_AXPLORER_TRAIN_STEPS if quick else FORMAL_AXPLORER_TRAIN_STEPS
        ),
        "axplorer_samples_per_round": int(
            QUICK_AXPLORER_SAMPLES if quick else FORMAL_AXPLORER_SAMPLES
        ),
        "axplorer_temperature": float(FORMAL_AXPLORER_TEMPERATURE),
        "final_holdout": {
            "count": int(len(final_seeds)),
            "first_seed": int(final_seeds[0]),
            "last_seed": int(final_seeds[-1]),
        },
        "stress_episodes_per_family": int(stress_episodes),
        "device": str(device),
        "workers": int(workers),
    }


def run_final_proof(
    out_dir="artifacts/final_proof",
    workers=1,
    device=None,
    quick=False,
    force_train=False,
):
    out_dir = Path(out_dir)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    if quick:
        search_seeds = QUICK_SEARCH_SEEDS
        train_scenarios = QUICK_TRAIN_SCENARIOS
        oracle_budget = QUICK_ORACLE_BUDGET
        population = QUICK_POPULATION
        local_rounds = QUICK_LOCAL_REFINEMENT_ROUNDS
        ax_train_steps = QUICK_AXPLORER_TRAIN_STEPS
        ax_samples = QUICK_AXPLORER_SAMPLES
        final_seeds = QUICK_VALIDATION_SEEDS
        stress_episodes = QUICK_STRESS_EPISODES
        stress_seed_base = 52000
    else:
        search_seeds = FORMAL_SEARCH_SEEDS
        train_scenarios = FORMAL_TRAIN_SCENARIOS
        oracle_budget = FORMAL_ORACLE_BUDGET
        population = FORMAL_POPULATION
        local_rounds = FORMAL_LOCAL_REFINEMENT_ROUNDS
        ax_train_steps = FORMAL_AXPLORER_TRAIN_STEPS
        ax_samples = FORMAL_AXPLORER_SAMPLES
        final_seeds = FINAL_HOLDOUT_SEEDS
        stress_episodes = FORMAL_STRESS_EPISODES
        stress_seed_base = 12000

    device = device or device_auto()
    train_config = EvalConfig(seeds=TRAIN_SEEDS[:train_scenarios])
    protocol = _protocol_dict(
        quick,
        search_seeds,
        train_scenarios,
        oracle_budget,
        population,
        local_rounds,
        final_seeds,
        stress_episodes,
        device,
        workers,
    )
    _save_json(out_dir / "protocol.json", protocol)

    print(
        f"AegisSwarm {protocol['mode']} | "
        f"runs={len(search_seeds)} budget={oracle_budget} "
        f"train_scenarios={train_scenarios} device={device} workers={workers}",
        flush=True,
    )

    local_runs = []
    ax_runs = []

    for index, search_seed in enumerate(search_seeds, start=1):
        print(
            f"\n=== paired training run {index}/{len(search_seeds)} "
            f"(search seed {search_seed}) ===",
            flush=True,
        )

        local_path = runs_dir / f"rule_local_seed_{search_seed}.json"
        local_run = _load_or_train(
            "rule_local",
            search_seed,
            local_path,
            train_budgeted_local,
            force_train,
            config=train_config,
            oracle_budget=oracle_budget,
            population=population,
            local_refinement_rounds=local_rounds,
            workers=workers,
            verbose=True,
        )
        local_runs.append(local_run)

        ax_path = runs_dir / f"rule_axplorer_seed_{search_seed}.json"
        ax_run = _load_or_train(
            "rule_axplorer",
            search_seed,
            ax_path,
            train_budgeted_axplorer,
            force_train,
            config=train_config,
            oracle_budget=oracle_budget,
            population=population,
            samples_per_round=ax_samples,
            train_steps=ax_train_steps,
            local_refinement_rounds=local_rounds,
            temperature=FORMAL_AXPLORER_TEMPERATURE,
            workers=workers,
            device=device,
            verbose=True,
        )
        ax_runs.append(ax_run)

    # Train a stronger RL baseline automatically rather than reusing the tiny
    # q-table produced by the smoke-test command.
    qtable_path = out_dir / "final_qtable.json"
    if qtable_path.exists() and not force_train:
        qtable = load_qtable(qtable_path)
        print(f"\n[resume] RL baseline: {qtable_path}", flush=True)
    else:
        rl_episodes = 100 if quick else 1500
        print(f"\nTraining Q-learning baseline ({rl_episodes} episodes)...", flush=True)
        qtable = train_q_learning(episodes=rl_episodes, seed=51001)
        save_qtable(qtable, qtable_path)

    legacy_local, legacy_axplorer = _load_optional_legacy_artifacts(out_dir)

    scenario_kwargs = {
        "n_threats": 30,
        "n_defenders": 8,
        "n_assets": 2,
        "n_sensors": 3,
    }

    print(
        f"\nEvaluating {'validation' if quick else 'UNTOUCHED FINAL HOLDOUT'} "
        f"({len(final_seeds)} scenarios)...",
        flush=True,
    )

    baseline_result = evaluate_policies(
        final_seeds,
        scenario_kwargs=scenario_kwargs,
        qtable=qtable,
        local_genome=legacy_local,
        axplorer_genome=legacy_axplorer,
    )

    local_programs = [
        np.asarray(run["best_program"], dtype=np.int16)
        for run in local_runs
    ]
    ax_programs = [
        np.asarray(run["best_program"], dtype=np.int16)
        for run in ax_runs
    ]

    local_eval = evaluate_program_runs(
        local_programs,
        final_seeds,
        scenario_kwargs,
        workers=workers,
    )
    ax_eval = evaluate_program_runs(
        ax_programs,
        final_seeds,
        scenario_kwargs,
        workers=workers,
    )

    local_summary = summarize_method(local_eval, bootstrap_seed=81000)
    ax_summary = summarize_method(ax_eval, bootstrap_seed=82000)
    comparison = compare_structured(local_eval, ax_eval)

    stress_summary = {}
    stress_comparisons = {}
    stress_raw = {}

    print("\nRunning stress families...", flush=True)
    for family_index, (family, kwargs) in enumerate(STRESS_FAMILIES.items()):
        stress_seeds = tuple(
            range(
                stress_seed_base + family_index * 1000,
                stress_seed_base + family_index * 1000 + stress_episodes,
            )
        )
        print(f"  - {family}: {len(stress_seeds)} scenarios", flush=True)

        family_local = evaluate_program_runs(
            local_programs,
            stress_seeds,
            kwargs,
            workers=workers,
        )
        family_ax = evaluate_program_runs(
            ax_programs,
            stress_seeds,
            kwargs,
            workers=workers,
        )

        stress_summary[family] = {
            "rule_local": summarize_method(
                family_local,
                bootstrap_seed=83000 + family_index * 100,
            ),
            "rule_axplorer": summarize_method(
                family_ax,
                bootstrap_seed=84000 + family_index * 100,
            ),
        }
        stress_comparisons[family] = compare_structured(family_local, family_ax)
        stress_raw[family] = {
            "rule_local": family_local["raw_by_run"],
            "rule_axplorer": family_ax["raw_by_run"],
        }

    result = {
        "protocol": protocol,
        "training": {
            "rule_local": local_runs,
            "rule_axplorer": ax_runs,
        },
        "final_holdout": {
            "baselines": baseline_result["summary"],
            "rule_local": local_summary,
            "rule_axplorer": ax_summary,
            "paired_comparison": comparison,
        },
        "stress": {
            "summary": stress_summary,
            "paired_comparison": stress_comparisons,
        },
    }

    _save_json(out_dir / "results.json", result)
    _save_json(out_dir / "final_raw_baselines.json", baseline_result["raw"])
    _save_json(
        out_dir / "final_raw_structured.json",
        {
            "seeds": [int(x) for x in final_seeds],
            "rule_local": local_eval["raw_by_run"],
            "rule_axplorer": ax_eval["raw_by_run"],
        },
    )
    _save_json(out_dir / "stress_raw_structured.json", stress_raw)

    _write_summary_csv(
        out_dir / "final_summary.csv",
        baseline_result["summary"],
        local_summary,
        ax_summary,
    )
    _write_report(
        out_dir / "REPORT.md",
        protocol,
        baseline_result["summary"],
        local_summary,
        ax_summary,
        comparison,
        stress_summary,
    )

    survival_cmp = comparison["asset_survival_rate"]
    print("\n=== FINAL STRUCTURED COMPARISON ===", flush=True)
    print(
        f"rule_local survival:    {local_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={local_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"rule_axplorer survival: {ax_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={ax_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"difference (A-L):       {survival_cmp['axplorer_minus_local']:+.4f} "
        f"CI={survival_cmp['ci95']}",
        flush=True,
    )
    print(
        f"paired p-value:         {survival_cmp['paired_sign_flip_pvalue']:.6f}",
        flush=True,
    )
    print(f"\nSaved complete bundle to: {out_dir}", flush=True)

    return result
