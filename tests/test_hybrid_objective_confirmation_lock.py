import json

import pytest

from aegisswarm.hybrid_objective_proof import run_hybrid_objective_confirmation


def test_confirmation_is_locked_until_architecture_is_frozen(tmp_path):
    source = tmp_path / "dev"
    source.mkdir()
    (source / "protocol.json").write_text(json.dumps({"architecture_frozen": False}))
    with pytest.raises(RuntimeError, match="confirmation is locked"):
        run_hybrid_objective_confirmation(source_dir=source, out_dir=tmp_path / "confirm")
