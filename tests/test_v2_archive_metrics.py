import numpy as np

from aegisswarm.axplorer_v2 import select_diverse_archive
from aegisswarm.rule_program import random_program
from aegisswarm.rule_search import evaluate_rule_program
from aegisswarm.scoring import EvalConfig


def test_rule_evaluation_exposes_archive_metrics_and_archive_builds():
    rng = np.random.default_rng(123)
    config = EvalConfig(seeds=(0,), n_threats=12, n_defenders=4, n_assets=2, n_sensors=2, max_steps=60)

    cache = {}
    for _ in range(4):
        program = random_program(rng)
        metrics = evaluate_rule_program(program, config)
        assert "penetrations" in metrics
        assert "asset_survival_rate" in metrics
        assert "containment_rate" in metrics
        assert "cumulative_damage" in metrics
        assert "defenders_consumed" in metrics
        assert "mean_response_delay" in metrics
        cache[tuple(int(x) for x in program)] = metrics

    archive = select_diverse_archive(cache, max_size=8)
    assert archive
    assert all("penetrations" in entry.metrics for entry in archive)
