from __future__ import annotations

import json
from collections import Counter, deque
from pathlib import Path

import numpy as np

from .evidence_hardening import load_incumbent_programs
from .hybrid import RuleGuidedHungarianPolicy
from .hybrid_ablation import SCENARIO_KWARGS
from .models import ThreatType
from .policies import distance_to_target
from .reliability import (
    ReliabilityAwareBackupPolicy,
    ReliabilityWeightedHungarianPolicy,
    abstract_success_probability,
)
from .scenarios import ScenarioGenerator
from .simulator_v2 import SimulatorV2
from .splits import PPO_DEV_SEEDS, PPO_TRAIN_SEEDS
from .strategy_selector import FEATURE_NAMES as SELECTOR_FEATURE_NAMES
from .strategy_selector import episode_reward, observable_features


PROTOCOL_ID = "aegisswarm-hierarchical-ppo-v1"
DEFAULT_SOURCE_DIR = "artifacts/optimizer_native_v2_dev"
BASE_PROGRAM_INDEX = 1
MODE_NAMES = (
    "incumbent",
    "urgency",
    "conserve",
    "reliability",
    "backup",
    "failure_recovery",
)
N_MODES = len(MODE_NAMES)
REWARD_SCALE = 10.0
QUICK_MODEL_SEEDS = (42101, 42102)
FULL_MODEL_SEEDS = (42101, 42102, 42103, 42104, 42105)
QUICK_TIMESTEPS = 100_000
FULL_TIMESTEPS = 500_000
QUICK_EVAL_COUNT = 20
QUICK_CALIBRATION_COUNT = 100
FULL_CALIBRATION_COUNT = 400

# Normalize the already leakage-tested t=0 observable feature family to roughly
# O(1) ranges. These are simulator-scale constants, not learned statistics.
_BASE_FEATURE_SCALES = np.asarray(
    [
        30.0,  # detected_total
        30.0,  # detected_real
        30.0,  # detected_direct
        30.0,  # detected_fast
        30.0,  # detected_decoy
        150.0,  # mean_time_to_target
        150.0,  # min_time_to_target
        100.0,  # mean_target_distance
        100.0,  # min_target_distance
        2.0,  # mean_detected_speed
        2.0,  # max_detected_speed
        8.0,  # mean_reachable_defenders
        1.0,  # fraction_zero_reach
        1.0,  # fraction_one_reach
        1.0,  # fraction_multi_reach
        8.0,  # available_defenders
        40.0,  # total_remaining_uses
        5.0,  # mean_remaining_uses
        5.0,  # min_remaining_uses
        1.2,  # mean_defender_capacity
        30.0,  # mean_defender_range
        5.0,  # detected_real_per_available_defender
        1.0,  # mean_sensor_detection_probability
        55.0,  # mean_sensor_range
        4.0,  # total_asset_value
    ],
    dtype=float,
)

DERIVED_FEATURE_NAMES = (
    "t_fraction",
    "damage_fraction",
    "penetration_fraction",
    "resource_use_fraction",
    "cumulative_failure_rate",
    "recent_failure_rate_1",
    "recent_failure_rate_3",
    "recent_failure_rate_5",
    "overload_fraction",
    "resource_exhausted",
)
OBS_FEATURE_NAMES = (
    tuple(SELECTOR_FEATURE_NAMES)
    + DERIVED_FEATURE_NAMES
    + tuple(f"last_mode_{name}" for name in MODE_NAMES)
)
OBS_DIM = len(OBS_FEATURE_NAMES)


def _recent_failure_rate(history, window: int) -> float:
    rows = list(history)[-int(window) :]
    attempts = sum(int(a) for a, _ in rows)
    failures = sum(int(f) for _, f in rows)
    return float(failures / attempts) if attempts > 0 else 0.0


def _current_overload_pressure(scenario) -> float:
    defenders = [
        d for d in scenario.defenders if d.available and d.remaining_uses > 0
    ]
    if not defenders:
        return 1.0
    reachable_real = 0
    for th in scenario.threats:
        if not th.active or not th.detected or th.threat_type == ThreatType.DECOY:
            continue
        if any(th.distance_to(d.x, d.y) <= d.range for d in defenders):
            reachable_real += 1
    return float(np.clip(reachable_real / max(len(defenders), 1) - 1.0, 0.0, 1.0))


