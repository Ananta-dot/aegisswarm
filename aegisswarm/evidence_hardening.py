from __future__ import annotations

import json
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .final_proof import METRICS, paired_hierarchical_bootstrap, summarize_method
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS, evaluate_hybrid_program_runs
from .optimization import HungarianPolicy
from .scenarios import ScenarioGenerator
from .simulator_v2 import SimulatorV2
from .splits import EVIDENCE_DEV_SEEDS


PROTOCOL_ID = "aegisswarm-evidence-hardening-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
SEARCH_SEEDS = (44001, 44002, 44003, 44004, 44005)
QUICK_EVAL_SEEDS = tuple(EVIDENCE_DEV_SEEDS[:20])


def load_incumbent_programs(source_dir=DEFAULT_SOURCE_DIR):
    runs_dir = Path(source_dir) / "runs"
    programs = []
    for seed in SEARCH_SEEDS:
        path = runs_dir / f"rule_objective_seed_{seed}.json"
        if not path.exists():
            raise FileNotFoundError(
                f"Missing incumbent artifact: {path}. "
                "Run optimizer-native V2 development first or pass --source-dir."
            )
        data = json.loads(path.read_text())
        if data.get("method") != "hybrid_local":
            raise ValueError(
                f"Unexpected incumbent artifact method in {path}: {data.get('method')}"
            )
        programs.append(np.asarray(data["best_program"], dtype=np.int16))
    return programs


def _evaluate_program_v2_worker(payload):
    program, seeds, scenario_kwargs, perfect_sensing, deterministic_interactions = payload
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.get("max_steps", 150)))
    kwargs = dict(scenario_kwargs)
    kwargs.pop("max_steps", None)

    rows = []
    diagnostics = []
    runtimes = []
    for seed in seeds:
        scenario = gen.generate(seed=int(seed), **kwargs)
        policy = RuleGuidedHungarianPolicy(program)
        started = time.perf_counter()
        metrics, diag = SimulatorV2.evaluate_policy_with_diagnostics(
            scenario,
            policy,
            perfect_sensing=perfect_sensing,
            deterministic_interactions=deterministic_interactions,
        )
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())
        diagnostics.append(diag)

    return {
        "rows": rows,
        "diagnostics": diagnostics,
        "runtime_mean": float(np.mean(runtimes)) if runtimes else 0.0,
    }


def evaluate_programs_v2(
    programs,
    seeds,
    *,
    workers=1,
    perfect_sensing=False,
    deterministic_interactions=False,
    scenario_kwargs=None,
):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    payloads = [
        (
            [int(x) for x in program],
            [int(s) for s in seeds],
            scenario_kwargs,
            bool(perfect_sensing),
            bool(deterministic_interactions),
        )
        for program in programs
    ]

    if workers <= 1 or len(payloads) <= 1:
        results = [_evaluate_program_v2_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=min(int(workers), len(payloads)),
            mp_context=get_context("spawn"),
        ) as executor:
            results = list(executor.map(_evaluate_program_v2_worker, payloads))

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
        "diagnostics_by_run": [result["diagnostics"] for result in results],
    }


def evaluate_fixed_optimizer_v2(seeds, scenario_kwargs=None):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    gen = ScenarioGenerator(max_steps=int(scenario_kwargs.get("max_steps", 150)))
    kwargs = dict(scenario_kwargs)
    kwargs.pop("max_steps", None)
    rows = []
    runtimes = []

    for seed in seeds:
        scenario = gen.generate(seed=int(seed), **kwargs)
        started = time.perf_counter()
        metrics = SimulatorV2.evaluate_policy(scenario, HungarianPolicy())
        runtimes.append(time.perf_counter() - started)
        rows.append(metrics.as_dict())

    return {
        "matrices": {
            metric: np.asarray([[float(row[metric]) for row in rows]], dtype=float)
            for metric in METRICS
        },
        "runtime_by_run": [float(np.mean(runtimes)) if runtimes else 0.0],
        "raw_by_run": [rows],
    }


