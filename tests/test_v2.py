import numpy as np

from aegisswarm.scoring_v2 import EvalConfigV2, evaluate_genome_v2
from aegisswarm.search_v2 import train_policy_search_v2
from aegisswarm.strategy_v2 import (
    GENOME_V2_LENGTH,
    AdaptiveGenomePolicy,
    decode_genome_v2,
    random_genome_v2,
)
from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator import Simulator


def test_adaptive_genome_runs():
    rng = np.random.default_rng(7)
    genes = random_genome_v2(rng)
    assert genes.shape == (GENOME_V2_LENGTH,)
    assert np.all(genes >= 0)
    assert np.all(genes < 16)
    spec = decode_genome_v2(genes)
    assert spec.imminent_distance_threshold > 0

    gen = ScenarioGenerator(max_steps=50)
    scenario = gen.generate(seed=31, n_threats=10, n_defenders=4)
    metrics = Simulator.evaluate_policy(scenario, AdaptiveGenomePolicy(genes))
    assert 0.0 <= metrics.asset_survival_rate <= 1.0


def test_v2_score_is_deterministic():
    genes = np.asarray([8] * GENOME_V2_LENGTH, dtype=np.int16)
    cfg = EvalConfigV2(seeds=(0, 1), n_threats=10, n_defenders=4, max_steps=50)
    a = evaluate_genome_v2(genes, cfg)
    b = evaluate_genome_v2(genes, cfg)
    assert a == b


def test_v2_search_smoke():
    common = dict(n_threats=8, n_defenders=4, max_steps=40)
    screen = EvalConfigV2(seeds=(0,), **common)
    train = EvalConfigV2(seeds=(0, 1), **common)
    validation = EvalConfigV2(seeds=(1000, 1001), **common)

    best, history, _model, archive = train_policy_search_v2(
        screen,
        train,
        validation,
        seed=3,
        epochs=1,
        population=8,
        samples_per_epoch=4,
        train_steps=2,
        validation_candidates=2,
        local_search_trials=1,
        archive_size=4,
        device="cpu",
    )
    assert len(history) == 1
    assert best is not None
    assert len(best["genes"]) == GENOME_V2_LENGTH
    assert archive.best["validation"]["episodes"] == 2.0
