from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .axplorer_v2 import canonicalize_program
from .evidence_hardening import load_incumbent_programs
from .final_proof import METRICS, paired_hierarchical_bootstrap, summarize_method
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS
from .random_tape import IndexedRandomTape
from .reliability import ReliabilityAwareBackupPolicy
from .reliability_ablation import evaluate_programs
from .rule_program import crossover_program, mutate_program, random_program
from .scenarios import ScenarioGenerator
from .simulator_v2 import SimulatorV2
from .splits import ROBUST_DEV_SEEDS, ROBUST_TRAIN_WORLD_SEEDS


PROTOCOL_ID = "aegisswarm-stochastic-robust-training-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"

SEARCH_SEEDS = (46001, 46002, 46003, 46004, 46005)
TRAIN_WORLDS = 12
TAPE_REPLICATES = 3
ORACLE_BUDGET = 1800
POPULATION = 64
LOCAL_REFINEMENT_ROUNDS = 2

QUICK_SEARCH_SEEDS = (96001, 96002)
QUICK_TRAIN_WORLDS = 4
QUICK_TAPE_REPLICATES = 2
QUICK_BUDGET = 128
QUICK_POPULATION = 16
QUICK_LOCAL_ROUNDS = 1
QUICK_EVAL_SEEDS = tuple(ROBUST_DEV_SEEDS[:20])


@dataclass(frozen=True)
class RobustEvalSpec:
    world_seeds: tuple[int, ...]
    tape_replicates: int
    executor_mode: str
    scenario_kwargs: tuple[tuple[str, float], ...]


def robust_tape_seed(world_seed: int, replicate_index: int) -> int:
    """Stable tape seed independent of candidate/policy call order."""
    modulus = (1 << 63) - 25
    return int(
        (
            1_000_003 * int(world_seed)
            + 97_531 * (int(replicate_index) + 1)
            + 424_242_424
        )
        % modulus
    )


def _policy(executor_mode: str, tokens):
    if executor_mode == "incumbent":
        return RuleGuidedHungarianPolicy(tokens)
    if executor_mode == "backup":
        return ReliabilityAwareBackupPolicy(tokens)
    raise ValueError(f"unknown executor mode: {executor_mode}")


def _aggregate_rows(rows):
    survival_values = np.asarray([float(r["asset_survival_rate"]) for r in rows], dtype=float)
    survival = float(np.mean(survival_values))
    containment = float(np.mean([r["containment_rate"] for r in rows]))
    penetrations = float(np.mean([r["penetrations"] for r in rows]))
    damage = float(np.mean([r["cumulative_damage"] for r in rows]))
    resources = float(np.mean([r["defenders_consumed"] for r in rows]))
    response = float(np.mean([r["mean_response_delay"] for r in rows]))

    # V1 intentionally retains the established scalar objective. Replication
    # changes the stochastic training distribution, not the scoring weights.
    loss = (
        100.0 * (1.0 - survival)
        + 40.0 * (1.0 - containment)
        + 3.0 * damage
        + 0.15 * resources
        + 0.05 * response
    )
    fitness = max(0.0, 200.0 - loss)

    q = max(1, int(np.ceil(0.25 * len(survival_values))))
    worst_quartile = float(np.sort(survival_values)[:q].mean())
    return {
        "fitness": float(fitness),
        "loss": float(loss),
        "asset_survival_rate": survival,
        "containment_rate": containment,
        "penetrations": penetrations,
        "cumulative_damage": damage,
        "defenders_consumed": resources,
        "mean_response_delay": response,
        "survival_std_across_rollouts": float(np.std(survival_values)),
        "worst_quartile_survival_diagnostic": worst_quartile,
        "rollouts": int(len(rows)),
    }