def _oracle_sort_key(row):
    return (
        float(row["asset_survival_rate"]),
        float(row["containment_rate"]),
        -float(row["cumulative_damage"]),
        -float(row["penetrations"]),
        -float(row["defenders_consumed"]),
        -float(row["mean_response_delay"]),
    )


def best_of_programs_oracle(normal_eval):
    """Non-deployable per-scenario oracle over the five frozen programs.

    This is a diagnostic of policy-class/selection headroom. It must never be
    described as a deployable policy or evaluated on a confirmation set after
    being used to design a selector.
    """

    raw = normal_eval["raw_by_run"]
    n_scenarios = len(raw[0]) if raw else 0
    chosen_rows = []
    chosen_runs = []
    for j in range(n_scenarios):
        candidates = [(i, raw[i][j]) for i in range(len(raw))]
        best_i, best_row = max(candidates, key=lambda item: _oracle_sort_key(item[1]))
        chosen_rows.append(dict(best_row))
        chosen_runs.append(int(best_i))

    evaluation = {
        "matrices": {
            metric: np.asarray(
                [[float(row[metric]) for row in chosen_rows]],
                dtype=float,
            )
            for metric in METRICS
        },
        "runtime_by_run": [0.0],
        "raw_by_run": [chosen_rows],
    }
    return evaluation, chosen_runs


def _paired_headroom(normal_eval, relaxed_eval, seed_base):
    out = {}
    for i, metric in enumerate(METRICS):
        stats = paired_hierarchical_bootstrap(
            normal_eval["matrices"][metric],
            relaxed_eval["matrices"][metric],
            metric,
            seed=seed_base + i,
        )
        out[metric] = {
            "relaxed_minus_normal": float(stats["axplorer_minus_local"]),
            "ci95": [float(x) for x in stats["ci95"]],
            "probability_relaxed_better": float(stats["probability_axplorer_better"]),
            "paired_training_run_win_rate": float(stats["paired_training_run_win_rate"]),
            "paired_scenario_win_rate": float(stats["paired_scenario_win_rate"]),
        }
    return out


def _aggregate_diagnostics(normal_eval):
    flattened = [
        diag
        for run in normal_eval.get("diagnostics_by_run", [])
        for diag in run
    ]
    if not flattened:
        return {}

    numeric_keys = [
        key
        for key, value in flattened[0].items()
        if isinstance(value, (int, float, bool, np.integer, np.floating))
    ]
    return {
        key: float(np.mean([float(diag.get(key, 0.0)) for diag in flattened]))
        for key in numeric_keys
    }


