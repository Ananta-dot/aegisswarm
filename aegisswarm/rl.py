from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from .scenarios import ScenarioGenerator
from .simulator import Simulator
from .strategy import GenomePolicy
from .models import ThreatType


TEMPLATES = np.asarray([
    [10, 10, 10, 6, 4, 5, 10, 5],   # balanced
    [15,  7, 12, 9, 3, 3, 12, 3],   # urgent
    [ 8,  8,  9, 4, 8,15, 12,15],   # conserve
    [10, 10, 11, 6, 5, 7, 15, 5],   # decoy aware
    [13,  8, 15,15, 3, 4, 10, 4],   # fast focus
], dtype=np.int16)


def discretize_state(scenario):
    active = [th for th in scenario.threats if th.active and th.threat_type != ThreatType.DECOY]
    detected = [th for th in active if th.detected]
    urgent = []
    for th in detected:
        asset = next(a for a in scenario.assets if a.id == th.target_asset_id)
        if th.distance_to(asset.x, asset.y) < 20.0:
            urgent.append(th)

    remaining = sum(max(0, d.remaining_uses) for d in scenario.defenders)
    total_damage = sum(a.damage / max(a.value, 1e-9) for a in scenario.assets)

    def b(v, cuts):
        return int(sum(v > c for c in cuts))

    return (
        b(len(active), [10, 25, 50]),
        b(len(detected), [5, 15, 30]),
        b(len(urgent), [2, 6, 12]),
        b(remaining, [5, 15, 30]),
        b(total_damage, [0.1, 0.5, 1.0]),
    )


def state_key(state):
    return ",".join(map(str, state))


class QLearningPolicy:
    name = "q_learning"

    def __init__(self, qtable: dict[str, list[float]]):
        self.qtable = qtable

    def reset(self, seed: int):
        self.seed = int(seed)

    def assign(self, scenario, t):
        key = state_key(discretize_state(scenario))
        q = self.qtable.get(key, [0.0] * len(TEMPLATES))
        action = int(np.argmax(q))
        return GenomePolicy(TEMPLATES[action]).assign(scenario, t)


def train_q_learning(
    episodes: int = 1000,
    seed: int = 123,
    n_threats: int = 30,
    n_defenders: int = 8,
    alpha: float = 0.12,
    gamma: float = 0.97,
    epsilon_start: float = 0.35,
    epsilon_end: float = 0.05,
):
    rng = np.random.default_rng(seed)
    gen = ScenarioGenerator()
    q: dict[str, np.ndarray] = {}

    for episode in range(int(episodes)):
        scenario_seed = int(rng.integers(0, 256))
        scenario = gen.generate(
            seed=scenario_seed,
            n_threats=n_threats,
            n_defenders=n_defenders,
        )
        sim = Simulator(scenario)

        eps = epsilon_start + (epsilon_end - epsilon_start) * episode / max(episodes - 1, 1)

        while not sim.is_done():
            sim.sense()
            s = discretize_state(sim.scenario)
            key = state_key(s)
            q.setdefault(key, np.zeros(len(TEMPLATES), dtype=float))

            if rng.random() < eps:
                action = int(rng.integers(0, len(TEMPLATES)))
            else:
                action = int(np.argmax(q[key]))

            assignments = GenomePolicy(TEMPLATES[action]).assign(sim.scenario, sim.t)

            before_alive = sum(a.alive for a in sim.scenario.assets)
            result = sim.step(assignments)
            after_alive = sum(a.alive for a in sim.scenario.assets)

            reward = (
                3.0 * result.contained_real
                - 12.0 * result.penetrations
                - 10.0 * (before_alive - after_alive)
                - 2.0 * result.damage_added
                - 0.08 * result.resources_used
            )

            s2 = discretize_state(sim.scenario)
            key2 = state_key(s2)
            q.setdefault(key2, np.zeros(len(TEMPLATES), dtype=float))
            target = reward if result.done else reward + gamma * float(np.max(q[key2]))
            q[key][action] += alpha * (target - q[key][action])

    return {k: [float(x) for x in v] for k, v in q.items()}


def save_qtable(qtable, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(qtable, indent=2))


def load_qtable(path):
    return json.loads(Path(path).read_text())
