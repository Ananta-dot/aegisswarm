import numpy as np

from aegisswarm.models import ThreatType
from aegisswarm.rule_program import PROGRAM_LENGTH
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator_v2 import SimulatorV2
from aegisswarm.splits import (
    EVIDENCE_DEV_SEEDS,
    RELIABILITY_DEV_SEEDS,
    ROBUST_DEV_SEEDS,
    STOCHASTIC_ABLATION_DEV_SEEDS,
    STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS,
    SELECTOR_CONFIRM_SEEDS,
    SELECTOR_DEV_SEEDS,
    SELECTOR_TRAIN_SEEDS,
)
from aegisswarm.strategy_selector import (
    FEATURE_NAMES,
    ObservableStrategySelectorPolicy,
    RidgeRewardSelectorModel,
    feature_for_seed,
    observable_features,
)


def test_observable_features_ignore_undetected_threat_state():
    scenario = ScenarioGenerator().generate(seed=17)
    scenario.threats[0].detected = True
    scenario.threats[0].first_detected_t = 0

    altered = ScenarioGenerator.clone(scenario)
    hidden = altered.threats[1]
    assert not hidden.detected
    hidden.x += 37.0
    hidden.y -= 23.0
    hidden.vx *= -2.0
    hidden.vy *= 3.0
    hidden.threat_type = ThreatType.FAST if hidden.threat_type != ThreatType.FAST else ThreatType.DECOY
    hidden.target_asset_id = (hidden.target_asset_id + 1) % len(altered.assets)

    np.testing.assert_allclose(
        observable_features(scenario),
        observable_features(altered),
        rtol=0.0,
        atol=0.0,
    )


def test_observable_features_respond_to_detected_track_state():
    scenario = ScenarioGenerator().generate(seed=18)
    scenario.threats[0].detected = True
    scenario.threats[0].first_detected_t = 0

    altered = ScenarioGenerator.clone(scenario)
    altered.threats[0].x += 8.0
    altered.threats[0].y += 5.0

    first = observable_features(scenario)
    second = observable_features(altered)
    assert first.shape == (len(FEATURE_NAMES),)
    assert not np.allclose(first, second)


def test_feature_snapshot_is_deterministic_for_seed():
    np.testing.assert_allclose(feature_for_seed(28001), feature_for_seed(28001))


def test_ridge_reward_selector_can_learn_contextual_preference():
    x = np.asarray([[-2.0], [-1.0], [1.0], [2.0]], dtype=float)
    rewards = np.asarray(
        [
            [10.0, 0.0],
            [8.0, 1.0],
            [1.0, 8.0],
            [0.0, 10.0],
        ],
        dtype=float,
    )
    model = RidgeRewardSelectorModel.fit(x, rewards, alpha=0.1)
    choices = model.choose(np.asarray([[-3.0], [3.0]], dtype=float))
    assert choices.tolist() == [0, 1]


def test_selector_policy_commits_to_predicted_frozen_program():
    n_features = len(FEATURE_NAMES)
    model = RidgeRewardSelectorModel(
        feature_mean=np.zeros(n_features, dtype=float),
        feature_scale=np.ones(n_features, dtype=float),
        reward_mean=np.asarray([10.0, 0.0], dtype=float),
        coefficients=np.zeros((n_features, 2), dtype=float),
        alpha=1.0,
    )
    programs = [
        np.zeros(PROGRAM_LENGTH, dtype=np.int16),
        np.ones(PROGRAM_LENGTH, dtype=np.int16),
    ]
    policy = ObservableStrategySelectorPolicy(programs, model)
    scenario = ScenarioGenerator().generate(seed=23)
    SimulatorV2.evaluate_policy(scenario, policy)
    assert policy.selected_index == 0


def test_selector_seed_blocks_are_fresh_and_disjoint():
    selector_train = set(SELECTOR_TRAIN_SEEDS)
    selector_dev = set(SELECTOR_DEV_SEEDS)
    selector_confirm = set(SELECTOR_CONFIRM_SEEDS)

    assert selector_train.isdisjoint(selector_dev)
    assert selector_train.isdisjoint(selector_confirm)
    assert selector_dev.isdisjoint(selector_confirm)

    prior = set(EVIDENCE_DEV_SEEDS)
    prior.update(RELIABILITY_DEV_SEEDS)
    prior.update(ROBUST_DEV_SEEDS)
    prior.update(STOCHASTIC_ABLATION_TRAIN_WORLD_SEEDS)
    prior.update(STOCHASTIC_ABLATION_DEV_SEEDS)

    assert selector_train.isdisjoint(prior)
    assert selector_dev.isdisjoint(prior)
    assert selector_confirm.isdisjoint(prior)
