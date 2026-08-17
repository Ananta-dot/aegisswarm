import numpy as np

from aegisswarm.axplorer_v2 import canonicalize_program
from aegisswarm.rule_program import PROGRAM_LENGTH


def test_hybrid_objective_program_shape_is_fixed():
    p = canonicalize_program(np.zeros(PROGRAM_LENGTH, dtype=np.int16))
    assert p.shape == (PROGRAM_LENGTH,)