def failure_attribution(normal_eval, sensing_eval, interaction_eval, combined_eval, oracle_eval):
    """Heuristic development-only attribution for episodes with asset loss.

    Counterfactual relaxations are used first because they are easier to defend
    than inferring internal policy intent. Residual cases are labeled from direct
    simulator diagnostics and remain descriptive, not causal proof.
    """

    categories = Counter()
    failed_episodes = 0
    raw = normal_eval["raw_by_run"]
    sensing = sensing_eval["raw_by_run"]
    interaction = interaction_eval["raw_by_run"]
    combined = combined_eval["raw_by_run"]
    diagnostics = normal_eval["diagnostics_by_run"]
    oracle_rows = oracle_eval["raw_by_run"][0]

    for i in range(len(raw)):
        for j in range(len(raw[i])):
            normal_survival = float(raw[i][j]["asset_survival_rate"])
            if normal_survival >= 1.0:
                continue
            failed_episodes += 1

            sensing_better = float(sensing[i][j]["asset_survival_rate"]) > normal_survival
            interaction_better = (
                float(interaction[i][j]["asset_survival_rate"]) > normal_survival
            )
            combined_better = (
                float(combined[i][j]["asset_survival_rate"]) > normal_survival
            )
            oracle_better = (
                float(oracle_rows[j]["asset_survival_rate"]) > normal_survival
            )

            if sensing_better and not interaction_better:
                category = "sensing_limited"
            elif interaction_better and not sensing_better:
                category = "interaction_stochasticity"
            elif sensing_better and interaction_better:
                category = "multiple_relaxations_help"
            elif combined_better:
                category = "compound_sensing_interaction"
            elif oracle_better:
                category = "strategy_selection_headroom"
            else:
                diag = diagnostics[i][j]
                if (
                    diag.get("resource_exhausted", False)
                    and diag.get("decoy_resource_uses", 0) > 0
                ):
                    category = "decoy_resource_waste"
                elif (
                    diag.get("penetrations_in_range_no_resource", 0) > 0
                    or diag.get("resource_exhausted", False)
                ):
                    category = "resource_exhaustion"
                elif diag.get("penetrations_undetected", 0) > 0:
                    category = "late_detection_residual"
                elif diag.get("real_interaction_failures", 0) > 0:
                    category = "interaction_failure_residual"
                elif diag.get("overload_steps", 0) > 0:
                    category = "simultaneous_overload"
                elif diag.get("penetrations_no_in_range_defender", 0) > 0:
                    category = "reachability"
                else:
                    category = "priority_or_coordination_residual"

            categories[category] += 1

    return {
        "failed_program_scenario_episodes": int(failed_episodes),
        "counts": {key: int(value) for key, value in categories.most_common()},
        "fractions": {
            key: float(value / failed_episodes) if failed_episodes else 0.0
            for key, value in categories.most_common()
        },
    }