class AdaptiveObjectiveHungarianPolicy(RuleGuidedHungarianPolicy):
    """Small tactical adjustment around the frozen rule-guided objective."""

    def __init__(
        self,
        tokens,
        *,
        urgency_gain: float = 0.0,
        fast_gain: float = 0.0,
        direct_gain: float = 0.0,
        decoy_penalty: float = 0.0,
        reliability_mix: float = 0.0,
        conserve_last_use: bool = False,
        dynamic_context: bool = False,
        name: str = "adaptive_objective_hungarian",
    ):
        super().__init__(tokens, name=name)
        self.urgency_gain = float(urgency_gain)
        self.fast_gain = float(fast_gain)
        self.direct_gain = float(direct_gain)
        self.decoy_penalty = float(decoy_penalty)
        self.reliability_mix = float(np.clip(reliability_mix, 0.0, 1.0))
        self.conserve_last_use = bool(conserve_last_use)
        self.dynamic_context = bool(dynamic_context)
        self.failure_pressure = 0.0
        self.overload_pressure = 0.0

    def set_context(self, failure_pressure: float, overload_pressure: float):
        self.failure_pressure = float(np.clip(failure_pressure, 0.0, 1.0))
        self.overload_pressure = float(np.clip(overload_pressure, 0.0, 1.0))

    def pair_utility(self, scenario, defender, threat):
        value = super().pair_utility(scenario, defender, threat)
        if value is None:
            return None

        d_asset = distance_to_target(scenario, threat)
        urgency = float(np.clip(1.0 - d_asset / 40.0, 0.0, 1.0))

        urgency_gain = self.urgency_gain
        reliability_mix = self.reliability_mix
        if self.dynamic_context:
            urgency_gain += 2.0 * self.overload_pressure
            reliability_mix = float(
                np.clip(
                    reliability_mix + 0.55 * self.failure_pressure,
                    0.0,
                    0.85,
                )
            )

        value += urgency_gain * urgency
        if threat.threat_type == ThreatType.FAST:
            value += self.fast_gain
        elif threat.threat_type == ThreatType.DIRECT:
            value += self.direct_gain
        else:
            value -= self.decoy_penalty

        if (
            self.conserve_last_use
            and defender.remaining_uses <= 1
            and d_asset > 16.0
            and threat.threat_type != ThreatType.FAST
        ):
            return None

        if reliability_mix > 0.0:
            p_success = abstract_success_probability(defender, threat)
            multiplier = (1.0 - reliability_mix) + reliability_mix * p_success
            value *= multiplier
        return float(value)


class TacticalModeBank:
    """Six abstract tactical modes sharing the same frozen strategic program."""

    def __init__(self, tokens):
        tokens = np.asarray(tokens, dtype=np.int16)
        self.policies = (
            RuleGuidedHungarianPolicy(tokens, name="ppo_mode_incumbent"),
            AdaptiveObjectiveHungarianPolicy(
                tokens,
                urgency_gain=3.0,
                fast_gain=0.75,
                direct_gain=0.25,
                name="ppo_mode_urgency",
            ),
            AdaptiveObjectiveHungarianPolicy(
                tokens,
                reliability_mix=0.15,
                conserve_last_use=True,
                decoy_penalty=0.25,
                name="ppo_mode_conserve",
            ),
            ReliabilityWeightedHungarianPolicy(tokens, name="ppo_mode_reliability"),
            ReliabilityAwareBackupPolicy(tokens, name="ppo_mode_backup"),
            AdaptiveObjectiveHungarianPolicy(
                tokens,
                urgency_gain=1.5,
                fast_gain=0.50,
                direct_gain=0.25,
                reliability_mix=0.25,
                dynamic_context=True,
                name="ppo_mode_failure_recovery",
            ),
        )

    def reset(self, seed: int):
        for policy in self.policies:
            policy.reset(int(seed))

    def assign(self, scenario, t: int, mode: int, history):
        mode = int(mode)
        if mode < 0 or mode >= N_MODES:
            raise ValueError(f"invalid tactical mode {mode}")
        policy = self.policies[mode]
        if isinstance(policy, AdaptiveObjectiveHungarianPolicy) and policy.dynamic_context:
            policy.set_context(
                _recent_failure_rate(history, 5),
                _current_overload_pressure(scenario),
            )
        return policy.assign(scenario, int(t))