def evaluate_program_replicated(tokens, spec: RobustEvalSpec):
    kwargs = dict(spec.scenario_kwargs)
    max_steps = int(kwargs.pop("max_steps", 150))
    gen = ScenarioGenerator(max_steps=max_steps)
    rows = []

    for world_seed in spec.world_seeds:
        base = gen.generate(seed=int(world_seed), **kwargs)
        for replicate_index in range(int(spec.tape_replicates)):
            scenario = ScenarioGenerator.clone(base)
            simulator = SimulatorV2(scenario)
            simulator.tape = IndexedRandomTape(
                robust_tape_seed(int(world_seed), int(replicate_index))
            )
            rows.append(simulator.run(_policy(spec.executor_mode, tokens)).as_dict())

    return _aggregate_rows(rows)


def _candidate_worker(payload):
    tokens, spec = payload
    return evaluate_program_replicated(np.asarray(tokens, dtype=np.int16), spec)


class RobustBudgetedOracle:
    def __init__(self, spec: RobustEvalSpec, budget: int, workers: int = 1):
        self.spec = spec
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
    def remaining(self):
        return max(0, self.budget - self.evaluations)

    def evaluate_many(self, programs):
        pending = []
        keys = []
        seen = set()
        for program in programs:
            canonical = canonicalize_program(program)
            key = tuple(int(x) for x in canonical)
            if key in self.cache or key in seen:
                continue
            if len(pending) >= self.remaining:
                break
            seen.add(key)
            keys.append(key)
            pending.append(list(key))

        if not pending:
            return 0

        payloads = [(tokens, self.spec) for tokens in pending]
        if self._executor is None:
            results = [_candidate_worker(payload) for payload in payloads]
        else:
            results = list(self._executor.map(_candidate_worker, payloads))

        for key, metrics in zip(keys, results):
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
            (
                float(self.cache[key]["fitness"]),
                np.asarray(key, dtype=np.int16),
                self.cache[key],
            )
            for key in keys
        ]
        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked


