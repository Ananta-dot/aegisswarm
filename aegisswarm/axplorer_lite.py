from __future__ import annotations

import json
from pathlib import Path
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .strategy import GENE_LEVELS, GENOME_LENGTH, random_genome
from .scoring import EvalConfig, evaluate_genome
from .local_search import hill_climb


BOS = GENE_LEVELS
EOS = GENE_LEVELS + 1
PAD = GENE_LEVELS + 2
VOCAB_SIZE = GENE_LEVELS + 3
SEQ_LEN = GENOME_LENGTH + 2


class GenomeTransformer(nn.Module):
    def __init__(self, d_model=96, nhead=4, layers=3):
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
        b, t = x.shape
        pos = torch.arange(t, device=x.device).unsqueeze(0)
        h = self.tok(x) + self.pos(pos)
        mask = torch.triu(
            torch.ones(t, t, device=x.device, dtype=torch.bool),
            diagonal=1,
        )
        h = self.encoder(h, mask=mask)
        return self.head(h)


def device_auto():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def encode_genome(g):
    return np.asarray([BOS] + [int(x) for x in g] + [EOS], dtype=np.int64)


def train_model(model, genomes, steps=300, batch_size=32, lr=3e-4, device="cpu", seed=0):
    rng = np.random.default_rng(seed)
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    seqs = np.stack([encode_genome(g) for g in genomes])

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
def sample_genomes(model, n, temperature=0.8, device="cpu", seed=0):
    torch.manual_seed(seed)
    model.eval()
    out = []

    for _ in range(int(n)):
        seq = torch.tensor([[BOS]], dtype=torch.long, device=device)
        genes = []

        for _step in range(GENOME_LENGTH):
            logits = model(seq)[:, -1, :GENE_LEVELS] / max(temperature, 1e-4)
            probs = torch.softmax(logits, dim=-1)
            token = int(torch.multinomial(probs, 1).item())
            genes.append(token)
            seq = torch.cat(
                [seq, torch.tensor([[token]], dtype=torch.long, device=device)],
                dim=1,
            )

        out.append(np.asarray(genes, dtype=np.int16))

    return out


def unique_genomes(genomes):
    seen = set()
    out = []
    for g in genomes:
        key = tuple(int(x) for x in g)
        if key not in seen:
            seen.add(key)
            out.append(np.asarray(g, dtype=np.int16))
    return out


def train_axplorer_style(
    config: EvalConfig,
    seed: int = 0,
    epochs: int = 10,
    population: int = 128,
    samples_per_epoch: int = 128,
    train_steps: int = 300,
    elite_fraction: float = 0.25,
    local_search_trials: int = 4,
    temperature: float = 0.8,
    device: str | None = None,
):
    rng = np.random.default_rng(seed)
    device = device or device_auto()
    model = GenomeTransformer().to(device)

    population_data = [random_genome(rng) for _ in range(population)]
    history = []

    for epoch in range(int(epochs)):
        scored = [(evaluate_genome(g, config)["fitness"], g) for g in population_data]
        scored.sort(key=lambda x: x[0], reverse=True)
        elite_n = max(8, int(population * elite_fraction))
        elites = [g.copy() for _, g in scored[:elite_n]]

        train_model(
            model,
            elites,
            steps=train_steps,
            batch_size=min(32, elite_n),
            device=device,
            seed=seed + epoch,
        )

        sampled = sample_genomes(
            model,
            samples_per_epoch,
            temperature=temperature,
            device=device,
            seed=seed + 10_000 + epoch,
        )

        improved = []
        for i, g in enumerate(sampled):
            ig, _ = hill_climb(
                g,
                config,
                trials=local_search_trials,
                seed=seed + epoch * 100_000 + i,
            )
            improved.append(ig)

        candidates = unique_genomes(elites + sampled + improved)
        rescored = [(evaluate_genome(g, config)["fitness"], g) for g in candidates]
        rescored.sort(key=lambda x: x[0], reverse=True)

        population_data = [g.copy() for _, g in rescored[:population]]
        while len(population_data) < population:
            population_data.append(random_genome(rng))

        best_fitness, best_genome = rescored[0]
        best_metrics = evaluate_genome(best_genome, config)
        history.append({
            "epoch": int(epoch),
            "device": device,
            "best_genome": [int(x) for x in best_genome],
            **{k: float(v) for k, v in best_metrics.items()},
        })

    best = max(history, key=lambda x: x["fitness"])
    return best, history, model


def save_axplorer_result(best, history, path, model=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"best": best, "history": history}, indent=2))
    if model is not None:
        torch.save(model.state_dict(), path.with_suffix(".pt"))


def load_best_genome(path):
    data = json.loads(Path(path).read_text())
    return np.asarray(data["best"]["best_genome"], dtype=np.int16)
