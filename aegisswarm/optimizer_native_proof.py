from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .final_proof import (
    METRICS,
    paired_hierarchical_bootstrap,
    paired_sign_flip_pvalue,
    summarize_method,
)
from .hybrid_ablation import (
    SCENARIO_KWARGS,
    evaluate_hybrid_program_runs,
    evaluate_optimizer_only,
)
from .hybrid_objective import train_hybrid_local
from .optimizer_native import OptimizerNativePolicy, train_native_local
from .scenarios import ScenarioGenerator
from .scoring import EvalConfig
from .simulator import Simulator
from .splits import (
    NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS,
    NATIVE_OBJECTIVE_V2_DEV_SEEDS,
    TRAIN_SEEDS,
)


# V1 quick and full development exposed a malformed zero-centred native utility
# that systematically under-assigned. V2 is a new representation and therefore
# gets fresh development/confirmation blocks.
PROTOCOL_ID = "aegisswarm-optimizer-native-objective-v2"
SEARCH_SEEDS = (44001, 44002, 44003, 44004, 44005)
TRAIN_SCENARIOS = 16
ORACLE_BUDGET = 1800
POPULATION = 64
LOCAL_REFINEMENT_ROUNDS = 2

QUICK_SEARCH_SEEDS = (94001, 94002)
QUICK_TRAIN_SCENARIOS = 4
QUICK_BUDGET = 128
QUICK_POPULATION = 16
QUICK_LOCAL_ROUNDS = 1
QUICK_EVAL_SEEDS = tuple(NATIVE_OBJECTIVE_V2_DEV_SEEDS[:20])


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _load_or_train(path, method, search_seed, train_fn, force=False, **kwargs):
    path = Path(path)
    if path.exists() and not force:
        data = json.loads(path.read_text())
        if (
            data.get("method") == method
            and int(data.get("search_seed", -1)) == int(search_seed)
        ):
            print(f"[resume] {method} seed={search_seed}: {path}", flush=True)
            return data
    data = train_fn(search_seed=search_seed, **kwargs)
    _save_json(path, data)
    return data


def _evaluate_native_on_seeds(vector, seeds, scenario_kwargs):
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
            OptimizerNativePolicy(vector),
        )
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())
    return {
        "rows": rows,
        "runtime_mean": float(np.mean(runtimes)) if runtimes else 0.0,
    }


def _native_run_worker(payload):
    vector, seeds, scenario_kwargs = payload
    return _evaluate_native_on_seeds(vector, seeds, scenario_kwargs)


def evaluate_native_runs(vectors, seeds, scenario_kwargs=None, workers=1):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    payloads = [
        ([float(x) for x in vector], [int(s) for s in seeds], scenario_kwargs)
        for vector in vectors
    ]
    if workers <= 1 or len(payloads) <= 1:
        results = [_native_run_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=min(int(workers), len(payloads)),
            mp_context=get_context("spawn"),
        ) as executor:
            results = list(executor.map(_native_run_worker, payloads))

    matrices = {
        metric: np.asarray(
            [
                [float(row[metric]) for row in result["rows"]]
                for result in results
            ],
            dtype=float,
        )
        for metric in METRICS
    }
    return {
        "matrices": matrices,
        "runtime_by_run": [float(result["runtime_mean"]) for result in results],
        "raw_by_run": [result["rows"] for result in results],
    }


def compare_rule_vs_native(rule_eval, native_eval):
    comparison = {}
    for i, metric in enumerate(METRICS):
        rule = rule_eval["matrices"][metric]
        native = native_eval["matrices"][metric]
        stats = paired_hierarchical_bootstrap(
            rule,
            native,
            metric,
            seed=110000 + i,
        )
        comparison[metric] = {
            "native_minus_rule": float(stats["axplorer_minus_local"]),
            "ci95": [float(x) for x in stats["ci95"]],
            "probability_native_better": float(
                stats["probability_axplorer_better"]
            ),
            "paired_training_run_win_rate": float(
                stats["paired_training_run_win_rate"]
            ),
            "paired_scenario_win_rate": float(
                stats["paired_scenario_win_rate"]
            ),
            "paired_sign_flip_pvalue": float(
                paired_sign_flip_pvalue(rule, native, seed=111000 + i)
            ),
        }
    return comparison


