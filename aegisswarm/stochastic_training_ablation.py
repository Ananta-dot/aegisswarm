from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .evidence_hardening import load_incumbent_programs
from .final_proof import METRICS, paired_hierarchical_bootstrap, summarize_method
from .hybrid_ablation import SCENARIO_KWARGS
from .reliability_ablation import evaluate_programs
from .stochastic_robust import RobustEvalSpec, train_robust_local
from .splits import (
    STOCHASTIC_ABLATION_DEV_SEEDS,
    STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS,
)


PROTOCOL_ID = "aegisswarm-stochastic-training-ablation-v2"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"

SEARCH_SEEDS = (47001, 47002, 47003, 47004, 47005)
TRAIN_WORLDS = 12
REPEATED_TAPES = 3
ORACLE_BUDGET = 1800
POPULATION = 64
LOCAL_REFINEMENT_ROUNDS = 2

QUICK_SEARCH_SEEDS = (97001, 97002)
QUICK_TRAIN_WORLDS = 4
QUICK_REPEATED_TAPES = 2
QUICK_BUDGET = 128
QUICK_POPULATION = 16
QUICK_LOCAL_ROUNDS = 1
QUICK_EVAL_SEEDS = tuple(STOCHASTIC_ABLATION_DEV_SEEDS[:20])


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _load_or_train(path, expected_method, search_seed, *, spec, budget, population, local_rounds, workers):
    path = Path(path)
    if path.exists():
        data = json.loads(path.read_text())
        if data.get("method") == expected_method and int(data.get("search_seed", -1)) == int(search_seed):
            print(f"[resume] {expected_method} seed={search_seed}: {path}", flush=True)
            return data

    data = train_robust_local(
        spec=spec,
        search_seed=int(search_seed),
        oracle_budget=int(budget),
        population=int(population),
        local_refinement_rounds=int(local_rounds),
        workers=int(workers),
        verbose=True,
    )
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
    first = first_eval["matrices"]["asset_survival_rate"]
    second = second_eval["matrices"]["asset_survival_rate"]
    return [float(x) for x in (second - first).mean(axis=1)]