def adaptive_observation(scenario, simulator: SimulatorV2, history, last_mode: int) -> np.ndarray:
    base = observable_features(scenario)
    if base.shape != _BASE_FEATURE_SCALES.shape:
        raise RuntimeError("selector feature shape changed; update PPO normalization")
    base = np.clip(base / _BASE_FEATURE_SCALES, 0.0, 2.0)

    diag = simulator.diagnostics()
    initial_uses = max(float(scenario.metadata.get("initial_defender_uses", 1.0)), 1.0)
    real_total = max(
        sum(int(th.threat_type != ThreatType.DECOY) for th in scenario.threats),
        1,
    )
    total_asset_value = max(float(sum(a.value for a in scenario.assets)), 1e-9)
    attempts = float(diag.get("real_interaction_attempts", 0))
    failures = float(diag.get("real_interaction_failures", 0))

    derived = np.asarray(
        [
            float(simulator.t / max(scenario.max_steps, 1)),
            float(np.clip(simulator.cumulative_damage / total_asset_value, 0.0, 2.0)),
            float(np.clip(simulator.total_penetrations / real_total, 0.0, 1.0)),
            float(np.clip(simulator.total_resources_used / initial_uses, 0.0, 1.5)),
            float(failures / attempts) if attempts > 0 else 0.0,
            _recent_failure_rate(history, 1),
            _recent_failure_rate(history, 3),
            _recent_failure_rate(history, 5),
            float(
                np.clip(
                    float(diag.get("overload_steps", 0)) / max(simulator.t + 1, 1),
                    0.0,
                    1.0,
                )
            ),
            float(bool(diag.get("resource_exhausted", False))),
        ],
        dtype=float,
    )

    last = np.zeros(N_MODES, dtype=float)
    if 0 <= int(last_mode) < N_MODES:
        last[int(last_mode)] = 1.0
    obs = np.concatenate([base, derived, last]).astype(np.float32)
    if obs.shape != (OBS_DIM,):
        raise RuntimeError(f"adaptive observation shape mismatch: {obs.shape} != {(OBS_DIM,)}")
    return obs


class AdaptiveEpisode:
    """Gym-independent one-episode state machine for testing and evaluation."""

    def __init__(self, program, scenario_kwargs=None):
        self.program = np.asarray(program, dtype=np.int16).copy()
        self.scenario_kwargs = dict(scenario_kwargs or SCENARIO_KWARGS)
        self.scenario = None
        self.simulator = None
        self.mode_bank = None
        self.history = deque(maxlen=5)
        self.last_mode = -1
        self._previous_score = 0.0
        self.initial_score = 0.0

    def reset(self, scenario_seed: int) -> np.ndarray:
        kwargs = dict(self.scenario_kwargs)
        max_steps = int(kwargs.pop("max_steps", 150))
        self.scenario = ScenarioGenerator(max_steps=max_steps).generate(
            seed=int(scenario_seed), **kwargs
        )
        self.simulator = SimulatorV2(self.scenario)
        self.mode_bank = TacticalModeBank(self.program)
        self.mode_bank.reset(int(scenario_seed))
        self.history.clear()
        self.last_mode = -1

        self.simulator.sense()
        self.simulator._update_overload_diagnostic()
        self.initial_score = episode_reward(
            self.simulator.metrics("ppo_partial").as_dict()
        )
        self._previous_score = float(self.initial_score)
        return adaptive_observation(
            self.scenario, self.simulator, self.history, self.last_mode
        )

    def _termination_flags(self):
        real_active = any(
            th.active and th.threat_type != ThreatType.DECOY
            for th in self.scenario.threats
        )
        terminated = not real_active
        truncated = bool(real_active and self.simulator.t >= self.scenario.max_steps)
        return terminated, truncated

    def step(self, mode: int):
        if self.scenario is None or self.simulator is None:
            raise RuntimeError("episode must be reset before step")
        terminated, truncated = self._termination_flags()
        if terminated or truncated:
            raise RuntimeError("cannot step a completed episode")

        before = self.simulator.diagnostics()
        assignments = self.mode_bank.assign(
            self.scenario,
            self.simulator.t,
            int(mode),
            self.history,
        )
        step_result = self.simulator.step(assignments)
        after = self.simulator.diagnostics()
        attempts_delta = int(after["real_interaction_attempts"] - before["real_interaction_attempts"])
        failures_delta = int(after["real_interaction_failures"] - before["real_interaction_failures"])
        self.history.append((attempts_delta, failures_delta))
        self.last_mode = int(mode)

        current_score = episode_reward(
            self.simulator.metrics("ppo_adaptive").as_dict()
        )
        reward = float((current_score - self._previous_score) / REWARD_SCALE)
        self._previous_score = float(current_score)

        terminated, truncated = self._termination_flags()
        if not (terminated or truncated):
            self.simulator.sense()
            self.simulator._update_overload_diagnostic()

        obs = adaptive_observation(
            self.scenario, self.simulator, self.history, self.last_mode
        )
        info = {
            "mode": int(mode),
            "mode_name": MODE_NAMES[int(mode)],
            "score": float(current_score),
            "attempts_delta": attempts_delta,
            "failures_delta": failures_delta,
            "step": {
                "contained_real": int(step_result.contained_real),
                "penetrations": int(step_result.penetrations),
                "damage_added": float(step_result.damage_added),
                "resources_used": int(step_result.resources_used),
            },
        }
        if terminated or truncated:
            info["metrics"] = self.simulator.metrics("ppo_adaptive").as_dict()
            info["diagnostics"] = self.simulator.diagnostics()
            info["established_episode_reward"] = float(current_score)
            info["shaped_return_unscaled"] = float(current_score - self.initial_score)
        return obs, reward, terminated, truncated, info


