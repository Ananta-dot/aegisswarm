from aegisswarm.hybrid_objective_proof import PROTOCOL_ID


def test_hybrid_objective_protocol_id_is_versioned():
    assert PROTOCOL_ID == "aegisswarm-hybrid-objective-v1"