def run_stochastic_training_ablation(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/stochastic_training_ablation_quick",
    workers=5,
    quick=True,
):
    if quick:
        search_seeds = QUICK_SEARCH_SEEDS
        train_worlds = tuple(STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS[:QUICK_TRAIN_WORLDS])
        repeated_tapes = QUICK_REPEATED_TAPES
        budget = QUICK_BUDGET
        population = QUICK_POPULATION
        local_rounds = QUICK_LOCAL_ROUNDS
        eval_seeds = QUICK_EVAL_SEEDS
    else:
        search_seeds = SEARCH_SEEDS
        train_worlds = tuple(STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS[:TRAIN_WORLDS])
        repeated_tapes = REPEATED_TAPES
        budget = ORACLE_BUDGET
        population = POPULATION
        local_rounds = LOCAL_REFINEMENT_ROUNDS
        eval_seeds = STOCHASTIC_ABLATION_DEV_SEEDS

    scenario_kwargs = tuple(sorted(dict(SCENARIO_KWARGS).items()))
    single_spec = RobustEvalSpec(
        world_seeds=train_worlds,
        tape_replicates=1,
        executor_mode="incumbent",
        scenario_kwargs=scenario_kwargs,
    )
    repeated_spec = RobustEvalSpec(
        world_seeds=train_worlds,
        tape_replicates=int(repeated_tapes),
        executor_mode="incumbent",
        scenario_kwargs=scenario_kwargs,
    )

    out_dir = Path(out_dir)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    protocol = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "search_seeds": [int(x) for x in search_seeds],
        "train_world_seeds": [int(x) for x in train_worlds],
        "single_tapes_per_world": 1,
        "repeated_tapes_per_world": int(repeated_tapes),
        "single_rollouts_per_candidate": int(len(train_worlds)),
        "repeated_rollouts_per_candidate": int(len(train_worlds) * repeated_tapes),
        "oracle_budget_per_arm_per_run": int(budget),
        "population": int(population),
        "executor_both_arms": "RuleGuidedHungarianPolicy",
        "fitness_both_arms": "existing scalar fitness under SimulatorV2",
        "evaluation_first_seed": int(eval_seeds[0]),
        "evaluation_last_seed": int(eval_seeds[-1]),
        "evaluation_count": int(len(eval_seeds)),
        "architecture_frozen": False,
        "interpretation": (
            "The repeated-tape arm contains the single-tape arm's replicate-0 tape "
            "plus additional matched tapes for every structural world."
        ),
    }
    _save_json(out_dir / "protocol.json", protocol)

    print(
        f"AegisSwarm stochastic-training ablation {'quick' if quick else 'development'} | "
        f"runs={len(search_seeds)} budget={budget} worlds={len(train_worlds)} "
        f"single=1 tape/world repeated={repeated_tapes} tapes/world "
        f"eval_scenarios={len(eval_seeds)} workers={workers}",
        flush=True,
    )

    single_runs = []
    repeated_runs = []
    for i, search_seed in enumerate(search_seeds, start=1):
        print(f"\n=== paired stochastic run {i}/{len(search_seeds)} seed={search_seed} ===", flush=True)
        single_runs.append(
            _load_or_train(
                runs_dir / f"single_tape_seed_{search_seed}.json",
                "robust_local_incumbent",
                search_seed,
                spec=single_spec,
                budget=budget,
                population=population,
                local_rounds=local_rounds,
                workers=workers,
            )
        )
        repeated_runs.append(
            _load_or_train(
                runs_dir / f"repeated_tape_seed_{search_seed}.json",
                "robust_local_incumbent",
                search_seed,
                spec=repeated_spec,
                budget=budget,
                population=population,
                local_rounds=local_rounds,
                workers=workers,
            )
        )

    single_programs = [np.asarray(run["best_program"], dtype=np.int16) for run in single_runs]
    repeated_programs = [np.asarray(run["best_program"], dtype=np.int16) for run in repeated_runs]
    frozen_programs = load_incumbent_programs(source_dir)

    single_eval = evaluate_programs("incumbent", single_programs, eval_seeds, workers=workers)
    repeated_eval = evaluate_programs("incumbent", repeated_programs, eval_seeds, workers=workers)
    frozen_eval = evaluate_programs("incumbent", frozen_programs, eval_seeds, workers=workers)

    summaries = {
        "frozen_reference": summarize_method(frozen_eval, 250100),
        "single_tape_training": summarize_method(single_eval, 250200),
        "repeated_tape_training": summarize_method(repeated_eval, 250300),
    }
    paired = _paired(single_eval, repeated_eval, 251000)
    per_run = _per_run_delta(single_eval, repeated_eval)

    result = {
        "protocol": protocol,
        "summaries": summaries,
        "repeated_minus_single": paired,
        "per_run_survival_deltas_repeated_minus_single": per_run,
        "training": {
            "single": single_runs,
            "repeated": repeated_runs,
        },
        "notes": [
            "The frozen reference is descriptive only because it was trained under an older protocol.",
            "The primary causal comparison is repeated-tape versus single-tape training.",
            "Both primary arms use the same incumbent executor, 60-token representation, search seeds, structural worlds and candidate budget.",
            "V2 intentionally does not compute-match simulator rollouts; repeated-tape evaluation costs more per candidate. A positive result would establish value of repeated stochastic evaluation, after which a compute-matched efficiency ablation can follow.",
        ],
    }
    _save_json(out_dir / "results.json", result)

    def surv(name):
        return summaries[name]["asset_survival_rate"]["mean"]

    s = paired["asset_survival_rate"]
    report = [
        "# AegisSwarm Stochastic Training Ablation V2",
        "",
        f"Protocol: `{protocol['protocol_id']}`",
        f"Evaluation scenarios: {len(eval_seeds)} ({eval_seeds[0]}–{eval_seeds[-1]})",
        "",
        f"- frozen reference: {surv('frozen_reference'):.4f}",
        f"- single-tape training: {surv('single_tape_training'):.4f}",
        f"- repeated-tape training: {surv('repeated_tape_training'):.4f}",
        f"- repeated minus single: {s['second_minus_first']:+.4f}, CI={s['ci95']}",
        f"- per-run deltas: {per_run}",
        "",
        "Primary interpretation is repeated-tape versus single-tape training only.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== STOCHASTIC TRAINING ABLATION V2 ===", flush=True)
    print(f"frozen reference:               {surv('frozen_reference'):.3f}", flush=True)
    print(f"single-tape training:           {surv('single_tape_training'):.3f}", flush=True)
    print(f"repeated-tape training:         {surv('repeated_tape_training'):.3f}", flush=True)
    print(
        f"repeated - single:              {s['second_minus_first']:+.4f} CI={s['ci95']}",
        flush=True,
    )
    print(f"per-run deltas:                 {per_run}", flush=True)
    print(
        "training rollouts/candidate:    "
        f"{protocol['single_rollouts_per_candidate']} / {protocol['repeated_rollouts_per_candidate']}",
        flush=True,
    )
    print(
        "runtime single/repeated:        "
        f"{summaries['single_tape_training']['runtime_seconds']['mean']:.4f}s / "
        f"{summaries['repeated_tape_training']['runtime_seconds']['mean']:.4f}s",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