try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:  # pragma: no cover - exercised only without optional RL deps.
    gym = None
    spaces = None


if gym is not None:

    class AegisSwarmAdaptiveEnv(gym.Env):
        """Gymnasium wrapper around AdaptiveEpisode for hierarchical PPO."""

        metadata = {"render_modes": []}

        def __init__(
            self,
            program,
            scenario_seeds=PPO_TRAIN_SEEDS,
            *,
            fixed_scenario_seed=None,
            base_rng_seed: int = 0,
            scenario_kwargs=None,
        ):
            super().__init__()
            self.program = np.asarray(program, dtype=np.int16).copy()
            self.scenario_seeds = tuple(int(x) for x in scenario_seeds)
            if not self.scenario_seeds and fixed_scenario_seed is None:
                raise ValueError("scenario seed pool must not be empty")
            self.fixed_scenario_seed = (
                None if fixed_scenario_seed is None else int(fixed_scenario_seed)
            )
            self.base_rng_seed = int(base_rng_seed)
            self._first_reset = True
            self.episode = AdaptiveEpisode(self.program, scenario_kwargs=scenario_kwargs)
            self.action_space = spaces.Discrete(N_MODES)
            self.observation_space = spaces.Box(
                low=np.zeros(OBS_DIM, dtype=np.float32),
                high=np.full(OBS_DIM, 2.0, dtype=np.float32),
                dtype=np.float32,
            )

        def reset(self, *, seed=None, options=None):
            if seed is None and self._first_reset:
                seed = self.base_rng_seed
            super().reset(seed=seed)
            self._first_reset = False
            if self.fixed_scenario_seed is not None:
                scenario_seed = self.fixed_scenario_seed
            else:
                scenario_seed = int(self.np_random.choice(self.scenario_seeds))
            obs = self.episode.reset(scenario_seed)
            return obs, {"scenario_seed": int(scenario_seed)}

        def step(self, action):
            return self.episode.step(int(action))

else:

    class AegisSwarmAdaptiveEnv:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "RL dependencies are not installed. Run: pip install -e '.[rl]'"
            )


def run_static_mode(program, mode: int, scenario_seed: int):
    episode = AdaptiveEpisode(program)
    episode.reset(int(scenario_seed))
    mode_counts = Counter()
    while True:
        _, _, terminated, truncated, info = episode.step(int(mode))
        mode_counts[int(mode)] += 1
        if terminated or truncated:
            return dict(info["metrics"]), dict(info["diagnostics"]), mode_counts


