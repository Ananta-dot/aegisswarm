from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .final_proof import (
    METRICS,
    evaluate_program_runs,
    paired_hierarchical_bootstrap,
    paired_sign_flip_pvalue,
    summarize_method,
)
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_stats import paired_run_sign_flip_pvalue
from .optimization import HungarianPolicy
from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .splits import HYBRID_DEV_SEEDS


SCENARIO_KWARGS = {
    "n_threats": 30,
    "n_defenders": 8,
    "n_assets": 2,
    "n_sensors": 3,
}


def _evaluate_policy_on_seeds(policy_factory, seeds, scenario_kwargs):
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.get("max_steps", 150)))
    kwargs = dict(scenario_kwargs)
    kwargs.pop("max_steps", None)
    rows = []
    runtimes = []

    for seed in seeds:
        scenario = gen.generate(seed=int(seed), **kwargs)
        started = time.perf_counter()
        metrics = Simulator.evaluate_policy(scenario, policy_factory())
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())

    return {
        "rows": rows,
        "runtime_mean": float(np.mean(runtimes)) if runtimes else 0.0,
    }


def _program_worker(payload):
    mode, program, seeds, scenario_kwargs = payload
    if mode == "hybrid":
        factory = lambda: RuleGuidedHungarianPolicy(program)
    elif mode == "greedy":
        from .rule_program import RuleProgramPolicy
        factory = lambda: RuleProgramPolicy(program)
    else:
        raise ValueError(f"unknown program worker mode: {mode}")
    return _evaluate_policy_on_seeds(factory, seeds, scenario_kwargs)


def _evaluate_programs(mode, programs, seeds, scenario_kwargs=None, workers=1):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    payloads = [
        (mode, [int(x) for x in program], [int(s) for s in seeds], scenario_kwargs)
        for program in programs
    ]

    if workers <= 1 or len(payloads) <= 1:
        results = [_program_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=min(int(workers), len(payloads)),
            mp_context=get_context("spawn"),
        ) as executor:
            results = list(executor.map(_program_worker, payloads))

    matrices = {
        metric: np.asarray(
            [[float(row[metric]) for row in result["rows"]] for result in results],
            dtype=float,
        )
        for metric in METRICS
    }
    return {
        "matrices": matrices,
        "runtime_by_run": [float(result["runtime_mean"]) for result in results],
        "raw_by_run": [result["rows"] for result in results],
    }


def evaluate_hybrid_program_runs(programs, seeds, scenario_kwargs=None, workers=1):
    return _evaluate_programs("hybrid", programs, seeds, scenario_kwargs, workers)


def evaluate_greedy_program_runs(programs, seeds, scenario_kwargs=None, workers=1):
    return _evaluate_programs("greedy", programs, seeds, scenario_kwargs, workers)


def evaluate_optimizer_only(seeds, scenario_kwargs=None):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    result = _evaluate_policy_on_seeds(HungarianPolicy, seeds, scenario_kwargs)
    matrices = {
        metric: np.asarray(
            [[float(row[metric]) for row in result["rows"]]],
            dtype=float,
        )
        for metric in METRICS
    }
    return {
        "matrices": matrices,
        "runtime_by_run": [float(result["runtime_mean"])],
        "raw_by_run": [result["rows"]],
    }


def _paired(first_eval, second_eval, first_name, second_name):
    out = {}
    for i, metric in enumerate(METRICS):
        first = first_eval["matrices"][metric]
        second = second_eval["matrices"][metric]
        stats = paired_hierarchical_bootstrap(
            first,
            second,
            metric,
            seed=94000 + i,
        )
        out[metric] = {
            "first": first_name,
            "second": second_name,
            "second_minus_first": float(stats["axplorer_minus_local"]),
            "ci95": [float(x) for x in stats["ci95"]],
            "probability_second_better": float(stats["probability_axplorer_better"]),
            "paired_training_run_win_rate": float(stats["paired_training_run_win_rate"]),
            "paired_scenario_win_rate": float(stats["paired_scenario_win_rate"]),
            "paired_run_exact_pvalue": float(
                paired_run_sign_flip_pvalue(first, second)
            ),
            "scenario_level_sign_flip_pvalue": float(
                paired_sign_flip_pvalue(first, second, seed=95000 + i)
            ),
        }
    return out


