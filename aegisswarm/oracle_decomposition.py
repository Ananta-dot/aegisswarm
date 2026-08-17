from __future__ import annotations

import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import numpy as np

from .evidence_hardening import load_incumbent_programs
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS
from .random_tape import IndexedRandomTape
from .scenarios import ScenarioGenerator
from .simulator_v2 import SimulatorV2
from .splits import ORACLE_DECOMP_DEV_SEEDS
from .strategy_selector import episode_reward


PROTOCOL_ID = "aegisswarm-oracle-decomposition-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
QUICK_WORLD_COUNT = 20
QUICK_TAPES = 4
FULL_TAPES = 8


def oracle_tape_seed(world_seed: int, replicate_index: int) -> int:
    """Stable evaluation-tape seed, independent of program/control flow."""
    modulus = (1 << 63) - 25
    return int(
        (
            1_000_003 * int(world_seed)
            + 104_729 * (int(replicate_index) + 1)
            + 987_654_319
        )
        % modulus
    )


def _program_world_worker(payload):
    program, world_seed, tape_count, scenario_kwargs = payload
    kwargs = dict(scenario_kwargs)
    max_steps = int(kwargs.pop("max_steps", 150))
    base = ScenarioGenerator(max_steps=max_steps).generate(seed=int(world_seed), **kwargs)

    rows = []
    for replicate_index in range(int(tape_count)):
        scenario = ScenarioGenerator.clone(base)
        simulator = SimulatorV2(scenario)
        simulator.tape = IndexedRandomTape(
            oracle_tape_seed(int(world_seed), int(replicate_index))
        )
        metrics = simulator.run(RuleGuidedHungarianPolicy(program))
        row = metrics.as_dict()
        row["reward"] = episode_reward(row)
        rows.append(row)
    return int(world_seed), rows


def evaluate_program_world_tapes(programs, world_seeds, tape_count, workers=1, scenario_kwargs=None):
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    programs = [np.asarray(p, dtype=np.int16) for p in programs]
    world_seeds = tuple(int(s) for s in world_seeds)
    tape_count = int(tape_count)
    payloads = [
        ([int(x) for x in program], int(world_seed), tape_count, scenario_kwargs)
        for program in programs
        for world_seed in world_seeds
    ]

    if workers <= 1:
        outputs = [_program_world_worker(payload) for payload in payloads]
    else:
        with ProcessPoolExecutor(
            max_workers=max(1, int(workers)),
            mp_context=get_context("spawn"),
        ) as executor:
            outputs = list(executor.map(_program_world_worker, payloads))

    n_programs = len(programs)
    n_worlds = len(world_seeds)
    metrics = {
        name: np.zeros((n_programs, n_worlds, tape_count), dtype=float)
        for name in (
            "asset_survival_rate",
            "containment_rate",
            "penetrations",
            "cumulative_damage",
            "defenders_consumed",
            "mean_response_delay",
            "reward",
        )
    }

    k = 0
    for program_index in range(n_programs):
        for world_index, expected_seed in enumerate(world_seeds):
            world_seed, rows = outputs[k]
            k += 1
            if int(world_seed) != int(expected_seed):
                raise RuntimeError("Parallel oracle-decomposition output order changed")
            if len(rows) != tape_count:
                raise RuntimeError("Unexpected tape count in oracle decomposition")
            for tape_index, row in enumerate(rows):
                for name in metrics:
                    metrics[name][program_index, world_index, tape_index] = float(row[name])

    return metrics


def _bootstrap_mean(diff_by_world, seed=1, n_boot=5000):
    diff = np.asarray(diff_by_world, dtype=float)
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        idx = rng.integers(0, len(diff), size=len(diff))
        draws[i] = float(diff[idx].mean())
    return {
        "mean": float(diff.mean()),
        "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
    }


def _chosen_values(tensor, choices, tape_indices):
    tensor = np.asarray(tensor, dtype=float)
    choices = np.asarray(choices, dtype=int)
    tape_indices = np.asarray(tape_indices, dtype=int)
    values = np.empty((tensor.shape[1], len(tape_indices)), dtype=float)
    for world_index, program_index in enumerate(choices):
        values[world_index] = tensor[program_index, world_index, tape_indices]
    return values


def _global_fixed_choice(reward, tape_indices):
    tape_indices = np.asarray(tape_indices, dtype=int)
    program_rewards = reward[:, :, tape_indices].mean(axis=(1, 2))
    return int(np.argmax(program_rewards))


def _scenario_expected_choices(reward, tape_indices):
    tape_indices = np.asarray(tape_indices, dtype=int)
    per_program_world = reward[:, :, tape_indices].mean(axis=2)
    return np.argmax(per_program_world, axis=0).astype(int)


