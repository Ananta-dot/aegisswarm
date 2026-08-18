import numpy as np
import pytest

from aegisswarm.adaptive_rl import (
    AdaptiveEpisode,
    N_MODES,
    OBS_DIM,
    REWARD_SCALE,
    TacticalModeBank,
    adaptive_observation,
)
from aegisswarm.models import ThreatType
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator_v2 import SimulatorV2
from aegisswarm.splits import (
    EVIDENCE_DEV_SEEDS,
    ORACLE_DECOMP_DEV_SEEDS,
    ORACLE_DECOMP_REPLICATION_SEEDS,
    PPO_CONFIRM_SEEDS,
    PPO_DEV_SEEDS,
    PPO_TRAIN_SEEDS,
    RELIABILITY_DEV_SEEDS,
    ROBUST_DEV_SEEDS,
    SELECTOR_CONFIRM_SEEDS,
    SELECTOR_DEV_SEEDS,
    SELECTOR_TRAIN_SEEDS,
    STOCHASTIC_ABLATION_DEV_SEEDS,
)


PROGRAM = np.asarray(
    [
        1, 0, 0, 0, 0,
        1, 1, 2, 1, 2,
        1, 3, 1, 0, 2,
        1, 4, 0, 0, 1,
        1, 5, 0, 4, 2,
        1, 6, 0, 5, 2,
        1, 7, 1, 0, 1,
        0, 0, 0, 0, 0,
        0, 0, 0, 0, 0,
        0, 0, 0, 0, 0,
        0, 0, 0, 0, 0,
        0, 0, 0, 0, 0,
    ],
    dtype=np.int16,
)


def _observable_scenario(seed=71):
    scenario = ScenarioGenerator().generate(seed=seed)
    # Make a small detected cluster reachable so every tactical mode has a
    # meaningful feasibility check independent of initial sensor geometry.
    for i, th in enumerate(scenario.threats[:3]):
        defender = scenario.defenders[i % len(scenario.defenders)]
        th.detected = True
        th.first_detected_t = 0
        th.x = defender.x + 1.0
        th.y = defender.y
    return scenario


def test_adaptive_observation_ignores_undetected_threat_state():
    scenario = _observable_scenario(72)
    hidden = next(th for th in scenario.threats if not th.detected)

    sim = SimulatorV2(scenario)
    sim._update_overload_diagnostic()
    first = adaptive_observation(scenario, sim, [], -1)

    altered = ScenarioGenerator.clone(scenario)
    changed = next(th for th in altered.threats if th.id == hidden.id)
    changed.x += 43.0
    changed.y -= 31.0
    changed.vx *= -3.0
    changed.vy *= 2.0
    changed.threat_type = (
        ThreatType.FAST if changed.threat_type != ThreatType.FAST else ThreatType.DECOY
    )
    changed.target_asset_id = (changed.target_asset_id + 1) % len(altered.assets)

    sim2 = SimulatorV2(altered)
    sim2._update_overload_diagnostic()
    second = adaptive_observation(altered, sim2, [], -1)

    assert first.shape == (OBS_DIM,)
    np.testing.assert_allclose(first, second, rtol=0.0, atol=0.0)


def test_every_tactical_mode_returns_feasible_abstract_assignments():
    scenario = _observable_scenario(73)
    bank = TacticalModeBank(PROGRAM)
    bank.reset(scenario.seed)
    defenders = {d.id: d for d in scenario.defenders}
    threats = {th.id: th for th in scenario.threats}

    for mode in range(N_MODES):
        assignments = bank.assign(scenario, 0, mode, [(2, 1), (1, 1)])
        assert set(assignments) == set(defenders)
        for defender_id, threat_id in assignments.items():
            if threat_id is None:
                continue
            defender = defenders[defender_id]
            threat = threats[threat_id]
            assert defender.available
            assert defender.remaining_uses > 0
            assert threat.active
            assert threat.detected
            assert threat.distance_to(defender.x, defender.y) <= defender.range


def test_shaped_reward_telescopes_to_established_episode_score_difference():
    episode = AdaptiveEpisode(PROGRAM)
    episode.reset(74)
    total = 0.0
    final_info = None

    while True:
        _, reward, terminated, truncated, info = episode.step(0)
        total += float(reward)
        if terminated or truncated:
            final_info = info
            break

    assert final_info is not None
    expected = (
        float(final_info["established_episode_reward"]) - float(episode.initial_score)
    )
    assert total * REWARD_SCALE == pytest.approx(expected, abs=1e-9)
    assert float(final_info["shaped_return_unscaled"]) == pytest.approx(expected, abs=1e-9)


def test_ppo_seed_blocks_are_fresh_and_disjoint():
    train = set(PPO_TRAIN_SEEDS)
    dev = set(PPO_DEV_SEEDS)
    confirm = set(PPO_CONFIRM_SEEDS)
    assert train.isdisjoint(dev)
    assert train.isdisjoint(confirm)
    assert dev.isdisjoint(confirm)

    prior = set(EVIDENCE_DEV_SEEDS)
    prior.update(RELIABILITY_DEV_SEEDS)
    prior.update(ROBUST_DEV_SEEDS)
    prior.update(STOCHASTIC_ABLATION_DEV_SEEDS)
    prior.update(SELECTOR_TRAIN_SEEDS)
    prior.update(SELECTOR_DEV_SEEDS)
    prior.update(SELECTOR_CONFIRM_SEEDS)
    prior.update(ORACLE_DECOMP_DEV_SEEDS)
    prior.update(ORACLE_DECOMP_REPLICATION_SEEDS)

    assert train.isdisjoint(prior)
    assert dev.isdisjoint(prior)
    assert confirm.isdisjoint(prior)


def test_gym_wrapper_shapes_when_optional_dependencies_available():
    gym = pytest.importorskip("gymnasium")
    from aegisswarm.adaptive_rl import AegisSwarmAdaptiveEnv

    env = AegisSwarmAdaptiveEnv(PROGRAM, scenario_seeds=(75,), fixed_scenario_seed=75)
    obs, info = env.reset(seed=75)
    assert obs.shape == (OBS_DIM,)
    assert env.observation_space.contains(obs)
    assert env.action_space.n == N_MODES
    assert info["scenario_seed"] == 75
    env.close()
