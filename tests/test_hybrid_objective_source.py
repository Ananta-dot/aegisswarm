from aegisswarm.hybrid_objective_proof import PROTOCOL_ID


def test_source_protocol_identity():
    assert PROTOCOL_ID.startswith("aegisswarm-hybrid-objective")
