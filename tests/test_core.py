import numpy as np

from aegisswarm.scenarios import ScenarioGenerator
from aegisswarm.simulator import Simulator
from aegisswarm.policies import BASELINE_POLICIES
from aegisswarm.optimization import HungarianPolicy
from aegisswarm.strategy import random_genome, GenomePolicy, GENOME_LENGTH, GENE_LEVELS
from aegisswarm.scoring import EvalConfig, evaluate_genome


def test_reproducible_scenario():
    gen = ScenarioGenerator()
    a = gen.generate(seed=42, n_threats=12)
    b = gen.generate(seed=42, n_threats=12)
    assert [(x.x, x.y, x.vx, x.vy, x.threat_type) for x in a.threats] == [
        (x.x, x.y, x.vx, x.vy, x.threat_type) for x in b.threats
    ]


def test_all_baselines_run():
    gen = ScenarioGenerator(max_steps=60)
    base = gen.generate(seed=9, n_threats=12, n_defenders=5)
    policies = [cls() for cls in BASELINE_POLICIES.values()] + [HungarianPolicy()]
    for policy in policies:
        m = Simulator.evaluate_policy(gen.clone(base), policy)
        assert 0.0 <= m.asset_survival_rate <= 1.0
        assert 0.0 <= m.containment_rate <= 1.0
        assert m.cumulative_damage >= 0.0


def test_genome_bounds_and_score():
    rng = np.random.default_rng(1)
    g = random_genome(rng)
    assert g.shape == (GENOME_LENGTH,)
    assert np.all(g >= 0)
    assert np.all(g < GENE_LEVELS)
    metrics = evaluate_genome(
        g,
        EvalConfig(seeds=(0, 1), n_threats=12, n_defenders=5, max_steps=60),
    )
    assert metrics["fitness"] >= 0.0


def test_same_policy_same_seed_same_result():
    gen = ScenarioGenerator(max_steps=60)
    genes = np.array([8] * GENOME_LENGTH, dtype=np.int16)
    a = gen.generate(seed=123, n_threats=12, n_defenders=5)
    b = gen.generate(seed=123, n_threats=12, n_defenders=5)
    ma = Simulator.evaluate_policy(a, GenomePolicy(genes))
    mb = Simulator.evaluate_policy(b, GenomePolicy(genes))
    assert ma.as_dict() == mb.as_dict()
