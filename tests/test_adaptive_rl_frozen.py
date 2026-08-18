import pytest

from aegisswarm.adaptive_rl_frozen import (
    FROZEN_EVAL_COUNT,
    FROZEN_EVAL_SEEDS,
    _diagnostic_summary,
    _rows_with_reward,
)
from aegisswarm.splits import PPO_DEV_SEEDS


def test_frozen_eval_slice_is_fresh_relative_to_quick_and_inside_dev_block():
    quick = set(PPO_DEV_SEEDS[:20])
    frozen = set(FROZEN_EVAL_SEEDS)
    assert len(FROZEN_EVAL_SEEDS) == FROZEN_EVAL_COUNT == 100
    assert quick.isdisjoint(frozen)
    assert frozen.issubset(set(PPO_DEV_SEEDS))
    assert FROZEN_EVAL_SEEDS[0] == PPO_DEV_SEEDS[20]
    assert FROZEN_EVAL_SEEDS[-1] == PPO_DEV_SEEDS[119]


def test_rows_with_reward_uses_established_scoring_function():
    rows = [
        {
            "asset_survival_rate": 1.0,
            "containment_rate": 1.0,
            "cumulative_damage": 0.0,
            "defenders_consumed": 0.0,
            "mean_response_delay": 0.0,
        }
    ]
    enriched = _rows_with_reward(rows)
    assert enriched[0]["established_reward"] == pytest.approx(200.0)
    assert "established_reward" not in rows[0]


def test_diagnostic_summary_reports_aggregate_failure_rate_and_exhaustion():
    summary = _diagnostic_summary(
        [
            {
                "real_interaction_attempts": 10,
                "real_interaction_failures": 4,
                "resource_exhausted": True,
                "overload_steps": 5,
                "resource_uses_remaining": 0,
            },
            {
                "real_interaction_attempts": 20,
                "real_interaction_failures": 6,
                "resource_exhausted": False,
                "overload_steps": 7,
                "resource_uses_remaining": 2,
            },
        ]
    )
    assert summary["attempts_mean"] == pytest.approx(15.0)
    assert summary["failures_mean"] == pytest.approx(5.0)
    assert summary["aggregate_failure_rate"] == pytest.approx(10.0 / 30.0)
    assert summary["resource_exhaustion_rate"] == pytest.approx(0.5)
    assert summary["overload_steps_mean"] == pytest.approx(6.0)
    assert summary["resource_uses_remaining_mean"] == pytest.approx(1.0)
