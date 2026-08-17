from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .evidence_hardening import load_incumbent_programs
from .final_proof import METRICS, paired_hierarchical_bootstrap, summarize_method
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS
from .reliability import (
    ReliabilityAwareBackupPolicy,
    ReliabilityWeightedHungarianPolicy,
)
from .scenarios import ScenarioGenerator
from .simulator_v2 import SimulatorV2
from .splits import RELIABILITY_DEV_SEEDS


PROTOCOL_ID = "aegisswarm-reliability-aware-screen-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
QUICK_EVAL_SEEDS = tuple(RELIABILITY_DEV_SEEDS[:20])


def _policy_factory(mode, program):
    if mode == "incumbent":
        return RuleGuidedHungarianPolicy(program)
    if mode == "weighted":
        return ReliabilityWeightedHungarianPolicy(program)
    if mode == "backup":
        return ReliabilityAwareBackupPolicy(program)
    raise ValueError(f"Unknown reliability mode: {mode}")


def _evaluate_worker(payload):
    mode, program, seeds, scenario_kwargs = payload
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.get("max_steps", 150)))
    kwargs = dict(scenario_kwargs)
    kwargs.pop("max_steps", None)

    rows = []
    diagnostics = []
    runtimes = []
    for seed in seeds:
        scenario = gen.generate(seed=int(seed), **kwargs)
        policy = _policy_factory(mode, program)
        started = time.perf_counter()
        metrics, diag = SimulatorV2.evaluate_policy_with_diagnostics(scenario, policy)
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())
        diagnostics.append(diag)

    return {
        "rows": rows,
        "diagnostics": diagnostics,
        "runtime_mean": float(np.mean(runtimes)) if runtimes else 0.0,
    }


def evaluate_programs(mode, programs, seeds, workers=1, scenario_kwargs=None):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    payloads = [
        (
            mode,
            [int(x) for x in program],
            [int(s) for s in seeds],
            scenario_kwargs,
        )
        for program in programs
    ]

    if workers <= 1 or len(payloads) <= 1:
        results = [_evaluate_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=min(int(workers), len(payloads)),
            mp_context=get_context("spawn"),
        ) as executor:
            results = list(executor.map(_evaluate_worker, payloads))

    return {
        "matrices": {
            metric: np.asarray(
                [[float(row[metric]) for row in result["rows"]] for result in results],
                dtype=float,
            )
            for metric in METRICS
        },
        "runtime_by_run": [float(result["runtime_mean"]) for result in results],
        "raw_by_run": [result["rows"] for result in results],
        "diagnostics_by_run": [result["diagnostics"] for result in results],
    }


def _compare(first_eval, second_eval, seed_base):
    comparison = {}
    for i, metric in enumerate(METRICS):
        stats = paired_hierarchical_bootstrap(
            first_eval["matrices"][metric],
            second_eval["matrices"][metric],
            metric,
            seed=seed_base + i,
        )
        comparison[metric] = {
            "second_minus_first": float(stats["axplorer_minus_local"]),
            "ci95": [float(x) for x in stats["ci95"]],
            "probability_second_better": float(stats["probability_axplorer_better"]),
            "paired_training_run_win_rate": float(stats["paired_training_run_win_rate"]),
            "paired_scenario_win_rate": float(stats["paired_scenario_win_rate"]),
        }
    return comparison


def _per_program_delta(first_eval, second_eval, metric="asset_survival_rate"):
    first = first_eval["matrices"][metric]
    second = second_eval["matrices"][metric]
    return [float(x) for x in (second - first).mean(axis=1)]


def _diagnostic_mean(evaluation, key):
    values = [
        float(diag.get(key, 0.0))
        for run in evaluation.get("diagnostics_by_run", [])
        for diag in run
    ]
    return float(np.mean(values)) if values else 0.0


