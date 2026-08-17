from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .axplorer_v2 import device_auto
from .final_proof import compare_structured, summarize_method
from .hybrid_ablation import SCENARIO_KWARGS, evaluate_hybrid_program_runs, evaluate_optimizer_only
from .hybrid_objective import save_run, train_hybrid_axplorer, train_hybrid_local
from .scoring import EvalConfig
from .splits import HYBRID_OBJECTIVE_CONFIRM_SEEDS, HYBRID_OBJECTIVE_DEV_SEEDS, TRAIN_SEEDS


PROTOCOL_ID = "aegisswarm-hybrid-objective-v1"
SEARCH_SEEDS = (43001, 43002, 43003, 43004, 43005)
TRAIN_SCENARIOS = 16
ORACLE_BUDGET = 1800
POPULATION = 64
LOCAL_REFINEMENT_ROUNDS = 2
AXPLORER_SAMPLES = 64
AXPLORER_TRAIN_STEPS = 200
AXPLORER_SAMPLE_TEMPERATURE = 0.85
AXPLORER_WEIGHT_TEMPERATURE = 4.0
ARCHIVE_SIZE = 256

QUICK_SEARCH_SEEDS = (93001, 93002)
QUICK_TRAIN_SCENARIOS = 4
QUICK_BUDGET = 128
QUICK_POPULATION = 16
QUICK_LOCAL_ROUNDS = 1
QUICK_SAMPLES = 16
QUICK_TRAIN_STEPS = 12
QUICK_EVAL_SEEDS = tuple(HYBRID_OBJECTIVE_DEV_SEEDS[:20])


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _load_or_train(path, method, search_seed, train_fn, force=False, **kwargs):
    path = Path(path)
    if path.exists() and not force:
        data = json.loads(path.read_text())
        if data.get("method") == method and int(data.get("search_seed", -1)) == int(search_seed):
            print(f"[resume] {method} seed={search_seed}: {path}", flush=True)
            return data
    data = train_fn(search_seed=search_seed, **kwargs)
    save_run(path, data)
    return data


def _write_report(path, mode, seeds, optimizer_summary, local_summary, ax_summary, comparison):
    survival = comparison["asset_survival_rate"]
    lines = [
        "# AegisSwarm Hybrid Objective Learning Report",
        "",
        f"Protocol: `{PROTOCOL_ID}`",
        f"Mode: **{mode}**",
        f"Evaluation scenarios: **{len(seeds)}** ({seeds[0]}–{seeds[-1]})",
        "",
        "Every searched candidate is executed through the same Hungarian optimizer during training.",
        "The experiment therefore learns the optimizer's strategic objective rather than swapping",
        "an optimizer underneath a strategy trained for greedy execution.",
        "",
        "## Survival",
        "",
        "| Variant | Survival | 95% CI |",
        "|---|---:|---:|",
    ]
    for name, summary in (
        ("fixed_optimizer", optimizer_summary),
        ("hybrid_local", local_summary),
        ("hybrid_axplorer", ax_summary),
    ):
        s = summary["asset_survival_rate"]
        lines.append(
            f"| {name} | {100*s['mean']:.2f}% | "
            f"[{100*s['ci95'][0]:.2f}%, {100*s['ci95'][1]:.2f}%] |"
        )

    lines += [
        "",
        "## Learned-search comparison",
        "",
        f"- Axplorer minus local: **{100*survival['axplorer_minus_local']:+.2f} pp**",
        f"- 95% paired hierarchical CI: **[{100*survival['ci95'][0]:+.2f}, {100*survival['ci95'][1]:+.2f}] pp**",
        f"- Paired sign-flip p-value: **{survival['paired_sign_flip_pvalue']:.6f}**",
        "",
    ]
    if mode == "development":
        lines += [
            "This is development evidence. The confirmation block remains untouched.",
            "Do not run confirmation until the architecture and hyperparameters are frozen.",
        ]
    else:
        lines += [
            "This is the reserved confirmation block and must not be reused for tuning.",
        ]
    path.write_text("\n".join(lines))


