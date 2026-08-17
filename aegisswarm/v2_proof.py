from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import torch

from .axplorer_v2 import (
    FitnessConditionedRuleTransformer,
    archive_training_arrays,
    canonicalize_program,
    device_auto,
    sample_v2_programs,
    select_diverse_archive,
    train_v2_model,
)
from .final_proof import (
    BudgetedRuleOracle,
    compare_structured,
    evaluate_program_runs,
    summarize_method,
    train_budgeted_local,
)
from .rule_program import mutate_program, random_program
from .scoring import EvalConfig
from .splits import TRAIN_SEEDS, V2_CONFIRM_SEEDS, V2_DEV_SEEDS


V2_PROTOCOL_ID = "aegisswarm-axplorer-v2"
V2_SEARCH_SEEDS = (42001, 42002, 42003, 42004, 42005)
V2_TRAIN_SCENARIOS = 16
V2_ORACLE_BUDGET = 1800
V2_POPULATION = 64
V2_SAMPLES_PER_ROUND = 64
V2_LOCAL_REFINEMENT_ROUNDS = 2
V2_TRAIN_STEPS = 200
V2_SAMPLE_TEMPERATURE = 0.85
V2_WEIGHT_TEMPERATURE = 4.0
V2_ARCHIVE_SIZE = 256

QUICK_SEARCH_SEEDS = (92001, 92002)
QUICK_TRAIN_SCENARIOS = 4
QUICK_ORACLE_BUDGET = 128
QUICK_POPULATION = 16
QUICK_SAMPLES = 16
QUICK_LOCAL_ROUNDS = 1
QUICK_TRAIN_STEPS = 12
QUICK_DEV_SEEDS = tuple(V2_DEV_SEEDS[:20])


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _seed_torch(seed: int, device: str):
    torch.manual_seed(int(seed))
    if device == "mps" and torch.backends.mps.is_available():
        torch.mps.manual_seed(int(seed))
    elif device == "cuda" and torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))


def _all_cached_programs(oracle: BudgetedRuleOracle):
    return [np.asarray(key, dtype=np.int16) for key in oracle.cache]


def _best_cached(oracle: BudgetedRuleOracle):
    ranked = oracle.rank(_all_cached_programs(oracle))
    if not ranked:
        raise RuntimeError("V2 search has no evaluated programs")
    return ranked[0]