def run_reliability_screen(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/reliability_aware_quick",
    workers=5,
    quick=True,
):
    seeds = QUICK_EVAL_SEEDS if quick else RELIABILITY_DEV_SEEDS
    programs = load_incumbent_programs(source_dir)

    print(
        f"AegisSwarm reliability-aware screen | programs={len(programs)} "
        f"scenarios={len(seeds)} simulator=v2-indexed workers={workers}",
        flush=True,
    )

    incumbent = evaluate_programs("incumbent", programs, seeds, workers=workers)
    weighted = evaluate_programs("weighted", programs, seeds, workers=workers)
    backup = evaluate_programs("backup", programs, seeds, workers=workers)

    summaries = {
        "incumbent": summarize_method(incumbent, 190100),
        "reliability_weighted": summarize_method(weighted, 190200),
        "reliability_backup": summarize_method(backup, 190300),
    }
    weighted_vs_incumbent = _compare(incumbent, weighted, 191000)
    backup_vs_incumbent = _compare(incumbent, backup, 192000)
    backup_vs_weighted = _compare(weighted, backup, 193000)

    result = {
        "protocol_id": PROTOCOL_ID,
        "mode": "quick_development" if quick else "development_screen",
        "source_dir": str(source_dir),
        "evaluation_seeds": [int(x) for x in seeds],
        "simulator": "SimulatorV2 indexed event randomness",
        "summaries": summaries,
        "weighted_vs_incumbent": weighted_vs_incumbent,
        "backup_vs_incumbent": backup_vs_incumbent,
        "backup_vs_weighted": backup_vs_weighted,
        "per_program_survival_delta_weighted_minus_incumbent": _per_program_delta(
            incumbent, weighted
        ),
        "per_program_survival_delta_backup_minus_incumbent": _per_program_delta(
            incumbent, backup
        ),
        "diagnostics": {
            "incumbent_real_interaction_failures_mean": _diagnostic_mean(
                incumbent, "real_interaction_failures"
            ),
            "weighted_real_interaction_failures_mean": _diagnostic_mean(
                weighted, "real_interaction_failures"
            ),
            "backup_real_interaction_failures_mean": _diagnostic_mean(
                backup, "real_interaction_failures"
            ),
            "incumbent_resource_exhausted_fraction": _diagnostic_mean(
                incumbent, "resource_exhausted"
            ),
            "weighted_resource_exhausted_fraction": _diagnostic_mean(
                weighted, "resource_exhausted"
            ),
            "backup_resource_exhausted_fraction": _diagnostic_mean(
                backup, "resource_exhausted"
            ),
        },
        "notes": [
            "All three variants use the same five frozen 60-token programs.",
            "Weighted mode preserves one-to-one Hungarian assignment and changes only pair scoring.",
            "Backup mode permits at most one contingent backup per threat under existing SimulatorV2 sequential resolution semantics.",
            "No strategy is retrained in this screen.",
        ],
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))

    def survival(name):
        return summaries[name]["asset_survival_rate"]["mean"]

    wi = weighted_vs_incumbent["asset_survival_rate"]
    bi = backup_vs_incumbent["asset_survival_rate"]
    bw = backup_vs_weighted["asset_survival_rate"]

    report = [
        "# AegisSwarm Reliability-Aware Assignment Screen",
        "",
        f"Protocol: `{PROTOCOL_ID}`",
        f"Mode: {'quick development' if quick else 'development screen'}",
        f"Scenarios: {len(seeds)} ({seeds[0]}–{seeds[-1]})",
        "",
        f"- incumbent survival: {survival('incumbent'):.4f}",
        f"- reliability-weighted survival: {survival('reliability_weighted'):.4f}",
        f"- contingent-backup survival: {survival('reliability_backup'):.4f}",
        f"- weighted - incumbent: {wi['second_minus_first']:+.4f}, CI={wi['ci95']}",
        f"- backup - incumbent: {bi['second_minus_first']:+.4f}, CI={bi['ci95']}",
        f"- backup - weighted: {bw['second_minus_first']:+.4f}, CI={bw['ci95']}",
        "",
        "This is an executor screen with frozen strategies, not a trained reliability-aware policy.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== RELIABILITY-AWARE ASSIGNMENT SCREEN ===", flush=True)
    print(f"incumbent survival:               {survival('incumbent'):.3f}", flush=True)
    print(
        f"reliability-weighted survival:    {survival('reliability_weighted'):.3f}",
        flush=True,
    )
    print(
        f"contingent-backup survival:       {survival('reliability_backup'):.3f}",
        flush=True,
    )
    print(
        f"weighted - incumbent:            {wi['second_minus_first']:+.4f} CI={wi['ci95']}",
        flush=True,
    )
    print(
        f"backup - incumbent:              {bi['second_minus_first']:+.4f} CI={bi['ci95']}",
        flush=True,
    )
    print(
        f"backup - weighted:               {bw['second_minus_first']:+.4f} CI={bw['ci95']}",
        flush=True,
    )
    print(
        "per-program weighted deltas:     "
        f"{result['per_program_survival_delta_weighted_minus_incumbent']}",
        flush=True,
    )
    print(
        "per-program backup deltas:       "
        f"{result['per_program_survival_delta_backup_minus_incumbent']}",
        flush=True,
    )
    print(
        "resources consumed inc/wgt/bak:  "
        f"{summaries['incumbent']['defenders_consumed']['mean']:.3f} / "
        f"{summaries['reliability_weighted']['defenders_consumed']['mean']:.3f} / "
        f"{summaries['reliability_backup']['defenders_consumed']['mean']:.3f}",
        flush=True,
    )
    print(
        "interaction failures inc/wgt/bak: "
        f"{result['diagnostics']['incumbent_real_interaction_failures_mean']:.3f} / "
        f"{result['diagnostics']['weighted_real_interaction_failures_mean']:.3f} / "
        f"{result['diagnostics']['backup_real_interaction_failures_mean']:.3f}",
        flush=True,
    )
    print(
        "runtime inc/wgt/bak:             "
        f"{summaries['incumbent']['runtime_seconds']['mean']:.4f}s / "
        f"{summaries['reliability_weighted']['runtime_seconds']['mean']:.4f}s / "
        f"{summaries['reliability_backup']['runtime_seconds']['mean']:.4f}s",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