def _evaluate(out_dir, mode, seeds, local_runs, ax_runs, workers):
    local_programs = [np.asarray(run["best_program"], dtype=np.int16) for run in local_runs]
    ax_programs = [np.asarray(run["best_program"], dtype=np.int16) for run in ax_runs]

    optimizer_eval = evaluate_optimizer_only(seeds, SCENARIO_KWARGS)
    local_eval = evaluate_hybrid_program_runs(local_programs, seeds, SCENARIO_KWARGS, workers=workers)
    ax_eval = evaluate_hybrid_program_runs(ax_programs, seeds, SCENARIO_KWARGS, workers=workers)

    optimizer_summary = summarize_method(optimizer_eval, bootstrap_seed=101000)
    local_summary = summarize_method(local_eval, bootstrap_seed=102000)
    ax_summary = summarize_method(ax_eval, bootstrap_seed=103000)
    comparison = compare_structured(local_eval, ax_eval)

    result = {
        "protocol_id": PROTOCOL_ID,
        "mode": mode,
        "evaluation_seeds": [int(x) for x in seeds],
        "fixed_optimizer": optimizer_summary,
        "hybrid_local": local_summary,
        "hybrid_axplorer": ax_summary,
        "paired_comparison": comparison,
    }
    _save_json(Path(out_dir) / "results.json", result)
    _write_report(
        Path(out_dir) / "REPORT.md",
        mode,
        seeds,
        optimizer_summary,
        local_summary,
        ax_summary,
        comparison,
    )

    s = comparison["asset_survival_rate"]
    print("\n=== HYBRID OBJECTIVE LEARNING ===", flush=True)
    print(
        f"fixed_optimizer survival: {optimizer_summary['asset_survival_rate']['mean']:.3f}",
        flush=True,
    )
    print(
        f"hybrid_local survival:    {local_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={local_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"hybrid_axplorer survival: {ax_summary['asset_survival_rate']['mean']:.3f} "
        f"CI={ax_summary['asset_survival_rate']['ci95']}",
        flush=True,
    )
    print(
        f"difference (A-L):         {s['axplorer_minus_local']:+.4f} CI={s['ci95']}",
        flush=True,
    )
    print(f"paired p-value:           {s['paired_sign_flip_pvalue']:.6f}", flush=True)
    print(f"Saved: {out_dir}", flush=True)
    return result


