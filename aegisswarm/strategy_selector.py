from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .evidence_hardening import (
    _oracle_sort_key,
    best_of_programs_oracle,
    evaluate_programs_v2,
    load_incumbent_programs,
)
from .final_proof import METRICS
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS
from .models import ThreatType
from .policies import distance_to_target
from .scenarios import ScenarioGenerator
from .simulator_v2 import SimulatorV2
from .splits import SELECTOR_DEV_SEEDS, SELECTOR_TRAIN_SEEDS


PROTOCOL_ID = "aegisswarm-observable-strategy-selector-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
RIDGE_ALPHA = 1.0
QUICK_TRAIN_COUNT = 100
QUICK_EVAL_COUNT = 20


FEATURE_NAMES = (
    "detected_total",
    "detected_real",
    "detected_direct",
    "detected_fast",
    "detected_decoy",
    "mean_time_to_target",
    "min_time_to_target",
    "mean_target_distance",
    "min_target_distance",
    "mean_detected_speed",
    "max_detected_speed",
    "mean_reachable_defenders",
    "fraction_zero_reach",
    "fraction_one_reach",
    "fraction_multi_reach",
    "available_defenders",
    "total_remaining_uses",
    "mean_remaining_uses",
    "min_remaining_uses",
    "mean_defender_capacity",
    "mean_defender_range",
    "detected_real_per_available_defender",
    "mean_sensor_detection_probability",
    "mean_sensor_range",
    "total_asset_value",
)


def _safe_mean(values, default=0.0):
    return float(np.mean(values)) if values else float(default)


def _safe_min(values, default=0.0):
    return float(np.min(values)) if values else float(default)


def _safe_max(values, default=0.0):
    return float(np.max(values)) if values else float(default)


def observable_features(scenario) -> np.ndarray:
    """Feature snapshot using only state observable before the first action.

    Undetected threats are deliberately excluded. Known assets, defenders and
    sensors are allowed. The function contains no seed, future trajectory,
    realized interaction outcome or oracle information.
    """

    detected = [th for th in scenario.threats if th.active and th.detected]
    real = [th for th in detected if th.threat_type != ThreatType.DECOY]
    direct = [th for th in detected if th.threat_type == ThreatType.DIRECT]
    fast = [th for th in detected if th.threat_type == ThreatType.FAST]
    decoy = [th for th in detected if th.threat_type == ThreatType.DECOY]

    target_distances = [distance_to_target(scenario, th) for th in real]
    times_to_target = [
        distance_to_target(scenario, th) / max(float(th.speed), 1e-6)
        for th in real
    ]
    speeds = [float(th.speed) for th in real]

    defenders = [
        d for d in scenario.defenders if d.available and d.remaining_uses > 0
    ]
    reach_counts = [
        sum(th.distance_to(d.x, d.y) <= d.range for d in defenders)
        for th in real
    ]

    n_real = len(real)
    zero_reach = sum(int(x == 0) for x in reach_counts)
    one_reach = sum(int(x == 1) for x in reach_counts)
    multi_reach = sum(int(x >= 2) for x in reach_counts)

    uses = [float(d.remaining_uses) for d in defenders]
    capacities = [float(d.capacity) for d in defenders]
    ranges = [float(d.range) for d in defenders]
    sensor_probs = [float(s.detection_probability) for s in scenario.sensors]
    sensor_ranges = [float(s.range) for s in scenario.sensors]

    values = np.asarray(
        [
            float(len(detected)),
            float(n_real),
            float(len(direct)),
            float(len(fast)),
            float(len(decoy)),
            _safe_mean(times_to_target),
            _safe_min(times_to_target),
            _safe_mean(target_distances),
            _safe_min(target_distances),
            _safe_mean(speeds),
            _safe_max(speeds),
            _safe_mean(reach_counts),
            float(zero_reach / n_real) if n_real else 0.0,
            float(one_reach / n_real) if n_real else 0.0,
            float(multi_reach / n_real) if n_real else 0.0,
            float(len(defenders)),
            float(sum(uses)),
            _safe_mean(uses),
            _safe_min(uses),
            _safe_mean(capacities),
            _safe_mean(ranges),
            float(n_real / max(len(defenders), 1)),
            _safe_mean(sensor_probs),
            _safe_mean(sensor_ranges),
            float(sum(float(a.value) for a in scenario.assets)),
        ],
        dtype=float,
    )
    if values.shape != (len(FEATURE_NAMES),):
        raise RuntimeError("Observable feature vector shape mismatch")
    return values


