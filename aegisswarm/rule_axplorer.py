from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .rule_program import TOKEN_LEVELS, PROGRAM_LENGTH, random_program
from .rule_search import evaluate_rule_program, hill_climb_rule_program
from .scoring import EvalConfig


BOS = TOKEN_LEVELS
EOS = TOKEN_LEVELS + 1
VOCAB_SIZE = TOKEN_LEVELS + 2
SEQ_LEN = PROGRAM_LENGTH + 2


class RuleProgramTransformer(nn.Module):
    def __init__(self, d_model=128, nhead=4, layers=4):
        super().__init__()
        self.tok = nn.Embedding(VOCAB_SIZE, d_model)
        self.pos = nn.Embedding(SEQ_LEN, d_model)
        block = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=4 * d_model,
            dropout=0.0,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(block, num_layers=layers)
        self.head = nn.Linear(d_model, VOCAB_SIZE)

    def forward(self, x):
        _, t = x.shape
        pos = torch.arange(t, device=x.device).unsqueeze(0)
        h = self.tok(x) + self.pos(pos)
        mask = torch.triu(torch.ones(t, t, device=x.device, dtype=torch.bool), diagonal=1)
        h = self.encoder(h, mask=mask)
        return self.head(h)


def device_auto():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def encode_program(program):
    return np.asarray([BOS] + [int(x) for x in program] + [EOS], dtype=np.int64)


def train_model(model, programs, steps=300, batch_size=32, lr=3e-4, device="cpu", seed=0):
    rng = np.random.default_rng(seed)
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    seqs = np.stack([encode_program(p) for p in programs])

    for _ in range(int(steps)):
        idx = rng.integers(0, len(seqs), size=min(batch_size, len(seqs)))
        batch = torch.tensor(seqs[idx], dtype=torch.long, device=device)
        x = batch[:, :-1]
        y = batch[:, 1:]
        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, VOCAB_SIZE), y.reshape(-1))
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return model


@torch.no_grad()
def sample_programs(model, n, temperature=0.9, device="cpu", seed=0):
    torch.manual_seed(seed)
    model.eval()
    out = []
    for _ in range(int(n)):
        seq = torch.tensor([[BOS]], dtype=torch.long, device=device)
        tokens = []
        for _step in range(PROGRAM_LENGTH):
            logits = model(seq)[:, -1, :TOKEN_LEVELS] / max(temperature, 1e-4)
            probs = torch.softmax(logits, dim=-1)
            token = int(torch.multinomial(probs, 1).item())
            tokens.append(token)
            seq = torch.cat(
                [seq, torch.tensor([[token]], dtype=torch.long, device=device)],
                dim=1,
            )
        out.append(np.asarray(tokens, dtype=np.int16))
    return out


def unique_programs(programs):
    seen = set()
    out = []
    for p in programs:
        key = tuple(int(x) for x in p)
        if key not in seen:
            seen.add(key)
            out.append(np.asarray(p, dtype=np.int16))
    return out


def train_rule_axplorer(
    config: EvalConfig,
    seed=0,
    epochs=10,
    population=128,
    samples_per_epoch=128,
    train_steps=300,
    elite_fraction=0.25,
    local_search_trials=4,
    temperature=0.9,
    device=None,
):
    rng = np.random.default_rng(seed)
    device = device or device_auto()
    model = RuleProgramTransformer().to(device)
    population_data = [random_program(rng) for _ in range(int(population))]
    history = []

    for epoch in range(int(epochs)):
        scored = [(evaluate_rule_program(p, config)["fitness"], p) for p in population_data]
        scored.sort(key=lambda x: x[0], reverse=True)
        elite_n = max(8, int(population * elite_fraction))
        elites = [p.copy() for _, p in scored[:elite_n]]

        train_model(
            model,
            elites,
            steps=train_steps,
            batch_size=min(32, elite_n),
            device=device,
            seed=seed + epoch,
        )

        sampled = sample_programs(
            model,
            samples_per_epoch,
            temperature=temperature,
            device=device,
            seed=seed + 10000 + epoch,
        )

        improved = []
        for i, p in enumerate(sampled):
            ip, _ = hill_climb_rule_program(
                p,
                config,
                trials=local_search_trials,
                seed=seed + epoch * 100000 + i,
            )
            improved.append(ip)

        candidates = unique_programs(elites + sampled + improved)
        rescored = [(evaluate_rule_program(p, config)["fitness"], p) for p in candidates]
        rescored.sort(key=lambda x: x[0], reverse=True)
        population_data = [p.copy() for _, p in rescored[:population]]
        while len(population_data) < population:
            population_data.append(random_program(rng))

        best_fitness, best_program = rescored[0]
        best_metrics = evaluate_rule_program(best_program, config)
        history.append({
            "epoch": int(epoch),
            "device": device,
            "best_program": [int(x) for x in best_program],
            **{k: float(v) for k, v in best_metrics.items()},
        })

    best = max(history, key=lambda x: x["fitness"])
    return best, history, model


def save_rule_axplorer_result(best, history, path, model=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"best": best, "history": history}, indent=2))
    if model is not None:
        torch.save(model.state_dict(), path.with_suffix(".pt"))


def load_best_program(path):
    data = json.loads(Path(path).read_text())
    return np.asarray(data["best"]["best_program"], dtype=np.int16)