def evaluate_static_modes(program, seeds):
    seeds = tuple(int(x) for x in seeds)
    rows_by_mode = []
    rewards_by_mode = []
    for mode in range(N_MODES):
        rows = []
        for seed in seeds:
            row, _, _ = run_static_mode(program, mode, seed)
            rows.append(row)
        rows_by_mode.append(rows)
        rewards_by_mode.append(float(np.mean([episode_reward(row) for row in rows])))
    return rows_by_mode, rewards_by_mode


def _require_sb3():
    if gym is None:
        raise ImportError("Install RL dependencies with: pip install -e '.[rl]'")
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Install RL dependencies with: pip install -e '.[rl]'") from exc
    return PPO, DummyVecEnv, SubprocVecEnv


def train_ppo_model(
    program,
    *,
    model_seed: int,
    train_seeds=PPO_TRAIN_SEEDS,
    total_timesteps: int,
    n_envs: int,
    model_path,
):
    PPO, DummyVecEnv, SubprocVecEnv = _require_sb3()
    n_envs = max(1, int(n_envs))
    program_list = [int(x) for x in np.asarray(program, dtype=np.int16)]

    def make_env(rank):
        def _factory():
            return AegisSwarmAdaptiveEnv(
                program_list,
                train_seeds,
                base_rng_seed=int(model_seed) * 100 + int(rank),
            )

        return _factory

    env_fns = [make_env(rank) for rank in range(n_envs)]
    if n_envs == 1:
        vec_env = DummyVecEnv(env_fns)
    else:
        vec_env = SubprocVecEnv(env_fns, start_method="spawn")

    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=3e-4,
        n_steps=256,
        batch_size=256,
        n_epochs=10,
        gamma=1.0,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs={"net_arch": [128, 128]},
        seed=int(model_seed),
        device="cpu",
        verbose=0,
    )
    model.learn(total_timesteps=int(total_timesteps), progress_bar=False)
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(model_path))
    vec_env.close()
    return model_path


def evaluate_ppo_model(program, model_path, seeds):
    PPO, _, _ = _require_sb3()
    model = PPO.load(str(model_path), device="cpu")
    rows = []
    diagnostics = []
    counts = Counter()
    for scenario_seed in seeds:
        env = AegisSwarmAdaptiveEnv(
            program,
            scenario_seeds=(int(scenario_seed),),
            fixed_scenario_seed=int(scenario_seed),
            base_rng_seed=int(scenario_seed),
        )
        obs, _ = env.reset(seed=int(scenario_seed))
        while True:
            action, _ = model.predict(obs, deterministic=True)
            mode = int(np.asarray(action).item())
            counts[mode] += 1
            obs, _, terminated, truncated, info = env.step(mode)
            if terminated or truncated:
                rows.append(dict(info["metrics"]))
                diagnostics.append(dict(info["diagnostics"]))
                break
        env.close()
    return rows, diagnostics, counts


def _metric_mean(rows, metric):
    return float(np.mean([float(row[metric]) for row in rows]))


def _scenario_bootstrap_delta(first_rows, second_rows, metric, seed=1, n_boot=5000):
    first = np.asarray([float(row[metric]) for row in first_rows], dtype=float)
    second = np.asarray([float(row[metric]) for row in second_rows], dtype=float)
    diff = second - first
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        idx = rng.integers(0, len(diff), size=len(diff))
        draws[i] = float(diff[idx].mean())
    return {
        "mean": float(diff.mean()),
        "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
    }


def _hierarchical_delta(baseline_rows, rows_by_training_run, metric, seed=1, n_boot=5000):
    baseline = np.asarray([float(row[metric]) for row in baseline_rows], dtype=float)
    candidate = np.asarray(
        [[float(row[metric]) for row in rows] for rows in rows_by_training_run],
        dtype=float,
    )
    if candidate.ndim != 2 or candidate.shape[1] != len(baseline):
        raise ValueError("training-run/scenario evaluation matrices are not aligned")
    diff = candidate - baseline[None, :]
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        run_idx = rng.integers(0, diff.shape[0], size=diff.shape[0])
        scenario_idx = rng.integers(0, diff.shape[1], size=diff.shape[1])
        draws[i] = float(diff[np.ix_(run_idx, scenario_idx)].mean())
    return {
        "mean": float(diff.mean()),
        "ci95": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
        "per_training_run": [float(x) for x in diff.mean(axis=1)],
    }