def _load_run_pairs(source_dir):
    runs_dir = Path(source_dir) / "runs"
    local = {}
    v2 = {}

    for path in runs_dir.glob("rule_local_seed_*.json"):
        seed = int(path.stem.rsplit("_", 1)[-1])
        local[seed] = json.loads(path.read_text())
    for path in runs_dir.glob("rule_axplorer_v2_seed_*.json"):
        seed = int(path.stem.rsplit("_", 1)[-1])
        v2[seed] = json.loads(path.read_text())

    seeds = sorted(set(local) & set(v2))
    if not seeds:
        raise FileNotFoundError(
            f"No paired local/V2 run artifacts found under {runs_dir}."
        )

    local_programs = [np.asarray(local[s]["best_program"], dtype=np.int16) for s in seeds]
    v2_programs = [np.asarray(v2[s]["best_program"], dtype=np.int16) for s in seeds]
    return seeds, local_programs, v2_programs


def _summary(eval_result, seed):
    return summarize_method(eval_result, bootstrap_seed=seed)


def _write_report(path, eval_seeds, run_seeds, summaries, comparisons):
    def pct(x):
        return f"{100.0 * x:.2f}%"

    lines = [
        "# AegisSwarm Hybrid Execution Ablation",
        "",
        f"Evaluation scenarios: **{len(eval_seeds)}** ({eval_seeds[0]}–{eval_seeds[-1]})",
        f"Paired discovered strategies: **{len(run_seeds)}**",
        "",
        "This experiment changes execution while holding discovered strategy programs fixed.",
        "The hybrid executor uses rule/model-derived utilities and reserve intent, then solves",
        "the immediate one-to-one assignment globally with a Hungarian optimizer.",
        "",
        "Statistical interpretation: the paired hierarchical bootstrap CI is primary.",
        "The exact paired-run permutation p-value treats independently trained policies as",
        "the experimental unit. The scenario-level sign-flip value is retained only as a",
        "secondary repeated-measures diagnostic.",
        "",
        "## Survival",
        "",
        "| Variant | Survival | 95% CI |",
        "|---|---:|---:|",
    ]

    for name in (
        "optimizer_only",
        "local_greedy",
        "local_hybrid",
        "v2_greedy",
        "v2_hybrid",
    ):
        stats = summaries[name]["asset_survival_rate"]
        lines.append(
            f"| {name} | {pct(stats['mean'])} | "
            f"[{pct(stats['ci95'][0])}, {pct(stats['ci95'][1])}] |"
        )

    lines += ["", "## Key ablations", ""]
    for key, label in (
        ("optimizer_on_local", "Optimizer effect on local-search strategy"),
        ("optimizer_on_v2", "Optimizer effect on V2 strategy"),
        ("v2_under_greedy", "V2 strategy effect under greedy execution"),
        ("v2_under_hybrid", "V2 strategy effect under optimized execution"),
    ):
        s = comparisons[key]["asset_survival_rate"]
        lines += [
            f"### {label}",
            "",
            f"- Difference: **{100.0 * s['second_minus_first']:+.2f} pp**",
            f"- 95% paired hierarchical bootstrap CI: **[{100.0 * s['ci95'][0]:+.2f}, {100.0 * s['ci95'][1]:+.2f}] pp**",
            f"- Exact paired-run permutation p-value: **{s['paired_run_exact_pvalue']:.6f}**",
            f"- Scenario-level sign-flip p-value (secondary): **{s['scenario_level_sign_flip_pvalue']:.6f}**",
            "",
        ]

    path.write_text("\n".join(lines))