def train_robust_local(
    *,
    spec: RobustEvalSpec,
    search_seed: int,
    oracle_budget: int,
    population: int,
    local_refinement_rounds: int,
    workers: int,
    verbose: bool = True,
):
    rng = np.random.default_rng(int(search_seed))
    programs = [canonicalize_program(random_program(rng)) for _ in range(int(population))]
    history = []
    started = time.perf_counter()

    with RobustBudgetedOracle(spec, oracle_budget, workers=workers) as oracle:
        oracle.evaluate_many(programs)
        round_index = 0
        while oracle.remaining > 0:
            ranked = oracle.rank(programs)
            if not ranked:
                raise RuntimeError("Robust local search has no evaluated population")

            elite_n = max(4, min(len(ranked), max(4, int(population) // 5)))
            elites = [p.copy() for _, p, _ in ranked[:elite_n]]
            pool = [p.copy() for _, p, _ in ranked[: int(population)]]

            children = []
            for _ in range(int(population)):
                a = elites[int(rng.integers(0, len(elites)))]
                b = elites[int(rng.integers(0, len(elites)))]
                child = canonicalize_program(crossover_program(a, b, rng))
                child = canonicalize_program(
                    mutate_program(
                        child,
                        rng,
                        n_mutations=int(rng.integers(1, 5)),
                        radius=4,
                    )
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

            programs = [p.copy() for _, p, _ in oracle.rank(pool)[: int(population)]]
            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [
                    canonicalize_program(random_program(rng))
                    for _ in range(min(int(population), oracle.remaining))
                ]
                oracle.evaluate_many(fresh)
                programs.extend(fresh)
                programs = [
                    p.copy() for _, p, _ in oracle.rank(programs)[: int(population)]
                ]

            _, best_program, best_metrics = oracle.rank()[0]
            row = {
                "round": int(round_index),
                "oracle_evaluations": int(oracle.evaluations),
                "fitness": float(best_metrics["fitness"]),
                "asset_survival_rate": float(best_metrics["asset_survival_rate"]),
                "worst_quartile_survival_diagnostic": float(
                    best_metrics["worst_quartile_survival_diagnostic"]
                ),
                "best_program": [int(x) for x in best_program],
                "elapsed_seconds": float(time.perf_counter() - started),
            }
            history.append(row)
            if verbose:
                print(
                    f"[robust-{spec.executor_mode} seed={search_seed}] "
                    f"round={round_index} evals={oracle.evaluations}/{oracle_budget} "
                    f"fitness={row['fitness']:.3f} "
                    f"survival={row['asset_survival_rate']:.3f} "
                    f"worstQ={row['worst_quartile_survival_diagnostic']:.3f}",
                    flush=True,
                )
            round_index += 1

        _, best_program, best_metrics = oracle.rank()[0]

    return {
        "method": f"robust_local_{spec.executor_mode}",
        "search_seed": int(search_seed),
        "executor_mode": spec.executor_mode,
        "best_program": [int(x) for x in best_program],
        "train_metrics": {k: float(v) for k, v in best_metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "rollouts_per_candidate": int(len(spec.world_seeds) * spec.tape_replicates),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _load_or_train(path, expected_method, search_seed, **kwargs):
    path = Path(path)
    if path.exists():
        data = json.loads(path.read_text())
        if (
            data.get("method") == expected_method
            and int(data.get("search_seed", -1)) == int(search_seed)
        ):
            print(f"[resume] {expected_method} seed={search_seed}: {path}", flush=True)
            return data
    data = train_robust_local(search_seed=search_seed, **kwargs)
    _save_json(path, data)
    return data


def _paired(first_eval, second_eval, seed_base):
    out = {}
    for i, metric in enumerate(METRICS):
        stats = paired_hierarchical_bootstrap(
            first_eval["matrices"][metric],
            second_eval["matrices"][metric],
            metric,
            seed=seed_base + i,
        )
        out[metric] = {
            "second_minus_first": float(stats["axplorer_minus_local"]),
            "ci95": [float(x) for x in stats["ci95"]],
            "paired_training_run_win_rate": float(stats["paired_training_run_win_rate"]),
            "paired_scenario_win_rate": float(stats["paired_scenario_win_rate"]),
        }
    return out


def _per_run_delta(first_eval, second_eval):
    a = first_eval["matrices"]["asset_survival_rate"]
    b = second_eval["matrices"]["asset_survival_rate"]
    return [float(x) for x in (b - a).mean(axis=1)]


def run_stochastic_robust_training(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/stochastic_robust_quick",
    workers=5,
    quick=True,
):
    if quick:
        search_seeds = QUICK_SEARCH_SEEDS
        train_worlds = tuple(ROBUST_TRAIN_WORLD_SEEDS[:QUICK_TRAIN_WORLDS])
        tape_replicates = QUICK_TAPE_REPLICATES
        budget = QUICK_BUDGET
        population = QUICK_POPULATION
        local_rounds = QUICK_LOCAL_ROUNDS
        eval_seeds = QUICK_EVAL_SEEDS
    else:
        search_seeds = SEARCH_SEEDS
        train_worlds = tuple(ROBUST_TRAIN_WORLD_SEEDS[:TRAIN_WORLDS])
        tape_replicates = TAPE_REPLICATES
        budget = ORACLE_BUDGET
        population = POPULATION
        local_rounds = LOCAL_REFINEMENT_ROUNDS
        eval_seeds = ROBUST_DEV_SEEDS

    scenario_kwargs = tuple(sorted(dict(SCENARIO_KWARGS).items()))
    incumbent_spec = RobustEvalSpec(
        world_seeds=train_worlds,
        tape_replicates=tape_replicates,
        executor_mode="incumbent",
        scenario_kwargs=scenario_kwargs,
    )
    backup_spec = RobustEvalSpec(
        world_seeds=train_worlds,
        tape_replicates=tape_replicates,
        executor_mode="backup",
        scenario_kwargs=scenario_kwargs,
    )

    out_dir = Path(out_dir)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "search_seeds": [int(x) for x in search_seeds],
        "train_world_seeds": [int(x) for x in train_worlds],
        "tape_replicates": int(tape_replicates),
        "rollouts_per_candidate": int(len(train_worlds) * tape_replicates),
        "oracle_budget_per_method_per_run": int(budget),
        "population": int(population),
        "fitness": "existing scalar fitness averaged over matched SimulatorV2 replications",
        "evaluation_first_seed": int(eval_seeds[0]),
        "evaluation_last_seed": int(eval_seeds[-1]),
        "evaluation_count": int(len(eval_seeds)),
        "architecture_frozen": False,
    }
    _save_json(out_dir / "protocol.json", protocol)

    print(
        f"AegisSwarm stochastic-robust {'quick' if quick else 'development'} | "
        f"runs={len(search_seeds)} budget={budget} worlds={len(train_worlds)} "
        f"tapes/world={tape_replicates} rollouts/candidate={len(train_worlds)*tape_replicates} "
        f"eval_scenarios={len(eval_seeds)} workers={workers}",
        flush=True,
    )

    incumbent_runs = []
    backup_runs = []
    for i, search_seed in enumerate(search_seeds, start=1):
        print(f"\n=== robust paired run {i}/{len(search_seeds)} seed={search_seed} ===", flush=True)
        incumbent_runs.append(
            _load_or_train(
                runs_dir / f"robust_incumbent_seed_{search_seed}.json",
                "robust_local_incumbent",
                search_seed,
                spec=incumbent_spec,
                oracle_budget=budget,
                population=population,
                local_refinement_rounds=local_rounds,
                workers=workers,
                verbose=True,
            )
        )
        backup_runs.append(
            _load_or_train(
                runs_dir / f"robust_backup_seed_{search_seed}.json",
                "robust_local_backup",
                search_seed,
                spec=backup_spec,
                oracle_budget=budget,
                population=population,
                local_refinement_rounds=local_rounds,
                workers=workers,
                verbose=True,
            )
        )

    incumbent_programs = [np.asarray(r["best_program"], dtype=np.int16) for r in incumbent_runs]
    backup_programs = [np.asarray(r["best_program"], dtype=np.int16) for r in backup_runs]
    frozen_programs = load_incumbent_programs(source_dir)

    # 2x2 cross-evaluation isolates program adaptation from executor effect.
    inc_on_inc = evaluate_programs("incumbent", incumbent_programs, eval_seeds, workers=workers)
    inc_on_backup = evaluate_programs("backup", incumbent_programs, eval_seeds, workers=workers)
    backup_on_inc = evaluate_programs("incumbent", backup_programs, eval_seeds, workers=workers)
    backup_on_backup = evaluate_programs("backup", backup_programs, eval_seeds, workers=workers)

    frozen_inc = evaluate_programs("incumbent", frozen_programs, eval_seeds, workers=workers)
    frozen_backup = evaluate_programs("backup", frozen_programs, eval_seeds, workers=workers)

    summaries = {
        "frozen_incumbent_reference": summarize_method(frozen_inc, 220100),
        "frozen_backup_reference": summarize_method(frozen_backup, 220200),
        "robust_inc_program_inc_executor": summarize_method(inc_on_inc, 220300),
        "robust_inc_program_backup_executor": summarize_method(inc_on_backup, 220400),
        "robust_backup_program_inc_executor": summarize_method(backup_on_inc, 220500),
        "robust_backup_program_backup_executor": summarize_method(backup_on_backup, 220600),
    }

    comparisons = {
        "main_coadapted_backup_minus_coadapted_incumbent": _paired(
            inc_on_inc, backup_on_backup, 221000
        ),
        "executor_effect_on_incumbent_trained_programs": _paired(
            inc_on_inc, inc_on_backup, 222000
        ),
        "program_effect_under_incumbent_executor": _paired(
            inc_on_inc, backup_on_inc, 223000
        ),
        "program_effect_under_backup_executor": _paired(
            inc_on_backup, backup_on_backup, 224000
        ),
        "executor_effect_on_backup_trained_programs": _paired(
            backup_on_inc, backup_on_backup, 225000
        ),
    }

    result = {
        "protocol": protocol,
        "summaries": summaries,
        "comparisons": comparisons,
        "main_per_run_survival_deltas": _per_run_delta(inc_on_inc, backup_on_backup),
        "notes": [
            "Frozen references were trained under an older simulator generation and are descriptive only.",
            "Both robust search arms use identical search seeds, candidate budgets, structural worlds and tape bundles.",
            "V1 changes the stochastic training distribution only; scoring weights and rule representation are unchanged.",
            "No CVaR or explicit tail-risk penalty is optimized in V1.",
        ],
    }
    _save_json(out_dir / "results.json", result)

    def surv(name):
        return summaries[name]["asset_survival_rate"]["mean"]

    main = comparisons["main_coadapted_backup_minus_coadapted_incumbent"]["asset_survival_rate"]
    ex_inc = comparisons["executor_effect_on_incumbent_trained_programs"]["asset_survival_rate"]
    prog_inc = comparisons["program_effect_under_incumbent_executor"]["asset_survival_rate"]
    prog_backup = comparisons["program_effect_under_backup_executor"]["asset_survival_rate"]

    report = [
        "# AegisSwarm Stochastic-Robust Training",
        "",
        f"Protocol: `{protocol['protocol_id']}`",
        f"Evaluation scenarios: {len(eval_seeds)} ({eval_seeds[0]}–{eval_seeds[-1]})",
        f"Training rollouts per candidate: {protocol['rollouts_per_candidate']}",
        "",
        f"- frozen incumbent reference: {surv('frozen_incumbent_reference'):.4f}",
        f"- frozen backup reference: {surv('frozen_backup_reference'):.4f}",
        f"- robust incumbent/incumbent: {surv('robust_inc_program_inc_executor'):.4f}",
        f"- robust incumbent/backup: {surv('robust_inc_program_backup_executor'):.4f}",
        f"- robust backup/incumbent: {surv('robust_backup_program_inc_executor'):.4f}",
        f"- robust backup/backup: {surv('robust_backup_program_backup_executor'):.4f}",
        "",
        f"Main co-adapted delta: {main['second_minus_first']:+.4f} CI={main['ci95']}",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== STOCHASTIC-ROBUST TRAINING ===", flush=True)
    print(f"frozen incumbent reference:      {surv('frozen_incumbent_reference'):.3f}", flush=True)
    print(f"frozen backup reference:         {surv('frozen_backup_reference'):.3f}", flush=True)
    print(f"robust inc / inc executor:       {surv('robust_inc_program_inc_executor'):.3f}", flush=True)
    print(f"robust inc / backup executor:    {surv('robust_inc_program_backup_executor'):.3f}", flush=True)
    print(f"robust backup / inc executor:    {surv('robust_backup_program_inc_executor'):.3f}", flush=True)
    print(f"robust backup / backup executor: {surv('robust_backup_program_backup_executor'):.3f}", flush=True)
    print(
        f"co-adapted backup - incumbent:   {main['second_minus_first']:+.4f} CI={main['ci95']}",
        flush=True,
    )
    print(
        f"executor effect on inc-programs: {ex_inc['second_minus_first']:+.4f} CI={ex_inc['ci95']}",
        flush=True,
    )
    print(
        f"program effect under incumbent:  {prog_inc['second_minus_first']:+.4f} CI={prog_inc['ci95']}",
        flush=True,
    )
    print(
        f"program effect under backup:     {prog_backup['second_minus_first']:+.4f} CI={prog_backup['ci95']}",
        flush=True,
    )
    print(f"main per-run deltas:             {result['main_per_run_survival_deltas']}", flush=True)
    print(f"Saved: {out_dir}", flush=True)
    return result