def decompose_oracle(metrics):
    reward = np.asarray(metrics["reward"], dtype=float)
    survival = np.asarray(metrics["asset_survival_rate"], dtype=float)
    n_programs, n_worlds, n_tapes = reward.shape
    if n_tapes < 2 or n_tapes % 2:
        raise ValueError("Oracle decomposition requires an even tape count >= 2")

    first = np.arange(0, n_tapes // 2, dtype=int)
    second = np.arange(n_tapes // 2, n_tapes, dtype=int)
    all_tapes = np.arange(n_tapes, dtype=int)

    tape0 = np.asarray([0], dtype=int)
    fixed_t0 = _global_fixed_choice(reward, tape0)
    oracle_t0_choices = _scenario_expected_choices(reward, tape0)
    fixed_t0_by_world = survival[fixed_t0, :, 0]
    oracle_t0_by_world = _chosen_values(survival, oracle_t0_choices, tape0)[:, 0]

    fixed_all = _global_fixed_choice(reward, all_tapes)
    expected_choices = _scenario_expected_choices(reward, all_tapes)
    fixed_all_by_world = survival[fixed_all, :, :].mean(axis=1)
    expected_by_world = _chosen_values(survival, expected_choices, all_tapes).mean(axis=1)

    choice_first = _scenario_expected_choices(reward, first)
    choice_second = _scenario_expected_choices(reward, second)
    fixed_first = _global_fixed_choice(reward, first)
    fixed_second = _global_fixed_choice(reward, second)

    oracle_eval_second = _chosen_values(survival, choice_first, second).mean(axis=1)
    oracle_eval_first = _chosen_values(survival, choice_second, first).mean(axis=1)
    cross_oracle_by_world = 0.5 * (oracle_eval_second + oracle_eval_first)

    fixed_eval_second = survival[fixed_first, :, :][:, second].mean(axis=1)
    fixed_eval_first = survival[fixed_second, :, :][:, first].mean(axis=1)
    cross_fixed_by_world = 0.5 * (fixed_eval_second + fixed_eval_first)

    raw_gap = _bootstrap_mean(oracle_t0_by_world - fixed_t0_by_world, seed=320101)
    expected_gap = _bootstrap_mean(expected_by_world - fixed_all_by_world, seed=320201)
    cross_gap = _bootstrap_mean(cross_oracle_by_world - cross_fixed_by_world, seed=320301)

    raw_gap_mean = float(raw_gap["mean"])
    stable_fraction = (
        float(cross_gap["mean"] / raw_gap_mean) if raw_gap_mean > 1e-12 else 0.0
    )

    tape_choices = np.argmax(reward, axis=0)  # [world, tape]
    modal_fractions = []
    for row in tape_choices:
        counts = Counter(int(x) for x in row)
        modal_fractions.append(max(counts.values()) / n_tapes)

    return {
        "program_mean_survivals": [float(x) for x in survival.mean(axis=(1, 2))],
        "program_mean_rewards": [float(x) for x in reward.mean(axis=(1, 2))],
        "single_tape_fixed_program_index": int(fixed_t0),
        "all_tape_fixed_program_index": int(fixed_all),
        "first_half_fixed_program_index": int(fixed_first),
        "second_half_fixed_program_index": int(fixed_second),
        "single_tape_fixed_survival": float(fixed_t0_by_world.mean()),
        "single_tape_oracle_survival": float(oracle_t0_by_world.mean()),
        "single_tape_oracle_minus_fixed": raw_gap,
        "expected_fixed_survival": float(fixed_all_by_world.mean()),
        "expected_oracle_survival": float(expected_by_world.mean()),
        "expected_oracle_minus_fixed": expected_gap,
        "cross_tape_fixed_survival": float(cross_fixed_by_world.mean()),
        "cross_tape_oracle_survival": float(cross_oracle_by_world.mean()),
        "cross_tape_oracle_minus_fixed": cross_gap,
        "cross_tape_choice_agreement": float(np.mean(choice_first == choice_second)),
        "mean_tape_oracle_modal_fraction": float(np.mean(modal_fractions)),
        "stable_fraction_of_raw_oracle_gap": stable_fraction,
        "expected_oracle_choice_counts": {
            str(k): int(v) for k, v in sorted(Counter(int(x) for x in expected_choices).items())
        },
        "first_half_choice_counts": {
            str(k): int(v) for k, v in sorted(Counter(int(x) for x in choice_first).items())
        },
        "second_half_choice_counts": {
            str(k): int(v) for k, v in sorted(Counter(int(x) for x in choice_second).items())
        },
        "n_programs": int(n_programs),
        "n_worlds": int(n_worlds),
        "n_tapes": int(n_tapes),
    }


def run_oracle_decomposition(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/oracle_decomposition_quick",
    workers=5,
    quick=True,
):
    world_seeds = (
        tuple(ORACLE_DECOMP_DEV_SEEDS[:QUICK_WORLD_COUNT])
        if quick
        else tuple(ORACLE_DECOMP_DEV_SEEDS)
    )
    tape_count = QUICK_TAPES if quick else FULL_TAPES
    programs = load_incumbent_programs(source_dir)

    print(
        f"AegisSwarm oracle decomposition | mode={'quick' if quick else 'development'} "
        f"programs={len(programs)} worlds={len(world_seeds)} tapes/world={tape_count} "
        f"workers={workers}",
        flush=True,
    )

    metrics = evaluate_program_world_tapes(programs, world_seeds, tape_count, workers=workers)
    result = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "world_seeds": [int(x) for x in world_seeds],
        "tape_count": int(tape_count),
        "decomposition": decompose_oracle(metrics),
        "notes": [
            "No policy is trained or changed in this protocol.",
            "Single-tape oracle uses same-realization hindsight and is intentionally optimistic.",
            "Expected oracle averages stochastic outcomes but chooses and scores on the same tapes.",
            "Cross-tape oracle chooses using one tape half and scores only on the held-out half; the reverse fold is averaged symmetrically.",
            "Cross-tape oracle remains non-deployable; it estimates stable structural specialization rather than a deployable selector.",
        ],
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))

    d = result["decomposition"]
    (out_dir / "REPORT.md").write_text(
        "\n".join(
            [
                "# AegisSwarm Oracle Decomposition",
                "",
                f"Protocol: `{result['protocol_id']}`",
                f"Worlds: {len(world_seeds)}",
                f"Tapes/world: {tape_count}",
                "",
                f"Single-tape fixed: {d['single_tape_fixed_survival']:.4f}",
                f"Single-tape oracle: {d['single_tape_oracle_survival']:.4f}",
                f"Cross-tape fixed: {d['cross_tape_fixed_survival']:.4f}",
                f"Cross-tape oracle: {d['cross_tape_oracle_survival']:.4f}",
                f"Cross-tape gap: {d['cross_tape_oracle_minus_fixed']['mean']:+.4f} CI={d['cross_tape_oracle_minus_fixed']['ci95']}",
                f"Cross-tape choice agreement: {d['cross_tape_choice_agreement']:.4f}",
                f"Stable fraction of raw gap: {d['stable_fraction_of_raw_oracle_gap']:.4f}",
            ]
        )
    )

    print("\n=== ORACLE DECOMPOSITION ===", flush=True)
    print(f"program mean survivals:          {[round(x, 4) for x in d['program_mean_survivals']]}", flush=True)
    print(f"single-tape fixed survival:      {d['single_tape_fixed_survival']:.3f}", flush=True)
    print(f"single-tape oracle survival:     {d['single_tape_oracle_survival']:.3f}", flush=True)
    print(f"single-tape oracle - fixed:      {d['single_tape_oracle_minus_fixed']['mean']:+.4f} CI={d['single_tape_oracle_minus_fixed']['ci95']}", flush=True)
    print(f"expected fixed survival:         {d['expected_fixed_survival']:.3f}", flush=True)
    print(f"expected oracle survival:        {d['expected_oracle_survival']:.3f}", flush=True)
    print(f"expected oracle - fixed:         {d['expected_oracle_minus_fixed']['mean']:+.4f} CI={d['expected_oracle_minus_fixed']['ci95']}", flush=True)
    print(f"cross-tape fixed survival:       {d['cross_tape_fixed_survival']:.3f}", flush=True)
    print(f"cross-tape oracle survival:      {d['cross_tape_oracle_survival']:.3f}", flush=True)
    print(f"cross-tape oracle - fixed:       {d['cross_tape_oracle_minus_fixed']['mean']:+.4f} CI={d['cross_tape_oracle_minus_fixed']['ci95']}", flush=True)
    print(f"cross-tape choice agreement:     {d['cross_tape_choice_agreement']:.3f}", flush=True)
    print(f"tape-oracle modal fraction:      {d['mean_tape_oracle_modal_fraction']:.3f}", flush=True)
    print(f"stable fraction of raw gap:      {d['stable_fraction_of_raw_oracle_gap']:.3f}", flush=True)
    print(f"expected choice counts:          {d['expected_oracle_choice_counts']}", flush=True)
    print(f"Saved: {out_dir}", flush=True)
    return result