def _write_report(path, mode, seeds, fixed, rule, native, comparison):
    s = comparison["asset_survival_rate"]
    lines = [
        "# AegisSwarm Optimizer-Native Objective V2 Report",
        "",
        f"Protocol: `{PROTOCOL_ID}`",
        f"Mode: **{mode}**",
        f"Evaluation scenarios: **{len(seeds)}** ({seeds[0]}–{seeds[-1]})",
        "",
        "This experiment holds simulator, scalar fitness, candidate-evaluation budget,",
        "local/evolutionary search family, and Hungarian execution fixed while changing",
        "the strategic representation searched by the optimizer-aware learner.",
        "",
        "V2 was created after the malformed V1 representation completed development.",
        "Because that full V1 result informed V2 design, V2 uses a fresh development block.",
        "V2 shares the rule-guided policy's structural base utility and searches smooth",
        "state-reactive strategic modifiers.",
        "",
        "## Survival",
        "",
        "| Variant | Survival | 95% CI |",
        "|---|---:|---:|",
        f"| fixed_optimizer | {100*fixed['asset_survival_rate']['mean']:.2f}% | [{100*fixed['asset_survival_rate']['ci95'][0]:.2f}%, {100*fixed['asset_survival_rate']['ci95'][1]:.2f}%] |",
        f"| rule_objective | {100*rule['asset_survival_rate']['mean']:.2f}% | [{100*rule['asset_survival_rate']['ci95'][0]:.2f}%, {100*rule['asset_survival_rate']['ci95'][1]:.2f}%] |",
        f"| native_objective_v2 | {100*native['asset_survival_rate']['mean']:.2f}% | [{100*native['asset_survival_rate']['ci95'][0]:.2f}%, {100*native['asset_survival_rate']['ci95'][1]:.2f}%] |",
        "",
        "## Primary representation ablation",
        "",
        f"- Native V2 minus 60-token rule objective: **{100*s['native_minus_rule']:+.2f} pp**",
        f"- 95% paired hierarchical CI: **[{100*s['ci95'][0]:+.2f}, {100*s['ci95'][1]:+.2f}] pp**",
        f"- Paired sign-flip p-value: **{s['paired_sign_flip_pvalue']:.6f}**",
        "",
    ]
    if mode == "development":
        lines += [
            "Development evidence only. Do not run the reserved V2 confirmation block until",
            "the architecture and hyperparameters are explicitly frozen.",
        ]
    elif mode == "quick_development":
        lines += ["Quick integration/architecture check only; do not treat as evidence."]
    else:
        lines += ["Reserved confirmation result; do not tune on this block afterward."]
    path.write_text("\n".join(lines))