def feature_for_seed(seed: int, scenario_kwargs=None) -> np.ndarray:
    scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
    max_steps = int(scenario_kwargs.pop("max_steps", 150))
    scenario = ScenarioGenerator(max_steps=max_steps).generate(seed=int(seed), **scenario_kwargs)
    simulator = SimulatorV2(scenario)
    simulator.sense()
    return observable_features(scenario)


def feature_matrix(seeds, scenario_kwargs=None) -> np.ndarray:
    return np.asarray(
        [feature_for_seed(int(seed), scenario_kwargs) for seed in seeds],
        dtype=float,
    )


def episode_reward(row: dict) -> float:
    loss = (
        100.0 * (1.0 - float(row["asset_survival_rate"]))
        + 40.0 * (1.0 - float(row["containment_rate"]))
        + 3.0 * float(row["cumulative_damage"])
        + 0.15 * float(row["defenders_consumed"])
        + 0.05 * float(row["mean_response_delay"])
    )
    return float(max(0.0, 200.0 - loss))


def reward_matrix(program_evaluation) -> np.ndarray:
    raw = program_evaluation["raw_by_run"]
    if not raw:
        return np.empty((0, 0), dtype=float)
    n_programs = len(raw)
    n_scenarios = len(raw[0])
    out = np.zeros((n_scenarios, n_programs), dtype=float)
    for i in range(n_programs):
        if len(raw[i]) != n_scenarios:
            raise ValueError("Program evaluation rows are not aligned")
        for j in range(n_scenarios):
            out[j, i] = episode_reward(raw[i][j])
    return out


@dataclass
class RidgeRewardSelectorModel:
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    reward_mean: np.ndarray
    coefficients: np.ndarray
    alpha: float = RIDGE_ALPHA

    @classmethod
    def fit(cls, features: np.ndarray, rewards: np.ndarray, alpha: float = RIDGE_ALPHA):
        features = np.asarray(features, dtype=float)
        rewards = np.asarray(rewards, dtype=float)
        if features.ndim != 2 or rewards.ndim != 2:
            raise ValueError("features and rewards must both be matrices")
        if features.shape[0] != rewards.shape[0]:
            raise ValueError("features and rewards must have matching rows")

        mean = features.mean(axis=0)
        scale = features.std(axis=0)
        scale = np.where(scale > 1e-12, scale, 1.0)
        x = (features - mean) / scale
        reward_mean = rewards.mean(axis=0)
        y = rewards - reward_mean
        gram = x.T @ x + float(alpha) * np.eye(x.shape[1], dtype=float)
        coefficients = np.linalg.solve(gram, x.T @ y)
        return cls(mean, scale, reward_mean, coefficients, float(alpha))

    def predict_scores(self, features) -> np.ndarray:
        x = np.asarray(features, dtype=float)
        if x.ndim == 1:
            x = x[None, :]
        z = (x - self.feature_mean) / self.feature_scale
        return z @ self.coefficients + self.reward_mean

    def choose(self, features) -> np.ndarray:
        return np.argmax(self.predict_scores(features), axis=1).astype(int)

    def as_dict(self):
        return {
            "alpha": float(self.alpha),
            "feature_names": list(FEATURE_NAMES),
            "feature_mean": self.feature_mean.tolist(),
            "feature_scale": self.feature_scale.tolist(),
            "reward_mean": self.reward_mean.tolist(),
            "coefficients": self.coefficients.tolist(),
        }


class ObservableStrategySelectorPolicy:
    """Commit to one frozen program using the first observable state snapshot."""

    name = "observable_strategy_selector"

    def __init__(self, programs, model: RidgeRewardSelectorModel):
        self.programs = [np.asarray(p, dtype=np.int16).copy() for p in programs]
        self.model = model
        self._selected_index = None
        self._selected_policy = None
        self.seed = 0

    @property
    def selected_index(self):
        return self._selected_index

    def reset(self, seed: int):
        self.seed = int(seed)
        self._selected_index = None
        self._selected_policy = None

    def assign(self, scenario, t):
        if self._selected_policy is None:
            features = observable_features(scenario)
            self._selected_index = int(self.model.choose(features)[0])
            self._selected_policy = RuleGuidedHungarianPolicy(
                self.programs[self._selected_index],
                name=f"selector_program_{self._selected_index}",
            )
            self._selected_policy.reset(self.seed)
        return self._selected_policy.assign(scenario, t)