def train_budgeted_axplorer_v2(
    config: EvalConfig,
    search_seed: int,
    oracle_budget: int = V2_ORACLE_BUDGET,
    population: int = V2_POPULATION,
    samples_per_round: int = V2_SAMPLES_PER_ROUND,
    local_refinement_rounds: int = V2_LOCAL_REFINEMENT_ROUNDS,
    train_steps: int = V2_TRAIN_STEPS,
    sample_temperature: float = V2_SAMPLE_TEMPERATURE,
    weight_temperature: float = V2_WEIGHT_TEMPERATURE,
    archive_size: int = V2_ARCHIVE_SIZE,
    workers: int = 1,
    device: str | None = None,
    verbose: bool = True,
):
    """Budget-matched V2 learned search.

    Only the proposer changes relative to V1. The evaluator, score, rule program,
    training scenarios, and oracle accounting are unchanged.
    """
    rng = np.random.default_rng(int(search_seed))
    device = device or device_auto()
    _seed_torch(search_seed, device)
    model = FitnessConditionedRuleTransformer().to(device)
    started = time.perf_counter()
    history = []

    # V2 starts in the canonical grammar rather than wasting model mass on token
    # aliases that decode to identical rule semantics.
    programs = [canonicalize_program(random_program(rng)) for _ in range(int(population))]

    with BudgetedRuleOracle(config, oracle_budget, workers=workers) as oracle:
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

            sample_n = min(int(samples_per_round), max(1, oracle.remaining))
            sampled = sample_v2_programs(
                model,
                sample_n,
                temperature=sample_temperature,
                quality_level=3,
                device=device,
                seed=search_seed + 10000 + round_index,
            )

            before = oracle.evaluations
            oracle.evaluate_many(sampled)
            bases = [p for _, p, _ in oracle.rank(sampled)]

            for refinement in range(int(local_refinement_rounds)):
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
                    bkey = tuple(int(x) for x in base)
                    nkey = tuple(int(x) for x in neighbor)
                    bm = oracle.cache.get(bkey)
                    nm = oracle.cache.get(nkey)
                    if nm is not None and (bm is None or nm["fitness"] > bm["fitness"]):
                        improved.append(neighbor)
                    else:
                        improved.append(base)
                bases = improved

            # If generation collapsed to already-seen programs, inject canonical
            # random exploration so the oracle budget still measures real search.
            if oracle.evaluations == before and oracle.remaining > 0:
                fresh = [
                    canonicalize_program(random_program(rng))
                    for _ in range(min(population, oracle.remaining))
                ]
                oracle.evaluate_many(fresh)

            _, best_program, best_metrics = _best_cached(oracle)
            row = {
                "round": int(round_index),
                "oracle_evaluations": int(oracle.evaluations),
                "archive_size": int(len(archive)),
                "fitness": float(best_metrics["fitness"]),
                "asset_survival_rate": float(best_metrics["asset_survival_rate"]),
                "containment_rate": float(best_metrics["containment_rate"]),
                "cumulative_damage": float(best_metrics["cumulative_damage"]),
                "defenders_consumed": float(best_metrics["defenders_consumed"]),
                "elapsed_seconds": float(time.perf_counter() - started),
            }
            history.append(row)
            if verbose:
                print(
                    f"[axplorer-v2 seed={search_seed}] round={round_index} "
                    f"evals={oracle.evaluations}/{oracle_budget} "
                    f"archive={len(archive)} fitness={row['fitness']:.3f} "
                    f"survival={row['asset_survival_rate']:.3f}",
                    flush=True,
                )
            round_index += 1

        _, best_program, best_metrics = _best_cached(oracle)

    return {
        "method": "rule_axplorer_v2",
        "search_seed": int(search_seed),
        "device": str(device),
        "best_program": [int(x) for x in canonicalize_program(best_program)],
        "train_metrics": {k: float(v) for k, v in best_metrics.items()},
        "oracle_evaluations": int(oracle_budget),
        "training_seconds": float(time.perf_counter() - started),
        "history": history,
    }


def _load_or_train(method, search_seed, path, train_fn, force=False, **kwargs):
    path = Path(path)
    if path.exists() and not force:
        data = json.loads(path.read_text())
        if data.get("method") == method and int(data.get("search_seed", -1)) == int(search_seed):
            print(f"[resume] {method} seed={search_seed}: {path}", flush=True)
            return data
    data = train_fn(search_seed=search_seed, **kwargs)
    _save_json(path, data)
    return data


def _report(path, mode, seeds, local_summary, v2_summary, comparison):
    survival = comparison["asset_survival_rate"]
    lines = [
        "# AegisSwarm Axplorer V2 Report",
        "",
        f"Mode: **{mode}**",
        f"Evaluation scenarios: **{len(seeds)}** ({seeds[0]}–{seeds[-1]})",
        "",
        "## Primary comparison",
        "",
        f"- Structured local survival: **{100*local_summary['asset_survival_rate']['mean']:.2f}%**",
        f"- Axplorer V2 survival: **{100*v2_summary['asset_survival_rate']['mean']:.2f}%**",
        f"- V2 minus local: **{100*survival['axplorer_minus_local']:+.2f} pp**",
        f"- 95% paired hierarchical bootstrap CI: **[{100*survival['ci95'][0]:+.2f}, {100*survival['ci95'][1]:+.2f}] pp**",
        f"- Paired sign-flip p-value: **{survival['paired_sign_flip_pvalue']:.6f}**",
        "",
        "## Metrics",
        "",
        "| Method | Survival | Containment | Penetrations | Damage | Resources |",
        "|---|---:|---:|---:|---:|---:|",
        f"| rule_local | {100*local_summary['asset_survival_rate']['mean']:.1f}% | {100*local_summary['containment_rate']['mean']:.1f}% | {local_summary['penetrations']['mean']:.2f} | {local_summary['cumulative_damage']['mean']:.3f} | {local_summary['defenders_consumed']['mean']:.2f} |",
        f"| rule_axplorer_v2 | {100*v2_summary['asset_survival_rate']['mean']:.1f}% | {100*v2_summary['containment_rate']['mean']:.1f}% | {v2_summary['penetrations']['mean']:.2f} | {v2_summary['cumulative_damage']['mean']:.3f} | {v2_summary['defenders_consumed']['mean']:.2f} |",
        "",
    ]
    if mode == "development":
        lines += [
            "This block is development data and may be used to decide whether V2 is ready to freeze.",
            "Do not run the reserved confirmation block unless the V2 architecture is frozen first.",
        ]
    else:
        lines += [
            "This is the reserved confirmation block. It must not be used for another round of tuning.",
        ]
    path.write_text("\n".join(lines))


