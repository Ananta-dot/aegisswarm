from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from .adaptive_rl import (
    BASE_PROGRAM_INDEX,
    MODE_NAMES,
    QUICK_MODEL_SEEDS,
    _hierarchical_delta,
    _scenario_bootstrap_delta,
    evaluate_ppo_model,
    evaluate_static_modes,
    run_static_mode,
)
from .evidence_hardening import load_incumbent_programs
from .splits import PPO_DEV_SEEDS, PPO_TRAIN_SEEDS
from .strategy_selector import episode_reward


PROTOCOL_ID = "aegisswarm-hierarchical-ppo-v1-frozen-extension"
QUICK_EVAL_COUNT = 20
FROZEN_EVAL_COUNT = 100
FROZEN_EVAL_SEEDS = tuple(
    PPO_DEV_SEEDS[QUICK_EVAL_COUNT : QUICK_EVAL_COUNT + FROZEN_EVAL_COUNT]
)
CALIBRATION_SEEDS = tuple(PPO_TRAIN_SEEDS[:100])
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
DEFAULT_MODEL_DIR = "artifacts/ppo_adaptive_quick"
DEFAULT_OUT_DIR = "artifacts/ppo_adaptive_frozen_eval"


def _rows_with_reward(rows):
    out = []
    for row in rows:
        enriched = dict(row)
        enriched["established_reward"] = float(episode_reward(row))
        out.append(enriched)
    return out


def _metric_mean(rows, key):
    return float(np.mean([float(row[key]) for row in rows]))


def _static_rows_and_diagnostics(program, mode: int, seeds):
    rows = []
    diagnostics = []
    for seed in seeds:
        row, diag, _ = run_static_mode(program, int(mode), int(seed))
        rows.append(row)
        diagnostics.append(diag)
    return rows, diagnostics


def _diagnostic_summary(diags):
    if not diags:
        return {}
    attempts = np.asarray(
        [float(d.get("real_interaction_attempts", 0.0)) for d in diags], dtype=float
    )
    failures = np.asarray(
        [float(d.get("real_interaction_failures", 0.0)) for d in diags], dtype=float
    )
    exhausted = np.asarray(
        [float(bool(d.get("resource_exhausted", False))) for d in diags], dtype=float
    )
    overload = np.asarray(
        [float(d.get("overload_steps", 0.0)) for d in diags], dtype=float
    )
    remaining = np.asarray(
        [float(d.get("resource_uses_remaining", 0.0)) for d in diags], dtype=float
    )
    total_attempts = float(attempts.sum())
    total_failures = float(failures.sum())
    return {
        "attempts_mean": float(attempts.mean()),
        "failures_mean": float(failures.mean()),
        "aggregate_failure_rate": (
            float(total_failures / total_attempts) if total_attempts > 0.0 else 0.0
        ),
        "resource_exhaustion_rate": float(exhausted.mean()),
        "overload_steps_mean": float(overload.mean()),
        "resource_uses_remaining_mean": float(remaining.mean()),
    }


def _average_diagnostic_summaries(summaries):
    if not summaries:
        return {}
    keys = sorted(set().union(*(x.keys() for x in summaries)))
    return {
        key: float(np.mean([float(x.get(key, 0.0)) for x in summaries]))
        for key in keys
    }


def _mode_proportions(counts: Counter):
    total = max(sum(int(v) for v in counts.values()), 1)
    return {
        MODE_NAMES[int(k)]: float(int(v) / total)
        for k, v in sorted(counts.items())
    }


