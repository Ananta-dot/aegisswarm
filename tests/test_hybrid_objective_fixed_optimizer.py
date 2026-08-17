from aegisswarm.hybrid_ablation import evaluate_optimizer_only


def test_fixed_optimizer_baseline_evaluates():
    result = evaluate_optimizer_only((5000,))
    assert result["matrices"]["asset_survival_rate"].shape == (1, 1)
