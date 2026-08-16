from pathlib import Path

from aegisswarm.rl import train_q_learning, QLearningPolicy
from aegisswarm.axplorer_lite import train_axplorer_style
from aegisswarm.scoring import EvalConfig
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator import Simulator


def test_q_learning_smoke():
    q = train_q_learning(episodes=3, seed=1, n_threats=10, n_defenders=4)
    assert isinstance(q, dict)
    assert len(q) > 0
    gen = ScenarioGenerator(max_steps=50)
    s = gen.generate(seed=99, n_threats=10, n_defenders=4)
    m = Simulator.evaluate_policy(s, QLearningPolicy(q))
    assert 0.0 <= m.asset_survival_rate <= 1.0


def test_axplorer_style_smoke():
    cfg = EvalConfig(
        seeds=(0, 1),
        n_threats=10,
        n_defenders=4,
        max_steps=50,
    )
    best, history, _model = train_axplorer_style(
        cfg,
        seed=1,
        epochs=1,
        population=8,
        samples_per_epoch=4,
        train_steps=2,
        local_search_trials=1,
        device="cpu",
    )
    assert len(history) == 1
    assert "best_genome" in best
    assert best["fitness"] >= 0.0