def run_frozen_ppo_generalization(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    model_dir=DEFAULT_MODEL_DIR,
    out_dir=DEFAULT_OUT_DIR,
):
    programs = load_incumbent_programs(source_dir)
    if BASE_PROGRAM_INDEX >= len(programs):
        raise RuntimeError("frozen PPO base-program index is unavailable")
    program = np.asarray(programs[BASE_PROGRAM_INDEX], dtype=np.int16)

    _, calibration_rewards = evaluate_static_modes(program, CALIBRATION_SEEDS)
    static_best_mode = int(np.argmax(np.asarray(calibration_rewards, dtype=float)))

    incumbent_rows, incumbent_diag = _static_rows_and_diagnostics(
        program, 0, FROZEN_EVAL_SEEDS
    )
    static_rows, static_diag = _static_rows_and_diagnostics(
        program, static_best_mode, FROZEN_EVAL_SEEDS
    )
    incumbent_rows = _rows_with_reward(incumbent_rows)
    static_rows = _rows_with_reward(static_rows)

    ppo_rows_by_run = []
    ppo_diag_by_run = []
    mode_counts_by_run = []
    model_paths = []

    model_dir = Path(model_dir)
    for model_seed in QUICK_MODEL_SEEDS:
        model_path = model_dir / f"ppo_seed_{int(model_seed)}.zip"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Missing frozen quick PPO model: {model_path}. "
                "Run the quick PPO screen first."
            )
        rows, diagnostics, counts = evaluate_ppo_model(
            program, model_path, FROZEN_EVAL_SEEDS
        )
        ppo_rows_by_run.append(_rows_with_reward(rows))
        ppo_diag_by_run.append(diagnostics)
        mode_counts_by_run.append(_mode_proportions(counts))
        model_paths.append(str(model_path))

    survival_vs_inc = _hierarchical_delta(
        incumbent_rows,
        ppo_rows_by_run,
        "asset_survival_rate",
        seed=332001,
    )
    survival_vs_static = _hierarchical_delta(
        static_rows,
        ppo_rows_by_run,
        "asset_survival_rate",
        seed=332101,
    )
    reward_vs_inc = _hierarchical_delta(
        incumbent_rows,
        ppo_rows_by_run,
        "established_reward",
        seed=332201,
    )
    reward_vs_static = _hierarchical_delta(
        static_rows,
        ppo_rows_by_run,
        "established_reward",
        seed=332301,
    )
    static_survival_vs_inc = _scenario_bootstrap_delta(
        incumbent_rows,
        static_rows,
        "asset_survival_rate",
        seed=332401,
    )
    static_reward_vs_inc = _scenario_bootstrap_delta(
        incumbent_rows,
        static_rows,
        "established_reward",
        seed=332501,
    )

    ppo_rows_flat_by_metric = {
        key: float(
            np.mean([_metric_mean(rows, key) for rows in ppo_rows_by_run])
        )
        for key in (
            "asset_survival_rate",
            "containment_rate",
            "penetrations",
            "cumulative_damage",
            "defenders_consumed",
            "mean_response_delay",
            "established_reward",
        )
    }
    metric_summary = {}
    for key in ppo_rows_flat_by_metric:
        metric_summary[key] = {
            "incumbent": _metric_mean(incumbent_rows, key),
            "static_best": _metric_mean(static_rows, key),
            "ppo": ppo_rows_flat_by_metric[key],
        }

    diag_summary = {
        "incumbent": _diagnostic_summary(incumbent_diag),
        "static_best": _diagnostic_summary(static_diag),
        "ppo": _average_diagnostic_summaries(
            [_diagnostic_summary(x) for x in ppo_diag_by_run]
        ),
    }

    result = {
        "protocol_id": PROTOCOL_ID,
        "base_program_index": int(BASE_PROGRAM_INDEX),
        "model_seeds": [int(x) for x in QUICK_MODEL_SEEDS],
        "model_paths": model_paths,
        "evaluation_seeds": [int(x) for x in FROZEN_EVAL_SEEDS],
        "calibration_seeds": [int(x) for x in CALIBRATION_SEEDS],
        "static_best_mode_index": int(static_best_mode),
        "static_best_mode_name": MODE_NAMES[static_best_mode],
        "metric_summary": metric_summary,
        "diagnostic_summary": diag_summary,
        "static_survival_minus_incumbent": static_survival_vs_inc,
        "static_reward_minus_incumbent": static_reward_vs_inc,
        "ppo_survival_minus_incumbent": survival_vs_inc,
        "ppo_survival_minus_static": survival_vs_static,
        "ppo_reward_minus_incumbent": reward_vs_inc,
        "ppo_reward_minus_static": reward_vs_static,
        "ppo_mode_proportions_by_training_run": mode_counts_by_run,
        "notes": [
            "No PPO retraining, hyperparameter change, tactical-mode change, or reward change is performed in this extension.",
            "The two exact quick-screen PPO models are evaluated on 100 additional PPO-development scenarios disjoint from the first 20 quick scenarios.",
            "Established reward is computed row-wise from the same project scoring function used elsewhere.",
        ],
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))

    print(
        "AegisSwarm frozen PPO generalization | "
        f"models={len(QUICK_MODEL_SEEDS)} scenarios={len(FROZEN_EVAL_SEEDS)}",
        flush=True,
    )
    print("\n=== FROZEN PPO GENERALIZATION ===", flush=True)
    print(
        f"static best mode:                 {static_best_mode} ({MODE_NAMES[static_best_mode]})",
        flush=True,
    )
    print(
        "survival inc/static/PPO:           "
        f"{metric_summary['asset_survival_rate']['incumbent']:.3f} / "
        f"{metric_summary['asset_survival_rate']['static_best']:.3f} / "
        f"{metric_summary['asset_survival_rate']['ppo']:.3f}",
        flush=True,
    )
    print(
        "established reward inc/static/PPO: "
        f"{metric_summary['established_reward']['incumbent']:.3f} / "
        f"{metric_summary['established_reward']['static_best']:.3f} / "
        f"{metric_summary['established_reward']['ppo']:.3f}",
        flush=True,
    )
    print(
        f"PPO - incumbent survival:         {survival_vs_inc['mean']:+.4f} CI={survival_vs_inc['ci95']}",
        flush=True,
    )
    print(
        f"PPO - incumbent reward:           {reward_vs_inc['mean']:+.3f} CI={reward_vs_inc['ci95']}",
        flush=True,
    )
    print(
        f"PPO - static survival:            {survival_vs_static['mean']:+.4f} CI={survival_vs_static['ci95']}",
        flush=True,
    )
    print(
        f"PPO - static reward:              {reward_vs_static['mean']:+.3f} CI={reward_vs_static['ci95']}",
        flush=True,
    )
    print(
        f"PPO per-run survival deltas:      {survival_vs_inc['per_training_run']}",
        flush=True,
    )
    print(
        f"PPO per-run reward deltas:        {reward_vs_inc['per_training_run']}",
        flush=True,
    )
    print(
        f"mode proportions/run:             {mode_counts_by_run}",
        flush=True,
    )
    print(
        "diagnostics inc/static/PPO:        " + json.dumps(diag_summary, sort_keys=True),
        flush=True,
    )
    print(
        "metric means inc/static/PPO:       " + json.dumps(metric_summary, sort_keys=True),
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
