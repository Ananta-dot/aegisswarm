from aegisswarm.hybrid_objective_proof import (
    ARCHIVE_SIZE,
    ORACLE_BUDGET,
    SEARCH_SEEDS,
    TRAIN_SCENARIOS,
)


def test_hybrid_objective_protocol_is_matched():
    assert len(SEARCH_SEEDS) == 5
    assert TRAIN_SCENARIOS == 16
    assert ORACLE_BUDGET == 1800
    assert ARCHIVE_SIZE >= 64