def _evaluate_and_save(out_dir, mode, seeds, local_runs, v2_runs, workers):
    scenario_kwargs = {
        "n_threats": 30,
        "n_defenders": 8,
        "n_assets": 2,
        "n_sensors": 3,
    }
    local_programs = [np.asarray(run["best_program"], dtype=np.int16) for run in local_runs]
    v2_programs = [np.asarray(run["best_program"], dtype=np.int16) for run in v2_runs]

    local_eval = evaluate_program_runs(local_programs, seeds, scenario_kwargs, workers=workers)
    v2_eval = evaluate_program_runs(v2_programs, seeds, scenario_kwargs, workers=workers)
    local_summary = summarize_method(local_eval, bootstrap_seed=91000)
    v2_summary = summarize_method(v2_eval, bootstrap_seed=92000)
    comparison = compare_structured(local_eval, v2_eval)

    result = {
        "protocol_id": V2_PROTOCOL_ID,
        "mode": mode,
        "evaluation_seeds": [int(x) for x in seeds],
        "rule_local": local_summary,
        "rule_axplorer_v2": v2_summary,
        "paired_comparison": comparison,
    }
    _save_json(Path(out_dir) / "results.json", result)
    _report(Path(out_dir) / "REPORT.md", mode, seeds, local_summary, v2_summary, comparison)

    s = comparison["asset_survival_rate"]
    print("\n=== AXPLORER V2 COMPARISON ===", flush=True)
    print(
        f"rule_local survival:       {local_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={local_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"rule_axplorer_v2 survival: {v2_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={v2_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"difference (V2-L):         {s['axplorer_minus_local']:+.4f} CI={s['ci95']}",
        flush=True,
    )
    print(f"paired p-value:            {s['paired_sign_flip_pvalue']:.6f}", flush=True)
    print(f"Saved: {out_dir}", flush=True)
    return result


def run_v2_development(
    out_dir="artifacts/axplorer_v2_dev",
    workers=4,
    device=None,
    quick=False,
    force_train=False,
):
    out_dir = Path(out_dir)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    device = device or device_auto()

    if quick:
        search_seeds = QUICK_SEARCH_SEEDS
        train_scenarios = QUICK_TRAIN_SCENARIOS
        budget = QUICK_ORACLE_BUDGET
        population = QUICK_POPULATION
        samples = QUICK_SAMPLES
        local_rounds = QUICK_LOCAL_ROUNDS
        train_steps = QUICK_TRAIN_STEPS
        eval_seeds = QUICK_DEV_SEEDS
    else:
        search_seeds = V2_SEARCH_SEEDS
        train_scenarios = V2_TRAIN_SCENARIOS
        budget = V2_ORACLE_BUDGET
        population = V2_POPULATION
        samples = V2_SAMPLES_PER_ROUND
        local_rounds = V2_LOCAL_REFINEMENT_ROUNDS
        train_steps = V2_TRAIN_STEPS
        eval_seeds = V2_DEV_SEEDS

    protocol = {
        "protocol_id": V2_PROTOCOL_ID + ("-quick" if quick else "-development"),
        "search_seeds": list(search_seeds),
        "train_scenario_seeds": list(TRAIN_SEEDS[:train_scenarios]),
        "oracle_budget_per_method_per_run": int(budget),
        "population": int(population),
        "evaluation_seed_first": int(eval_seeds[0]),
        "evaluation_seed_last": int(eval_seeds[-1]),
        "evaluation_seed_count": int(len(eval_seeds)),
        "device": str(device),
        "workers": int(workers),
        "changes_vs_v1": [
            "fitness/rank conditioning",
            "score-weighted likelihood training",
            "field-specific grammar heads",
            "canonical rule encoding",
            "multi-objective diversity archive",
        ],
    }
    _save_json(out_dir / "protocol.json", protocol)

    print(
        f"AegisSwarm Axplorer V2 {'quick' if quick else 'development'} | "
        f"runs={len(search_seeds)} budget={budget} train_scenarios={train_scenarios} "
        f"eval_scenarios={len(eval_seeds)} device={device} workers={workers}",
        flush=True,
    )

    config = EvalConfig(seeds=TRAIN_SEEDS[:train_scenarios])
    local_runs = []
    v2_runs = []

    for i, search_seed in enumerate(search_seeds, start=1):
        print(f"\n=== paired V2 run {i}/{len(search_seeds)} seed={search_seed} ===", flush=True)
        local = _load_or_train(
            "rule_local",
            search_seed,
            runs_dir / f"rule_local_seed_{search_seed}.json",
            train_budgeted_local,
            force=force_train,
            config=config,
            oracle_budget=budget,
            population=population,
            local_refinement_rounds=local_rounds,
            workers=workers,
            verbose=True,
        )
        local_runs.append(local)

        v2 = _load_or_train(
            "rule_axplorer_v2",
            search_seed,
            runs_dir / f"rule_axplorer_v2_seed_{search_seed}.json",
            train_budgeted_axplorer_v2,
            force=force_train,
            config=config,
            oracle_budget=budget,
            population=population,
            samples_per_round=samples,
            local_refinement_rounds=local_rounds,
            train_steps=train_steps,
            sample_temperature=V2_SAMPLE_TEMPERATURE,
            weight_temperature=V2_WEIGHT_TEMPERATURE,
            archive_size=V2_ARCHIVE_SIZE,
            workers=workers,
            device=device,
            verbose=True,
        )
        v2_runs.append(v2)

    return _evaluate_and_save(
        out_dir,
        "quick_development" if quick else "development",
        eval_seeds,
        local_runs,
        v2_runs,
        workers,
    )


def run_v2_confirmation(
    source_dir="artifacts/axplorer_v2_dev",
    out_dir="artifacts/axplorer_v2_confirm",
    workers=4,
):
    """Evaluate the already-frozen development policies on reserved seeds.

    This function never trains and therefore cannot silently alter the frozen V2
    policies after development results are observed.
    """
    source_dir = Path(source_dir)
    runs_dir = source_dir / "runs"
    local_runs = []
    v2_runs = []
    for search_seed in V2_SEARCH_SEEDS:
        lp = runs_dir / f"rule_local_seed_{search_seed}.json"
        vp = runs_dir / f"rule_axplorer_v2_seed_{search_seed}.json"
        if not lp.exists() or not vp.exists():
            raise FileNotFoundError(
                f"Missing frozen development run for seed {search_seed}; run V2 development first."
            )
        local_runs.append(json.loads(lp.read_text()))
        v2_runs.append(json.loads(vp.read_text()))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _save_json(
        out_dir / "protocol.json",
        {
            "protocol_id": V2_PROTOCOL_ID + "-confirmation",
            "source_dir": str(source_dir),
            "search_seeds": list(V2_SEARCH_SEEDS),
            "confirmation_first_seed": int(V2_CONFIRM_SEEDS[0]),
            "confirmation_last_seed": int(V2_CONFIRM_SEEDS[-1]),
            "confirmation_count": int(len(V2_CONFIRM_SEEDS)),
            "training_allowed": False,
        },
    )
    print(
        f"AegisSwarm Axplorer V2 CONFIRMATION | frozen runs={len(V2_SEARCH_SEEDS)} "
        f"scenarios={len(V2_CONFIRM_SEEDS)} ({V2_CONFIRM_SEEDS[0]}-{V2_CONFIRM_SEEDS[-1]})",
        flush=True,
    )
    return _evaluate_and_save(
        out_dir,
        "confirmation",
        V2_CONFIRM_SEEDS,
        local_runs,
        v2_runs,
        workers,
    )