def run_hybrid_objective_development(
    out_dir="artifacts/hybrid_objective_dev",
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
        budget = QUICK_BUDGET
        population = QUICK_POPULATION
        local_rounds = QUICK_LOCAL_ROUNDS
        samples = QUICK_SAMPLES
        train_steps = QUICK_TRAIN_STEPS
        eval_seeds = QUICK_EVAL_SEEDS
    else:
        search_seeds = SEARCH_SEEDS
        train_scenarios = TRAIN_SCENARIOS
        budget = ORACLE_BUDGET
        population = POPULATION
        local_rounds = LOCAL_REFINEMENT_ROUNDS
        samples = AXPLORER_SAMPLES
        train_steps = AXPLORER_TRAIN_STEPS
        eval_seeds = HYBRID_OBJECTIVE_DEV_SEEDS

    protocol = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "search_seeds": [int(x) for x in search_seeds],
        "train_seeds": [int(x) for x in TRAIN_SEEDS[:train_scenarios]],
        "oracle_budget_per_method_per_run": int(budget),
        "population": int(population),
        "execution_during_search": "rule-guided Hungarian optimizer",
        "evaluation_first_seed": int(eval_seeds[0]),
        "evaluation_last_seed": int(eval_seeds[-1]),
        "evaluation_count": int(len(eval_seeds)),
        "device": str(device),
        "workers": int(workers),
        "architecture_frozen": False,
    }
    _save_json(out_dir / "protocol.json", protocol)

    print(
        f"AegisSwarm hybrid-objective {'quick' if quick else 'development'} | "
        f"runs={len(search_seeds)} budget={budget} train_scenarios={train_scenarios} "
        f"eval_scenarios={len(eval_seeds)} device={device} workers={workers}",
        flush=True,
    )

    config = EvalConfig(seeds=TRAIN_SEEDS[:train_scenarios])
    local_runs = []
    ax_runs = []
    for i, search_seed in enumerate(search_seeds, start=1):
        print(
            f"\n=== paired hybrid-objective run {i}/{len(search_seeds)} seed={search_seed} ===",
            flush=True,
        )
        local_runs.append(
            _load_or_train(
                runs_dir / f"hybrid_local_seed_{search_seed}.json",
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
        ax_runs.append(
            _load_or_train(
                runs_dir / f"hybrid_axplorer_seed_{search_seed}.json",
                "hybrid_axplorer",
                search_seed,
                train_hybrid_axplorer,
                force=force_train,
                config=config,
                oracle_budget=budget,
                population=population,
                samples_per_round=samples,
                local_refinement_rounds=local_rounds,
                train_steps=train_steps,
                sample_temperature=AXPLORER_SAMPLE_TEMPERATURE,
                weight_temperature=AXPLORER_WEIGHT_TEMPERATURE,
                archive_size=ARCHIVE_SIZE,
                workers=workers,
                device=device,
                verbose=True,
            )
        )

    return _evaluate(
        out_dir,
        "quick_development" if quick else "development",
        eval_seeds,
        local_runs,
        ax_runs,
        workers,
    )


def run_hybrid_objective_confirmation(
    source_dir="artifacts/hybrid_objective_dev",
    out_dir="artifacts/hybrid_objective_confirm",
    workers=4,
):
    source_dir = Path(source_dir)
    source_protocol_path = source_dir / "protocol.json"
    if not source_protocol_path.exists():
        raise FileNotFoundError(
            f"Missing development protocol at {source_protocol_path}; run full development first."
        )

    source_protocol = json.loads(source_protocol_path.read_text())
    expected_protocol = PROTOCOL_ID + "-development"
    if source_protocol.get("protocol_id") != expected_protocol:
        raise RuntimeError(
            "Confirmation requires the full development protocol, not quick or unrelated artifacts."
        )
    if source_protocol.get("architecture_frozen") is not True:
        raise RuntimeError(
            "Hybrid-objective architecture is not frozen. Review development results first, "
            "then explicitly set architecture_frozen=true in the development protocol before "
            "consuming confirmation seeds 8000-8399."
        )

    runs_dir = source_dir / "runs"
    local_runs = []
    ax_runs = []
    for seed in SEARCH_SEEDS:
        lp = runs_dir / f"hybrid_local_seed_{seed}.json"
        ap = runs_dir / f"hybrid_axplorer_seed_{seed}.json"
        if not lp.exists() or not ap.exists():
            raise FileNotFoundError(
                f"Missing frozen development artifacts for seed {seed}; run development first."
            )
        local_runs.append(json.loads(lp.read_text()))
        ax_runs.append(json.loads(ap.read_text()))

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    _save_json(
        out_dir / "protocol.json",
        {
            "protocol_id": PROTOCOL_ID + "-confirmation",
            "source_dir": str(source_dir),
            "source_development_protocol": expected_protocol,
            "search_seeds": list(SEARCH_SEEDS),
            "confirmation_first_seed": int(HYBRID_OBJECTIVE_CONFIRM_SEEDS[0]),
            "confirmation_last_seed": int(HYBRID_OBJECTIVE_CONFIRM_SEEDS[-1]),
            "confirmation_count": int(len(HYBRID_OBJECTIVE_CONFIRM_SEEDS)),
            "training_allowed": False,
        },
    )
    print(
        f"AegisSwarm HYBRID OBJECTIVE CONFIRMATION | frozen_runs={len(SEARCH_SEEDS)} "
        f"scenarios={len(HYBRID_OBJECTIVE_CONFIRM_SEEDS)}",
        flush=True,
    )
    return _evaluate(
        out_dir,
        "confirmation",
        HYBRID_OBJECTIVE_CONFIRM_SEEDS,
        local_runs,
        ax_runs,
        workers,
    )