def _evaluate(out_dir, mode, seeds, rule_runs, native_runs, workers):
    rule_programs = [
        np.asarray(run["best_program"], dtype=np.int16)
        for run in rule_runs
    ]
    native_vectors = [
        np.asarray(run["best_objective"], dtype=float)
        for run in native_runs
    ]

    fixed_eval = evaluate_optimizer_only(seeds, SCENARIO_KWARGS)
    rule_eval = evaluate_hybrid_program_runs(
        rule_programs,
        seeds,
        SCENARIO_KWARGS,
        workers=workers,
    )
    native_eval = evaluate_native_runs(
        native_vectors,
        seeds,
        SCENARIO_KWARGS,
        workers=workers,
    )

    fixed_summary = summarize_method(fixed_eval, bootstrap_seed=112000)
    rule_summary = summarize_method(rule_eval, bootstrap_seed=113000)
    native_summary = summarize_method(native_eval, bootstrap_seed=114000)
    comparison = compare_rule_vs_native(rule_eval, native_eval)

    result = {
        "protocol_id": PROTOCOL_ID,
        "mode": mode,
        "evaluation_seeds": [int(x) for x in seeds],
        "fixed_optimizer": fixed_summary,
        "rule_objective": rule_summary,
        "native_objective_v2": native_summary,
        "paired_representation_comparison": comparison,
    }
    _save_json(Path(out_dir) / "results.json", result)
    _write_report(
        Path(out_dir) / "REPORT.md",
        mode,
        seeds,
        fixed_summary,
        rule_summary,
        native_summary,
        comparison,
    )

    s = comparison["asset_survival_rate"]
    print("\n=== OPTIMIZER-NATIVE OBJECTIVE V2 ===", flush=True)
    print(
        f"fixed_optimizer survival: {fixed_summary['asset_survival_rate']['mean']:.3f}",
        flush=True,
    )
    print(
        f"rule_objective survival:  {rule_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={rule_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"native_objective_v2 survival: {native_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={native_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"difference (N-R):         {s['native_minus_rule']:+.4f} CI={s['ci95']}",
        flush=True,
    )
    print(
        f"paired p-value:           {s['paired_sign_flip_pvalue']:.6f}",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result


def run_native_objective_development(
    out_dir="artifacts/optimizer_native_v2_dev",
    workers=4,
    quick=False,
    force_train=False,
):
    out_dir = Path(out_dir)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    if quick:
        search_seeds = QUICK_SEARCH_SEEDS
        train_scenarios = QUICK_TRAIN_SCENARIOS
        budget = QUICK_BUDGET
        population = QUICK_POPULATION
        local_rounds = QUICK_LOCAL_ROUNDS
        eval_seeds = QUICK_EVAL_SEEDS
    else:
        search_seeds = SEARCH_SEEDS
        train_scenarios = TRAIN_SCENARIOS
        budget = ORACLE_BUDGET
        population = POPULATION
        local_rounds = LOCAL_REFINEMENT_ROUNDS
        eval_seeds = NATIVE_OBJECTIVE_V2_DEV_SEEDS

    protocol = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "architecture_frozen": False,
        "search_seeds": [int(x) for x in search_seeds],
        "train_seeds": [int(x) for x in TRAIN_SEEDS[:train_scenarios]],
        "oracle_budget_per_representation_per_run": int(budget),
        "population": int(population),
        "local_refinement_rounds": int(local_rounds),
        "executor": "per-step Hungarian assignment",
        "evaluation_first_seed": int(eval_seeds[0]),
        "evaluation_last_seed": int(eval_seeds[-1]),
        "evaluation_count": int(len(eval_seeds)),
        "workers": int(workers),
        "representation_ablation": [
            "60-token state-reactive rule objective",
            "14-parameter smooth optimizer-native objective V2",
        ],
        "v1_development_diagnosis": (
            "V1 zero-centred utility under-assigned; full V1 development on 9000-9399 was inspected and invalidated"
        ),
    }
    _save_json(out_dir / "protocol.json", protocol)

    print(
        f"AegisSwarm optimizer-native-v2 {'quick' if quick else 'development'} | "
        f"runs={len(search_seeds)} budget={budget} "
        f"train_scenarios={train_scenarios} eval_scenarios={len(eval_seeds)} "
        f"workers={workers}",
        flush=True,
    )

    config = EvalConfig(seeds=TRAIN_SEEDS[:train_scenarios])
    rule_runs = []
    native_runs = []
    for i, search_seed in enumerate(search_seeds, start=1):
        print(
            f"\n=== paired representation run {i}/{len(search_seeds)} seed={search_seed} ===",
            flush=True,
        )
        rule_runs.append(
            _load_or_train(
                runs_dir / f"rule_objective_seed_{search_seed}.json",
                "hybrid_local",
                search_seed,
                train_hybrid_local,
                force=force_train,
                config=config,
                oracle_budget=budget,
                population=population,
                local_refinement_rounds=local_rounds,
                workers=workers,
                verbose=True,
            )
        )
        native_runs.append(
            _load_or_train(
                runs_dir / f"native_v2_objective_seed_{search_seed}.json",
                "optimizer_native_local_v2",
                search_seed,
                train_native_local,
                force=force_train,
                config=config,
                oracle_budget=budget,
                population=population,
                local_refinement_rounds=local_rounds,
                workers=workers,
                verbose=True,
            )
        )

    return _evaluate(
        out_dir,
        "quick_development" if quick else "development",
        eval_seeds,
        rule_runs,
        native_runs,
        workers,
    )


def run_native_objective_confirmation(
    source_dir="artifacts/optimizer_native_v2_dev",
    out_dir="artifacts/optimizer_native_v2_confirm",
    workers=4,
):
    source_dir = Path(source_dir)
    protocol_path = source_dir / "protocol.json"
    if not protocol_path.exists():
        raise FileNotFoundError(f"Missing development protocol: {protocol_path}")
    protocol = json.loads(protocol_path.read_text())
    if not bool(protocol.get("architecture_frozen", False)):
        raise RuntimeError(
            "Optimizer-native V2 architecture is not frozen. Do not consume confirmation seeds. "
            "Review development first, then explicitly set architecture_frozen=true only after a freeze decision."
        )

    runs_dir = source_dir / "runs"
    rule_runs = []
    native_runs = []
    for seed in SEARCH_SEEDS:
        rp = runs_dir / f"rule_objective_seed_{seed}.json"
        npth = runs_dir / f"native_v2_objective_seed_{seed}.json"
        if not rp.exists() or not npth.exists():
            raise FileNotFoundError(
                f"Missing frozen run artifacts for search seed {seed}"
            )
        rule_runs.append(json.loads(rp.read_text()))
        native_runs.append(json.loads(npth.read_text()))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return _evaluate(
        out_dir,
        "confirmation",
        NATIVE_OBJECTIVE_V2_CONFIRM_SEEDS,
        rule_runs,
        native_runs,
        workers,
    )
