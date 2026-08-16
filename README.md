# AegisSwarm — Counter-Swarm Coordination Research Platform

AegisSwarm is a **simulation-first research platform** for studying defensive coordination
against heterogeneous swarms using abstract, normalized system models.

The repository is intentionally self-contained. It includes the full experimental pipeline:

1. deterministic/seeded simulator
2. scenario generator and fixed train/validation/test/stress splits
3. heuristic baselines
4. per-step optimization baseline
5. sequential Q-learning baseline
6. self-contained Axplorer-style transformer + elite-search loop
7. local-search ablation
8. held-out benchmarking and bootstrap confidence intervals
9. stress-test suite
10. FastAPI demo service
11. Docker deployment
12. optional adapter for upstream `AxiomMath/axplorer`

> **Scope note:** The simulator uses synthetic, dimensionless parameters and abstract
> defensive effects. It is for algorithmic benchmarking and decision-support research,
> not real-world weapon guidance, targeting, or platform-specific modeling.

---

## 1. One-time setup

### macOS / Linux

```bash
cd aegisswarm_full

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev,serve]"
```

PyTorch on Apple Silicon will automatically use MPS when available for the transformer stage.

Check the installation:

```bash
pytest -q
python -m aegisswarm.cli smoke
```

---

## 2. Fastest end-to-end run

This trains small RL and Axplorer-style models and evaluates them on held-out seeds:

```bash
python -m aegisswarm.cli all --quick
```

Outputs are written to:

```text
artifacts/
  qtable.json
  axplorer_best.json
  quick_proof.json
```

This is only a smoke/prototyping run.

---

## 3. Recommended development run

### A. Benchmark non-learning baselines

```bash
python -m aegisswarm.cli benchmark \
  --episodes 200 \
  --split test
```

### B. Train the sequential RL baseline

```bash
python -m aegisswarm.cli train-rl \
  --episodes 1500 \
  --out artifacts/qtable.json
```

### C. Train the Axplorer-style generative search model

```bash
python -m aegisswarm.cli train-axplorer \
  --epochs 20 \
  --population 256 \
  --samples-per-epoch 256 \
  --train-steps 500 \
  --out artifacts/axplorer_best.json
```

### D. Run held-out proof evaluation

```bash
python -m aegisswarm.cli prove \
  --episodes 500 \
  --rl-table artifacts/qtable.json \
  --genome artifacts/axplorer_best.json \
  --out artifacts/proof.json
```

### E. Run stress tests

```bash
python -m aegisswarm.cli stress \
  --episodes 200 \
  --rl-table artifacts/qtable.json \
  --genome artifacts/axplorer_best.json \
  --out artifacts/stress.json
```

---

## 4. One-command full experiment

```bash
bash scripts/run_full.sh
```

For a small sanity run:

```bash
bash scripts/run_quick.sh
```

---

## 5. Demo service

```bash
python -m aegisswarm.cli serve --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

The service exposes:

- `GET /health`
- `GET /`
- `POST /simulate`
- `POST /compare`

---

## 6. Docker

```bash
docker build -t aegisswarm .
docker run --rm -p 8000:8000 aegisswarm
```

Then open `http://localhost:8000`.

---

## 7. Fixed experiment design

### Primary KPI

`asset_survival_rate`

### Secondary metrics

- containment rate
- penetrations
- cumulative abstract damage
- defensive resource use
- mean response delay

### Fixed split policy

| Split | Seeds | Purpose |
|---|---:|---|
| train | 0–63 | learning |
| validation | 1000–1031 | model selection |
| test | 2000–2099 | final held-out comparison |
| stress | separate scenario families | robustness |

Do not train on test/stress seeds.

### Baselines

- random
- closest threat
- highest risk
- greedy risk/cost
- Hungarian per-step optimization
- sequential tabular Q-learning
- local-search-only genome optimization
- Axplorer-style transformer + local search

---

## 8. What the Axplorer-style stage is doing

A candidate strategy is a compact 8-token policy genome.

The genome controls **abstract coordination preferences**, not platform parameters.

Each epoch:

```text
elite genomes
    ↓
train causal transformer
    ↓
sample candidate genomes
    ↓
evaluate across training scenarios
    ↓
local search
    ↓
retain best unique genomes
    ↓
repeat
```

This mirrors Axplorer's core `train → sample → search/score → select best` logic while
remaining fully self-contained.

The optional `axplorer_integration/` directory contains a drop-in adapter for upstream
AxiomMath/axplorer if we later want a direct apples-to-apples implementation.

---

## 9. Project structure

```text
aegisswarm/
├── aegisswarm/
│   ├── models.py
│   ├── scenarios.py
│   ├── simulator.py
│   ├── policies.py
│   ├── optimization.py
│   ├── strategy.py
│   ├── scoring.py
│   ├── rl.py
│   ├── axplorer_lite.py
│   ├── benchmark.py
│   ├── stress.py
│   ├── service.py
│   └── cli.py
├── configs/default.json
├── scripts/run_quick.sh
├── scripts/run_full.sh
├── tests/
├── Dockerfile
└── pyproject.toml
```

---

## 10. What results count as evidence

Do **not** use training-seed results as headline evidence.

The minimum credible evidence package is:

1. 500+ held-out test scenarios
2. confidence intervals over paired seeds
3. stress scenarios with unseen swarm compositions/sizes
4. ablation: local search without transformer
5. comparison with RL and optimization baselines
6. runtime measurements
7. fixed simulator version and fixed metric definition
8. reproducible seeds/config files

Only after this stage should we make performance claims.

---

## 11. Next work after this repository

Once the full pipeline is running reliably:

1. calibrate synthetic distributions against defensible public literature
2. improve partial-observation modeling
3. add stronger multi-agent RL baseline
4. add scenario curriculum
5. add domain randomization
6. run large statistical campaign
7. package results for iDEX technical submission

The core simulator API and metrics should remain frozen while those improvements are added.
