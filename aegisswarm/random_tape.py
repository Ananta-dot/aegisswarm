from __future__ import annotations

import hashlib
import math


class IndexedRandomTape:
    """Policy-independent deterministic random draws keyed by event identity.

    The legacy simulator consumes one sequential RNG stream, so policy-dependent
    control flow can shift which later random numbers correspond to detection,
    motion, and interaction events. This tape instead derives each draw from
    `(scenario_seed, event_key...)`.

    It is intentionally stateless: querying events in a different order does not
    change any event's random value.
    """

    def __init__(self, seed: int):
        self.seed = int(seed)

    def _u64(self, *parts) -> int:
        payload = "|".join([str(self.seed), *(str(p) for p in parts)]).encode("utf-8")
        digest = hashlib.blake2b(payload, digest_size=8, person=b"AegisRNG").digest()
        return int.from_bytes(digest, byteorder="big", signed=False)

    def uniform(self, *parts) -> float:
        # Midpoint mapping avoids exact 0/1, which is useful for Box-Muller.
        return (self._u64(*parts) + 0.5) / float(2**64)

    def normal(self, *parts) -> float:
        # Box-Muller from two independently keyed uniforms.
        u1 = self.uniform(*parts, "normal-u1")
        u2 = self.uniform(*parts, "normal-u2")
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