def run_ppo_adaptive_screen(
    *,
    source_dir=DEFAULT_SOURCE_DIR,
    out_dir="artifacts/ppo_adaptive_quick",
    workers=8,
    quick=True,
):
    programs = load_incumbent_programs(source_dir)
    if BASE_PROGRAM_INDEX >= len(programs):
        raise RuntimeError("frozen PPO base-program index is unavailable")
    program = np.asarray(programs[BASE_PROGRAM_INDEX], dtype=np.int16)

    model_seeds = QUICK_MODEL_SEEDS if quick else FULL_MODEL_SEEDS
    total_timesteps = QUICK_TIMESTEPS if quick else FULL_TIMESTEPS
    eval_seeds = (
        tuple(PPO_DEV_SEEDS[:QUICK_EVAL_COUNT]) if quick else tuple(PPO_DEV_SEEDS)
    )
    calibration_count = QUICK_CALIBRATION_COUNT if quick else FULL_CALIBRATION_COUNT
    calibration_seeds = tuple(PPO_TRAIN_SEEDS[:calibration_count])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"AegisSwarm hierarchical PPO | mode={'quick' if quick else 'development'} "
        f"base_program={BASE_PROGRAM_INDEX} models={len(model_seeds)} "
        f"timesteps/model={total_timesteps} eval_scenarios={len(eval_seeds)} "
        f"envs={max(1, min(int(workers), 12))}",
        flush=True,
    )

    calibration_rows, calibration_rewards = evaluate_static_modes(
        program, calibration_seeds
    )
    static_best_mode = int(np.argmax(np.asarray(calibration_rewards, dtype=float)))

    dev_static_rows, _ = evaluate_static_modes(program, eval_seeds)
    incumbent_rows = dev_static_rows[0]
    static_best_rows = dev_static_rows[static_best_mode]

    n_envs = max(1, min(int(workers), 12))
    ppo_rows_by_run = []
    ppo_diag_by_run = []
    mode_counts_by_run = []
    model_paths = []

    for model_seed in model_seeds:
        model_path = out_dir / f"ppo_seed_{int(model_seed)}"
        train_ppo_model(
            program,
            model_seed=int(model_seed),
            train_seeds=PPO_TRAIN_SEEDS,
            total_timesteps=total_timesteps,
            n_envs=n_envs,
            model_path=model_path,
        )
        rows, diagnostics, counts = evaluate_ppo_model(
            program, model_path, eval_seeds
        )
        ppo_rows_by_run.append(rows)
        ppo_diag_by_run.append(diagnostics)
        mode_counts_by_run.append({str(k): int(v) for k, v in sorted(counts.items())})
        model_paths.append(str(model_path) + ".zip")

    incumbent_survival = _metric_mean(incumbent_rows, "asset_survival_rate")
    static_best_survival = _metric_mean(static_best_rows, "asset_survival_rate")
    ppo_survival = float(
        np.mean(
            [
                _metric_mean(rows, "asset_survival_rate")
                for rows in ppo_rows_by_run
            ]
        )
    )

    ppo_vs_inc = _hierarchical_delta(
        incumbent_rows,
        ppo_rows_by_run,
        "asset_survival_rate",
        seed=331001,
    )
    ppo_vs_static = _hierarchical_delta(
        static_best_rows,
        ppo_rows_by_run,
        "asset_survival_rate",
        seed=331101,
    )
    static_vs_inc = _scenario_bootstrap_delta(
        incumbent_rows,
        static_best_rows,
        "asset_survival_rate",
        seed=331201,
    )

    metric_summary = {}
    for metric in (
        "asset_survival_rate",
        "containment_rate",
        "penetrations",
        "cumulative_damage",
        "defenders_consumed",
        "mean_response_delay",
    ):
        metric_summary[metric] = {
            "incumbent": _metric_mean(incumbent_rows, metric),
            "static_best": _metric_mean(static_best_rows, metric),
            "ppo": float(np.mean([_metric_mean(rows, metric) for rows in ppo_rows_by_run])),
        }

    result = {
        "protocol_id": PROTOCOL_ID + ("-quick" if quick else "-development"),
        "mode": "quick" if quick else "development",
        "base_program_index": int(BASE_PROGRAM_INDEX),
        "tactical_modes": list(MODE_NAMES),
        "model_seeds": [int(x) for x in model_seeds],
        "timesteps_per_model": int(total_timesteps),
        "n_envs": int(n_envs),
        "calibration_seeds": [int(x) for x in calibration_seeds],
        "evaluation_seeds": [int(x) for x in eval_seeds],
        "calibration_mean_rewards_by_mode": [float(x) for x in calibration_rewards],
        "static_best_mode_index": int(static_best_mode),
        "static_best_mode_name": MODE_NAMES[static_best_mode],
        "incumbent_survival": incumbent_survival,
        "static_best_survival": static_best_survival,
        "ppo_survival": ppo_survival,
        "static_best_minus_incumbent": static_vs_inc,
        "ppo_minus_incumbent": ppo_vs_inc,
        "ppo_minus_static_best": ppo_vs_static,
        "metric_summary": metric_summary,
        "ppo_mode_counts_by_training_run": mode_counts_by_run,
        "model_paths": model_paths,
        "notes": [
            "PPO never assigns defenders directly; it selects one of six tactical modes each simulator step.",
            "Every mode uses the same frozen 60-token base program and constrained assignment layer.",
            "Static-best tactical mode is selected only on PPO training/calibration seeds.",
            "PPO observations include only detected/known state plus realized interaction/resource history.",
            "Per-step reward is a scaled difference in the established episode score; with gamma=1 the undiscounted shaped return telescopes to final-score minus the common initial score.",
        ],
    }

    (out_dir / "results.json").write_text(json.dumps(result, indent=2))
    report = [
        "# AegisSwarm Hierarchical PPO",
        "",
        f"Protocol: `{result['protocol_id']}`",
        f"Base frozen program: {BASE_PROGRAM_INDEX}",
        f"Static best mode: {static_best_mode} ({MODE_NAMES[static_best_mode]})",
        f"Incumbent survival: {incumbent_survival:.4f}",
        f"Static-best survival: {static_best_survival:.4f}",
        f"PPO survival: {ppo_survival:.4f}",
        f"PPO-incumbent: {ppo_vs_inc['mean']:+.4f} CI={ppo_vs_inc['ci95']}",
        f"PPO-static-best: {ppo_vs_static['mean']:+.4f} CI={ppo_vs_static['ci95']}",
        f"Per-training-run PPO-incumbent: {ppo_vs_inc['per_training_run']}",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(report))

    print("\n=== HIERARCHICAL PPO ADAPTIVE CONTROL ===", flush=True)
    print(f"base frozen program index:       {BASE_PROGRAM_INDEX}", flush=True)
    print(
        f"calibrated static best mode:     {static_best_mode} ({MODE_NAMES[static_best_mode]})",
        flush=True,
    )
    print(f"incumbent survival:              {incumbent_survival:.3f}", flush=True)
    print(f"static-best survival:            {static_best_survival:.3f}", flush=True)
    print(f"PPO adaptive survival:           {ppo_survival:.3f}", flush=True)
    print(
        f"static best - incumbent:         {static_vs_inc['mean']:+.4f} CI={static_vs_inc['ci95']}",
        flush=True,
    )
    print(
        f"PPO - incumbent:                 {ppo_vs_inc['mean']:+.4f} CI={ppo_vs_inc['ci95']}",
        flush=True,
    )
    print(
        f"PPO - static best:               {ppo_vs_static['mean']:+.4f} CI={ppo_vs_static['ci95']}",
        flush=True,
    )
    print(f"PPO per-run deltas:              {ppo_vs_inc['per_training_run']}", flush=True)
    print(f"PPO mode counts/run:             {mode_counts_by_run}", flush=True)
    print(
        "metric means inc/static/PPO:       "
        + json.dumps(metric_summary, sort_keys=True),
        flush=True,
    )
    print(f"Saved: {out_dir}", flush=True)
    return result