def run_evidence_hardening(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/evidence_hardening_quick",
    workers=5,
    quick=True,
):
    seeds = QUICK_EVAL_SEEDS if quick else EVIDENCE_DEV_SEEDS
    programs = load_incumbent_programs(source_dir)

    print(
        f"AegisSwarm evidence hardening | programs={len(programs)} "
        f"scenarios={len(seeds)} simulator=v2-indexed workers={workers}",
        flush=True,
    )

    # Legacy reference is descriptive only: random realization semantics differ.
    legacy = evaluate_hybrid_program_runs(
        programs,
        seeds,
        scenario_kwargs=SCENARIO_KWARGS,
        workers=workers,
    )
    fixed_v2 = evaluate_fixed_optimizer_v2(seeds, SCENARIO_KWARGS)
    normal = evaluate_programs_v2(programs, seeds, workers=workers)
    perfect_sensing = evaluate_programs_v2(
        programs,
        seeds,
        workers=workers,
        perfect_sensing=True,
    )
    deterministic_interactions = evaluate_programs_v2(
        programs,
        seeds,
        workers=workers,
        deterministic_interactions=True,
    )
    combined = evaluate_programs_v2(
        programs,
        seeds,
        workers=workers,
        perfect_sensing=True,
        deterministic_interactions=True,
    )
    oracle, oracle_choices = best_of_programs_oracle(normal)

    summaries = {
        "legacy_incumbent_reference": summarize_method(legacy, 170100),
        "fixed_optimizer_v2": summarize_method(fixed_v2, 170200),
        "incumbent_v2_normal": summarize_method(normal, 170300),
        "incumbent_v2_perfect_sensing": summarize_method(perfect_sensing, 170400),
        "incumbent_v2_deterministic_interactions": summarize_method(
            deterministic_interactions, 170500
        ),
        "incumbent_v2_combined_relaxation": summarize_method(combined, 170600),
        "best_of_5_oracle_v2": summarize_method(oracle, 170700),
    }
    headroom = {
        "perfect_sensing": _paired_headroom(normal, perfect_sensing, 171000),
        "deterministic_interactions": _paired_headroom(
            normal, deterministic_interactions, 172000
        ),
        "combined_relaxation": _paired_headroom(normal, combined, 173000),
    }
    attribution = failure_attribution(
        normal,
        perfect_sensing,
        deterministic_interactions,
        combined,
        oracle,
    )

    result = {
        "protocol_id": PROTOCOL_ID,
        "mode": "quick_development" if quick else "development",
        "source_dir": str(source_dir),
        "evaluation_seeds": [int(x) for x in seeds],
        "simulator": "SimulatorV2 indexed event randomness",
        "summaries": summaries,
        "headroom": headroom,
        "best_of_5_oracle_choices": oracle_choices,
        "normal_v2_diagnostics_mean": _aggregate_diagnostics(normal),
        "failure_attribution": attribution,
        "notes": [
            "Legacy and SimulatorV2 results use different stochastic semantics and are not one formal paired claim.",
            "Perfect sensing and deterministic interactions are diagnostic relaxations, not deployable assumptions or mathematical upper bounds.",
            "Best-of-5 is a non-deployable per-scenario oracle diagnostic.",
        ],
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))

    def survival(name):
        return summaries[name]["asset_survival_rate"]["mean"]

    report = [
        "# AegisSwarm Evidence Hardening / Headroom Report",
        "",
        f"Protocol: `{PROTOCOL_ID}`",
        f"Mode: {'quick development' if quick else 'development'}",
        f"Scenarios: {len(seeds)} ({seeds[0]}–{seeds[-1]})",
        "",
        "## Survival diagnostics",
        "",
        f"- legacy incumbent reference: {survival('legacy_incumbent_reference'):.4f}",
        f"- fixed optimizer v2: {survival('fixed_optimizer_v2'):.4f}",
        f"- incumbent v2 normal: {survival('incumbent_v2_normal'):.4f}",
        f"- perfect sensing diagnostic: {survival('incumbent_v2_perfect_sensing'):.4f}",
        f"- deterministic interaction diagnostic: {survival('incumbent_v2_deterministic_interactions'):.4f}",
        f"- combined diagnostic: {survival('incumbent_v2_combined_relaxation'):.4f}",
        f"- best-of-5 per-scenario oracle: {survival('best_of_5_oracle_v2'):.4f}",
        "",
        "These relaxations are diagnostics, not deployable assumptions or mathematical upper bounds.",
        "",
        "## Failure attribution",
        "",
    ]
    for key, fraction in attribution["fractions"].items():
        report.append(f"- {key}: {fraction:.3f}")
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== EVIDENCE HARDENING / HEADROOM ===", flush=True)
    print(
        f"legacy incumbent reference:       {survival('legacy_incumbent_reference'):.3f}",
        flush=True,
    )
    print(
        f"fixed optimizer v2:              {survival('fixed_optimizer_v2'):.3f}",
        flush=True,
    )
    print(
        f"incumbent v2 normal:             {survival('incumbent_v2_normal'):.3f}",
        flush=True,
    )
    print(
        f"perfect sensing diagnostic:      {survival('incumbent_v2_perfect_sensing'):.3f}",
        flush=True,
    )
    print(
        f"deterministic interaction diag:  {survival('incumbent_v2_deterministic_interactions'):.3f}",
        flush=True,
    )
    print(
        f"combined relaxation diagnostic:  {survival('incumbent_v2_combined_relaxation'):.3f}",
        flush=True,
    )
    print(
        f"best-of-5 oracle v2:             {survival('best_of_5_oracle_v2'):.3f}",
        flush=True,
    )
    print(
        "headroom deltas (survival):      "
        f"sense={headroom['perfect_sensing']['asset_survival_rate']['relaxed_minus_normal']:+.4f} "
        f"interaction={headroom['deterministic_interactions']['asset_survival_rate']['relaxed_minus_normal']:+.4f} "
        f"combined={headroom['combined_relaxation']['asset_survival_rate']['relaxed_minus_normal']:+.4f}",
        flush=True,
    )
    print(
        f"failure attribution:             {attribution['fractions']}",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