def evaluation_from_choices(program_evaluation, choices) -> dict:
    raw = program_evaluation["raw_by_run"]
    choices = [int(x) for x in choices]
    if not raw:
        raise ValueError("No program evaluation rows")
    n_scenarios = len(raw[0])
    if len(choices) != n_scenarios:
        raise ValueError("Choice vector length does not match scenarios")

    rows = [dict(raw[choices[j]][j]) for j in range(n_scenarios)]
    return {
        "matrices": {
            metric: np.asarray([[float(row[metric]) for row in rows]], dtype=float)
            for metric in METRICS
        },
        "runtime_by_run": [0.0],
        "raw_by_run": [rows],
    }


def fixed_program_evaluation(program_evaluation, program_index: int) -> dict:
    raw = program_evaluation["raw_by_run"]
    rows = [dict(row) for row in raw[int(program_index)]]
    return {
        "matrices": {
            metric: np.asarray([[float(row[metric]) for row in rows]], dtype=float)
            for metric in METRICS
        },
        "runtime_by_run": [0.0],
        "raw_by_run": [rows],
    }


def _scenario_bootstrap_delta(first, second, metric, seed=1234, n_boot=5000):
    a = np.asarray(first["matrices"][metric][0], dtype=float)
    b = np.asarray(second["matrices"][metric][0], dtype=float)
    if a.shape != b.shape:
        raise ValueError("Paired scenario vectors must match")
    diff = b - a
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        idx = rng.integers(0, len(diff), size=len(diff))
        draws[i] = float(diff[idx].mean())
    return {
        "second_minus_first": float(diff.mean()),
        "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
    }


def _reward_vector(evaluation):
    return np.asarray(
        [episode_reward(row) for row in evaluation["raw_by_run"][0]],
        dtype=float,
    )


def _bootstrap_reward_delta(first, second, seed=4321, n_boot=5000):
    a = _reward_vector(first)
    b = _reward_vector(second)
    diff = b - a
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        idx = rng.integers(0, len(diff), size=len(diff))
        draws[i] = float(diff[idx].mean())
    return {
        "second_minus_first": float(diff.mean()),
        "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
    }


def _mean_metric(evaluation, metric):
    return float(np.asarray(evaluation["matrices"][metric], dtype=float).mean())


def _program_survivals(program_evaluation):
    matrix = np.asarray(program_evaluation["matrices"]["asset_survival_rate"], dtype=float)
    return [float(x) for x in matrix.mean(axis=1)]


