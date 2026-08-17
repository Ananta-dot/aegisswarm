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
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS, evaluate_optimizer_only
from .rolling_horizon import RuleGuidedRollingHorizonPolicy
from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .splits import PLANNING_DEV_SEEDS


PROTOCOL_ID = "aegisswarm-rolling-horizon-screen-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
SEARCH_SEEDS = (44001, 44002, 44003, 44004, 44005)
QUICK_EVAL_SEEDS = tuple(PLANNING_DEV_SEEDS[:20])


def _evaluate_policy_on_seeds(tokens, seeds, scenario_kwargs, mode, horizon, discount, time_limit):
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.get("max_steps", 150)))
    kwargs = dict(scenario_kwargs)
    kwargs.pop("max_steps", None)
    rows = []
    runtimes = []

    for seed in seeds:
        scenario = gen.generate(seed=int(seed), **kwargs)
        if mode == "one_step":
            policy = RuleGuidedHungarianPolicy(tokens)
        elif mode == "rolling":
            policy = RuleGuidedRollingHorizonPolicy(
                tokens,
                horizon=horizon,
                discount=discount,
                time_limit_seconds=time_limit,
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")

        started = time.perf_counter()
        metrics = Simulator.evaluate_policy(scenario, policy)
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())

    return {
        "rows": rows,
        "runtime_mean": float(np.mean(runtimes)) if runtimes else 0.0,
    }


def _eval_worker(payload):
    return _evaluate_policy_on_seeds(*payload)


def evaluate_programs(programs, seeds, mode, workers, horizon=4, discount=0.90, time_limit=0.25):
    payloads = [
        (
            [int(x) for x in program],
            [int(s) for s in seeds],
            dict(SCENARIO_KWARGS),
            mode,
            int(horizon),
            float(discount),
            float(time_limit),
        )
        for program in programs
    ]

    if workers <= 1 or len(payloads) <= 1:
        results = [_eval_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=min(int(workers), len(payloads)),
            mp_context=get_context("spawn"),
        ) as executor:
            results = list(executor.map(_eval_worker, payloads))

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


def compare_one_step_vs_rolling(one_step, rolling):
    comparison = {}
    for i, metric in enumerate(METRICS):
        a = one_step["matrices"][metric]
        b = rolling["matrices"][metric]
        stats = paired_hierarchical_bootstrap(a, b, metric, seed=130000 + i)
        comparison[metric] = {
            "rolling_minus_one_step": float(stats["axplorer_minus_local"]),
            "ci95": [float(x) for x in stats["ci95"]],
            "probability_rolling_better": float(stats["probability_axplorer_better"]),
            "paired_training_run_win_rate": float(stats["paired_training_run_win_rate"]),
            "paired_scenario_win_rate": float(stats["paired_scenario_win_rate"]),
            "paired_sign_flip_pvalue": float(
                paired_sign_flip_pvalue(a, b, seed=131000 + i)
            ),
        }
    return comparison


def load_rule_programs(source_dir=DEFAULT_SOURCE_DIR):
    source_dir = Path(source_dir)
    runs_dir = source_dir / "runs"
    programs = []
    for seed in SEARCH_SEEDS:
        path = runs_dir / f"rule_objective_seed_{seed}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing incumbent rule artifact: {path}. "
                "Run optimizer-native V2 development first or pass --source-dir."
            )
        data = json.loads(path.read_text())
        if data.get("method") != "hybrid_local":
            raise ValueError(f"Unexpected rule artifact method in {path}: {data.get('method')}")
        programs.append(np.asarray(data["best_program"], dtype=np.int16))
    return programs


def run_planning_screen(
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/rolling_horizon_quick",
    workers=4,
    quick=True,
    horizon=4,
    discount=0.90,
    time_limit=0.25,
):
    seeds = QUICK_EVAL_SEEDS if quick else PLANNING_DEV_SEEDS
    programs = load_rule_programs(source_dir)

    print(
        f"AegisSwarm rolling-horizon screen | programs={len(programs)} "
        f"scenarios={len(seeds)} horizon={horizon} workers={workers}",
        flush=True,
    )

    fixed_eval = evaluate_optimizer_only(seeds, SCENARIO_KWARGS)
    one_step_eval = evaluate_programs(
        programs, seeds, "one_step", workers,
        horizon=horizon, discount=discount, time_limit=time_limit,
    )
    rolling_eval = evaluate_programs(
        programs, seeds, "rolling", workers,
        horizon=horizon, discount=discount, time_limit=time_limit,
    )

    fixed = summarize_method(fixed_eval, bootstrap_seed=132000)
    one_step = summarize_method(one_step_eval, bootstrap_seed=133000)
    rolling = summarize_method(rolling_eval, bootstrap_seed=134000)
    comparison = compare_one_step_vs_rolling(one_step_eval, rolling_eval)

    result = {
        "protocol_id": PROTOCOL_ID,
        "mode": "quick_development" if quick else "development_screen",
        "source_dir": str(source_dir),
        "evaluation_seeds": [int(x) for x in seeds],
        "horizon": int(horizon),
        "discount": float(discount),
        "solver_time_limit_seconds": float(time_limit),
        "fixed_optimizer": fixed,
        "rule_one_step": one_step,
        "rule_rolling_horizon": rolling,
        "paired_comparison": comparison,
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))

    s = comparison["asset_survival_rate"]
    report = [
        "# AegisSwarm Rolling-Horizon Screening Report",
        "",
        f"Protocol: `{PROTOCOL_ID}`",
        f"Mode: {'quick development' if quick else 'development screen'}",
        f"Scenarios: {len(seeds)} ({seeds[0]}–{seeds[-1]})",
        f"Horizon: {horizon}",
        "",
        "This screen holds the already-discovered 60-token strategies fixed and changes only",
        "execution from one-step Hungarian assignment to short rolling-horizon planning.",
        "It is a screening ablation, not final evidence for a planning-aware trained system.",
        "",
        f"- fixed optimizer survival: {fixed['asset_survival_rate']['mean']:.4f}",
        f"- rule + one-step survival: {one_step['asset_survival_rate']['mean']:.4f}",
        f"- rule + rolling survival: {rolling['asset_survival_rate']['mean']:.4f}",
        f"- rolling - one-step: {s['rolling_minus_one_step']:+.4f}",
        f"- paired 95% CI: {s['ci95']}",
        f"- paired p-value: {s['paired_sign_flip_pvalue']:.6f}",
        f"- one-step runtime mean: {one_step['runtime_seconds']['mean']:.6f}s/scenario",
        f"- rolling runtime mean: {rolling['runtime_seconds']['mean']:.6f}s/scenario",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== ROLLING-HORIZON SCREEN ===", flush=True)
    print(f"fixed_optimizer survival: {fixed['asset_survival_rate']['mean']:.3f}", flush=True)
    print(
        f"rule_one_step survival:   {one_step['asset_survival_rate']['mean']:.3f} "
        f"CI={one_step['asset_survival_rate']['ci95']}", flush=True,
    )
    print(
        f"rule_rolling survival:    {rolling['asset_survival_rate']['mean']:.3f} "
        f"CI={rolling['asset_survival_rate']['ci95']}", flush=True,
    )
    print(
        f"difference (R-O):         {s['rolling_minus_one_step']:+.4f} "
        f"CI={s['ci95']}", flush=True,
    )
    print(f"paired p-value:           {s['paired_sign_flip_pvalue']:.6f}", flush=True)
    print(
        f"runtime one-step/rolling: {one_step['runtime_seconds']['mean']:.4f}s / "
        f"{rolling['runtime_seconds']['mean']:.4f}s",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
