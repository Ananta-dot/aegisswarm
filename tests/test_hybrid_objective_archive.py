from aegisswarm.axplorer_v2 import select_diverse_archive


def test_archive_accepts_hybrid_metric_schema():
    metrics = {
        "fitness": 1.0,
        "loss": 1.0,
        "asset_survival_rate": 1.0,
        "containment_rate": 1.0,
        "penetrations": 0.0,
        "cumulative_damage": 0.0,
        "defenders_consumed": 1.0,
        "mean_response_delay": 1.0,
    }
    cache = {tuple([0] * 60): metrics}
    archive = select_diverse_archive(cache, max_size=8)
    assert len(archive) == 1