def run_strategy_selector(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/strategy_selector_quick",
    workers=5,
    quick=True,
):
    train_seeds = (
        tuple(SELECTOR_TRAIN_SEEDS[:QUICK_TRAIN_COUNT])
        if quick
        else tuple(SELECTOR_TRAIN_SEEDS)
    )
    eval_seeds = (
        tuple(SELECTOR_DEV_SEEDS[:QUICK_EVAL_COUNT])
        if quick
        else tuple(SELECTOR_DEV_SEEDS)
    )

    programs = load_incumbent_programs(source_dir)
    train_eval = evaluate_programs_v2(programs, train_seeds, workers=workers)
    train_x = feature_matrix(train_seeds)
    train_rewards = reward_matrix(train_eval)

    model = RidgeRewardSelectorModel.fit(train_x, train_rewards, alpha=RIDGE_ALPHA)
    train_mean_rewards = train_rewards.mean(axis=0)
    fixed_best_index = int(np.argmax(train_mean_rewards))

    eval_programs = evaluate_programs_v2(programs, eval_seeds, workers=workers)
    eval_x = feature_matrix(eval_seeds)
    choices = model.choose(eval_x)
    selector_eval = evaluation_from_choices(eval_programs, choices)
    fixed_eval = fixed_program_evaluation(eval_programs, fixed_best_index)
    oracle_eval, oracle_choices = best_of_programs_oracle(eval_programs)

    survival_delta = _scenario_bootstrap_delta(
        fixed_eval, selector_eval, "asset_survival_rate", seed=281001
    )
    reward_delta = _bootstrap_reward_delta(fixed_eval, selector_eval, seed=281101)
    oracle_vs_fixed = _scenario_bootstrap_delta(
        fixed_eval, oracle_eval, "asset_survival_rate", seed=281201
    )
    oracle_vs_selector = _scenario_bootstrap_delta(
        selector_eval, oracle_eval, "asset_survival_rate", seed=281301
    )

    fixed_survival = _mean_metric(fixed_eval, "asset_survival_rate")
    selector_survival = _mean_metric(selector_eval, "asset_survival_rate")
    oracle_survival = _mean_metric(oracle_eval, "asset_survival_rate")
    denominator = oracle_survival - fixed_survival
    gap_captured = (
        float((selector_survival - fixed_survival) / denominator)
        if denominator > 1e-12
        else 0.0
    )

    result = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "mode": "quick" if quick else "development",
        "train_seeds": [int(x) for x in train_seeds],
        "evaluation_seeds": [int(x) for x in eval_seeds],
        "ridge_alpha": float(RIDGE_ALPHA),
        "feature_names": list(FEATURE_NAMES),
        "model": model.as_dict(),
        "training_mean_rewards_by_program": [float(x) for x in train_mean_rewards],
        "fixed_best_program_index": int(fixed_best_index),
        "fresh_program_survival_rates": _program_survivals(eval_programs),
        "fixed_best_survival": fixed_survival,
        "selector_survival": selector_survival,
        "oracle_survival": oracle_survival,
        "selector_minus_fixed_survival": survival_delta,
        "selector_minus_fixed_reward": reward_delta,
        "oracle_minus_fixed_survival": oracle_vs_fixed,
        "oracle_minus_selector_survival": oracle_vs_selector,
        "oracle_gap_fraction_captured": float(gap_captured),
        "selector_choice_counts": {
            str(k): int(v) for k, v in sorted(Counter(int(x) for x in choices).items())
        },
        "oracle_choice_counts": {
            str(k): int(v) for k, v in sorted(Counter(int(x) for x in oracle_choices).items())
        },
        "selector_oracle_choice_agreement": float(
            np.mean(np.asarray(choices, dtype=int) == np.asarray(oracle_choices, dtype=int))
        ),
        "selector_choices": [int(x) for x in choices],
        "oracle_choices": [int(x) for x in oracle_choices],
        "notes": [
            "Selector features use only detected threats after first sensing plus known assets/defenders/sensors/resources.",
            "Undetected threat state, future outcomes and oracle information are excluded from selector features.",
            "Best fixed program is selected using mean established scalar reward on selector-training seeds.",
            "Oracle is non-deployable and is reported only as development headroom.",
        ],
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2))
    report = [
        "# AegisSwarm Observable Strategy Selector",
        "",
        f"Protocol: `{result['protocol_id']}`",
        f"Training scenarios: {len(train_seeds)}",
        f"Evaluation scenarios: {len(eval_seeds)}",
        "",
        f"- fixed best program index: {fixed_best_index}",
        f"- fixed best survival: {fixed_survival:.4f}",
        f"- selector survival: {selector_survival:.4f}",
        f"- oracle survival: {oracle_survival:.4f}",
        f"- selector-fixed: {survival_delta['second_minus_first']:+.4f} CI={survival_delta['ci95']}",
        f"- oracle gap captured: {gap_captured:.4f}",
        f"- selector choices: {result['selector_choice_counts']}",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== OBSERVABLE STRATEGY SELECTOR ===", flush=True)
    print(f"fixed best program index:        {fixed_best_index}", flush=True)
    print(f"fresh program survivals:         {result['fresh_program_survival_rates']}", flush=True)
    print(f"fixed best survival:             {fixed_survival:.3f}", flush=True)
    print(f"selector survival:               {selector_survival:.3f}", flush=True)
    print(f"oracle survival:                 {oracle_survival:.3f}", flush=True)
    print(
        f"selector - fixed:                {survival_delta['second_minus_first']:+.4f} "
        f"CI={survival_delta['ci95']}",
        flush=True,
    )
    print(
        f"selector - fixed reward:         {reward_delta['second_minus_first']:+.3f} "
        f"CI={reward_delta['ci95']}",
        flush=True,
    )
    print(f"oracle gap captured:             {gap_captured:.3f}", flush=True)
    print(f"selector choice counts:          {result['selector_choice_counts']}", flush=True)
    print(f"oracle choice counts:            {result['oracle_choice_counts']}", flush=True)
    print(
        f"selector/oracle choice agreement: {result['selector_oracle_choice_agreement']:.3f}",
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