def run_hybrid_ablation(
    source_dir="artifacts/axplorer_v2_dev",
    out_dir="artifacts/hybrid_ablation",
    workers=4,
    quick=False,
):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_seeds, local_programs, v2_programs = _load_run_pairs(source_dir)
    eval_seeds = tuple(HYBRID_DEV_SEEDS[:20]) if quick else HYBRID_DEV_SEEDS

    print(
        f"AegisSwarm hybrid ablation | paired_runs={len(run_seeds)} "
        f"scenarios={len(eval_seeds)} workers={workers}",
        flush=True,
    )

    optimizer_only = evaluate_optimizer_only(eval_seeds)
    local_greedy = evaluate_greedy_program_runs(
        local_programs,
        eval_seeds,
        SCENARIO_KWARGS,
        workers=workers,
    )
    local_hybrid = evaluate_hybrid_program_runs(
        local_programs,
        eval_seeds,
        SCENARIO_KWARGS,
        workers=workers,
    )
    v2_greedy = evaluate_greedy_program_runs(
        v2_programs,
        eval_seeds,
        SCENARIO_KWARGS,
        workers=workers,
    )
    v2_hybrid = evaluate_hybrid_program_runs(
        v2_programs,
        eval_seeds,
        SCENARIO_KWARGS,
        workers=workers,
    )

    evaluations = {
        "optimizer_only": optimizer_only,
        "local_greedy": local_greedy,
        "local_hybrid": local_hybrid,
        "v2_greedy": v2_greedy,
        "v2_hybrid": v2_hybrid,
    }
    summaries = {
        name: _summary(value, 96000 + i * 100)
        for i, (name, value) in enumerate(evaluations.items())
    }
    comparisons = {
        "optimizer_on_local": _paired(
            local_greedy, local_hybrid, "local_greedy", "local_hybrid"
        ),
        "optimizer_on_v2": _paired(
            v2_greedy, v2_hybrid, "v2_greedy", "v2_hybrid"
        ),
        "v2_under_greedy": _paired(
            local_greedy, v2_greedy, "local_greedy", "v2_greedy"
        ),
        "v2_under_hybrid": _paired(
            local_hybrid, v2_hybrid, "local_hybrid", "v2_hybrid"
        ),
    }

    result = {
        "source_dir": str(source_dir),
        "run_seeds": [int(x) for x in run_seeds],
        "evaluation_seeds": [int(x) for x in eval_seeds],
        "summaries": summaries,
        "comparisons": comparisons,
    }
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))
    _write_report(
        out_dir / "REPORT.md",
        eval_seeds,
        run_seeds,
        summaries,
        comparisons,
    )

    print("\n=== HYBRID EXECUTION ABLATION ===", flush=True)
    for name in (
        "optimizer_only",
        "local_greedy",
        "local_hybrid",
        "v2_greedy",
        "v2_hybrid",
    ):
        m = summaries[name]["asset_survival_rate"]["mean"]
        print(f"{name:18s} survival={m:.3f}", flush=True)

    opt = comparisons["optimizer_on_v2"]["asset_survival_rate"]
    strat = comparisons["v2_under_hybrid"]["asset_survival_rate"]
    print(
        f"optimizer effect on V2: {opt['second_minus_first']:+.4f} "
        f"CI={opt['ci95']} run-p={opt['paired_run_exact_pvalue']:.6f} "
        f"scenario-p={opt['scenario_level_sign_flip_pvalue']:.6f}",
        flush=True,
    )
    print(
        f"V2 strategy effect with optimizer: {strat['second_minus_first']:+.4f} "
        f"CI={strat['ci95']} run-p={strat['paired_run_exact_pvalue']:.6f} "
        f"scenario-p={strat['scenario_level_sign_flip_pvalue']:.6f}",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
