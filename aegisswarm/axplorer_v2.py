from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .rule_program import (
    Action,
    Condition,
    MAX_RULES,
    PROGRAM_LENGTH,
    RULE_WIDTH,
    TOKEN_LEVELS,
)


QUALITY_LEVELS = 4
BOS = TOKEN_LEVELS
TOKEN_VOCAB = TOKEN_LEVELS + 1

# Canonical category counts for each rule field:
# enabled | condition | threshold | action | magnitude
FIELD_CARDINALITIES = (
    2,
    len(Condition),
    TOKEN_LEVELS,
    len(Action),
    TOKEN_LEVELS,
)


@dataclass(frozen=True)
class ArchiveEntry:
    program: np.ndarray
    fitness: float
    metrics: dict


def canonicalize_program(program) -> np.ndarray:
    """Map semantically equivalent rule encodings to one grammar-valid form.

    The original rule decoder intentionally accepted any 0..15 token and used
    threshold/modulo logic for categorical fields. V2 removes those aliases so
    the model learns one representation per rule semantics.
    """
    arr = np.asarray(program, dtype=np.int16).copy()
    if arr.shape != (PROGRAM_LENGTH,):
        raise ValueError(f"Expected program shape {(PROGRAM_LENGTH,)}, got {arr.shape}")

    rows = arr.reshape(MAX_RULES, RULE_WIDTH)
    rows[:, 0] = np.where(rows[:, 0] >= TOKEN_LEVELS // 2, TOKEN_LEVELS - 1, 0)
    rows[:, 1] = rows[:, 1] % len(Condition)
    rows[:, 2] = np.clip(rows[:, 2], 0, TOKEN_LEVELS - 1)
    rows[:, 3] = rows[:, 3] % len(Action)
    rows[:, 4] = np.clip(rows[:, 4], 0, TOKEN_LEVELS - 1)
    return rows.reshape(-1).astype(np.int16)


def _target_categories(programs: np.ndarray, field: int) -> np.ndarray:
    vals = programs[:, field::RULE_WIDTH].astype(np.int64)
    if field == 0:
        return (vals >= TOKEN_LEVELS // 2).astype(np.int64)
    return vals


def _categories_to_tokens(categories: torch.Tensor, field: int) -> torch.Tensor:
    if field == 0:
        return torch.where(
            categories > 0,
            torch.full_like(categories, TOKEN_LEVELS - 1),
            torch.zeros_like(categories),
        )
    return categories


def quality_buckets(fitnesses) -> np.ndarray:
    """Rank-conditioned quality labels: bottom/mid/high/top."""
    f = np.asarray(fitnesses, dtype=float)
    if f.ndim != 1 or len(f) == 0:
        raise ValueError("fitnesses must be a non-empty vector")

    order = np.argsort(-f)
    buckets = np.zeros(len(f), dtype=np.int64)
    n = len(f)
    top = max(1, int(np.ceil(0.10 * n)))
    high = max(top + 1, int(np.ceil(0.30 * n)))
    mid = max(high + 1, int(np.ceil(0.60 * n)))
    buckets[order[:top]] = 3
    buckets[order[top:high]] = 2
    buckets[order[high:mid]] = 1
    return buckets


def score_weights(fitnesses, temperature: float = 4.0) -> np.ndarray:
    """Exponentially emphasize strong programs without discarding diversity."""
    f = np.asarray(fitnesses, dtype=float)
    tau = max(float(temperature), 1e-6)
    shifted = np.clip((f - np.max(f)) / tau, -12.0, 0.0)
    weights = np.exp(shifted)
    weights = np.maximum(weights, 1e-4)
    return weights / max(float(np.mean(weights)), 1e-12)


class FitnessConditionedRuleTransformer(nn.Module):
    """Causal transformer with explicit rule-field grammar and quality conditioning."""

    def __init__(self, d_model=128, nhead=4, layers=4):
        super().__init__()
        self.token = nn.Embedding(TOKEN_VOCAB, d_model)
        self.position = nn.Embedding(PROGRAM_LENGTH, d_model)
        self.field = nn.Embedding(RULE_WIDTH, d_model)
        self.quality = nn.Embedding(QUALITY_LEVELS, d_model)

        block = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=4 * d_model,
            dropout=0.0,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(block, num_layers=layers)
        self.heads = nn.ModuleList(
            nn.Linear(d_model, cardinality)
            for cardinality in FIELD_CARDINALITIES
        )

    def hidden(self, x: torch.Tensor, quality: torch.Tensor) -> torch.Tensor:
        _, t = x.shape
        positions = torch.arange(t, device=x.device)
        fields = positions % RULE_WIDTH
        h = (
            self.token(x)
            + self.position(positions).unsqueeze(0)
            + self.field(fields).unsqueeze(0)
            + self.quality(quality).unsqueeze(1)
        )
        mask = torch.triu(
            torch.ones(t, t, device=x.device, dtype=torch.bool),
            diagonal=1,
        )
        return self.encoder(h, mask=mask)

    def next_logits(self, x: torch.Tensor, quality: torch.Tensor, field: int) -> torch.Tensor:
        h = self.hidden(x, quality)
        return self.heads[int(field)](h[:, -1, :])


def device_auto():
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _input_sequences(programs: np.ndarray) -> np.ndarray:
    canonical = np.stack([canonicalize_program(p) for p in programs])
    x = np.empty_like(canonical, dtype=np.int64)
    x[:, 0] = BOS
    x[:, 1:] = canonical[:, :-1]
    return x


def train_v2_model(
    model: FitnessConditionedRuleTransformer,
    programs,
    fitnesses,
    steps=200,
    batch_size=32,
    lr=3e-4,
    weight_temperature=4.0,
    device="cpu",
    seed=0,
):
    programs = np.stack([canonicalize_program(p) for p in programs])
    fitnesses = np.asarray(fitnesses, dtype=float)
    if len(programs) != len(fitnesses):
        raise ValueError("program and fitness counts must match")

    qualities = quality_buckets(fitnesses)
    weights = score_weights(fitnesses, temperature=weight_temperature)
    inputs = _input_sequences(programs)

    rng = np.random.default_rng(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    model.train()

    for _ in range(int(steps)):
        size = min(int(batch_size), len(programs))
        idx = rng.integers(0, len(programs), size=size)

        x = torch.tensor(inputs[idx], dtype=torch.long, device=device)
        q = torch.tensor(qualities[idx], dtype=torch.long, device=device)
        w = torch.tensor(weights[idx], dtype=torch.float32, device=device)
        h = model.hidden(x, q)

        per_example = torch.zeros(size, dtype=torch.float32, device=device)
        for field in range(RULE_WIDTH):
            positions = torch.arange(field, PROGRAM_LENGTH, RULE_WIDTH, device=device)
            logits = model.heads[field](h[:, positions, :])
            targets_np = _target_categories(programs[idx], field)
            targets = torch.tensor(targets_np, dtype=torch.long, device=device)
            losses = F.cross_entropy(
                logits.reshape(-1, FIELD_CARDINALITIES[field]),
                targets.reshape(-1),
                reduction="none",
            ).reshape(size, -1).mean(dim=1)
            per_example += losses

        per_example /= RULE_WIDTH
        loss = (per_example * w).sum() / w.sum().clamp_min(1e-8)

        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

    return model


@torch.no_grad()
def sample_v2_programs(
    model: FitnessConditionedRuleTransformer,
    n: int,
    temperature: float = 0.85,
    quality_level: int = 3,
    device="cpu",
    seed=0,
):
    """Generate canonical programs while conditioning explicitly on top quality."""
    torch.manual_seed(int(seed))
    model.eval()

    n = int(n)
    q = torch.full((n,), int(quality_level), dtype=torch.long, device=device)
    seq = torch.full((n, 1), BOS, dtype=torch.long, device=device)
    generated = []

    for position in range(PROGRAM_LENGTH):
        field = position % RULE_WIDTH
        logits = model.next_logits(seq, q, field)
        logits = logits / max(float(temperature), 1e-4)
        probs = torch.softmax(logits, dim=-1)
        categories = torch.multinomial(probs, num_samples=1).squeeze(1)
        tokens = _categories_to_tokens(categories, field)
        generated.append(tokens)
        seq = torch.cat([seq, tokens.unsqueeze(1)], dim=1)

    matrix = torch.stack(generated, dim=1).cpu().numpy().astype(np.int16)
    return [canonicalize_program(row) for row in matrix]


def _entry_sort(entries, metric: str, reverse: bool):
    return sorted(entries, key=lambda e: float(e.metrics[metric]), reverse=reverse)


def select_diverse_archive(cache, max_size: int = 256) -> list[ArchiveEntry]:
    """Keep high-fitness programs plus specialists from several objective niches."""
    entries = [
        ArchiveEntry(
            program=canonicalize_program(np.asarray(key, dtype=np.int16)),
            fitness=float(metrics["fitness"]),
            metrics=dict(metrics),
        )
        for key, metrics in cache.items()
    ]
    if not entries:
        return []

    max_size = max(8, int(max_size))
    chosen: dict[tuple[int, ...], ArchiveEntry] = {}

    def add(items, limit):
        for entry in items[:limit]:
            key = tuple(int(x) for x in entry.program)
            chosen.setdefault(key, entry)
            if len(chosen) >= max_size:
                break

    # Main exploitation archive.
    add(sorted(entries, key=lambda e: e.fitness, reverse=True), max_size // 2)

    # Objective specialists prevent the model from collapsing onto one rule family.
    niche_limit = max(4, max_size // 12)
    add(_entry_sort(entries, "asset_survival_rate", True), niche_limit)
    add(_entry_sort(entries, "containment_rate", True), niche_limit)
    add(_entry_sort(entries, "penetrations", False), niche_limit)
    add(_entry_sort(entries, "cumulative_damage", False), niche_limit)
    add(_entry_sort(entries, "defenders_consumed", False), niche_limit)
    add(_entry_sort(entries, "mean_response_delay", False), niche_limit)

    # Fill remaining capacity by fitness.
    add(sorted(entries, key=lambda e: e.fitness, reverse=True), max_size)
    return list(chosen.values())[:max_size]


def archive_training_arrays(entries: list[ArchiveEntry]):
    if not entries:
        raise ValueError("archive is empty")
    programs = [entry.program for entry in entries]
    fitnesses = np.asarray([entry.fitness for entry in entries], dtype=float)
    return programs, fitnesses
