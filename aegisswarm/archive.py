from __future__ import annotations

import json
from pathlib import Path


class PolicyArchive:
    """Keep the best unique policies ranked by validation fitness."""

    def __init__(self, max_size: int = 32):
        self.max_size = int(max_size)
        self.entries: dict[tuple[int, ...], dict] = {}

    def add(self, genes, train_metrics: dict, validation_metrics: dict, source: str, epoch: int):
        key = tuple(int(x) for x in genes)
        entry = {
            "genes": list(key),
            "source": str(source),
            "epoch": int(epoch),
            "train": {k: float(v) if isinstance(v, (int, float)) else v for k, v in train_metrics.items()},
            "validation": {k: float(v) if isinstance(v, (int, float)) else v for k, v in validation_metrics.items()},
        }
        old = self.entries.get(key)
        if old is None or entry["validation"]["fitness"] > old["validation"]["fitness"]:
            self.entries[key] = entry
        self._trim()

    def _trim(self):
        ranked = sorted(
            self.entries.items(),
            key=lambda kv: (
                kv[1]["validation"]["fitness"],
                kv[1]["train"]["fitness"],
            ),
            reverse=True,
        )
        self.entries = dict(ranked[: self.max_size])

    def ranked(self):
        return sorted(
            self.entries.values(),
            key=lambda e: (
                e["validation"]["fitness"],
                e["train"]["fitness"],
            ),
            reverse=True,
        )

    @property
    def best(self):
        ranked = self.ranked()
        return ranked[0] if ranked else None

    def as_dict(self):
        return {
            "ranking_metric": "validation.fitness",
            "max_size": self.max_size,
            "best": self.best,
            "entries": self.ranked(),
        }

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=2))

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text())
        archive = cls(max_size=int(data.get("max_size", 32)))
        for entry in data.get("entries", []):
            archive.add(
                entry["genes"],
                entry["train"],
                entry["validation"],
                entry.get("source", "loaded"),
                int(entry.get("epoch", -1)),
            )
        return archive
