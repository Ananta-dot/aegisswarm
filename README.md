# AegisSwarm — Adaptive Coordination Policy Search

AegisSwarm is a **simulation-first research platform for discovering strong coordination policies** against heterogeneous synthetic swarms. The simulator uses normalized, dimensionless parameters and abstract defensive effects; it is intended for algorithmic benchmarking and policy-search research rather than real-world targeting or platform-specific modeling.

The repository now contains two search paths:

- **v1 (legacy/reproducibility):** 8-gene fixed coordination policy, tabular Q-learning, local search, and Axplorer-style transformer search.
- **v2 (recommended):** 20-gene adaptive coordination policy, hierarchical evaluation, transformer proposals, local refinement, train/validation separation, and a persistent validation-ranked hall of fame.

The project objective is to **discover the strongest policy**, not to compare baselines for their own sake. Baselines remain useful only as reference evidence after a strong policy has been found.

---

## 1. Setup

```bash
git pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,serve]"
pytest -q
python -m aegisswarm.cli smoke
```

PyTorch automatically uses MPS on supported Apple Silicon, CUDA when available, otherwise CPU.

---

## 2. Recommended v2 workflow

### Quick sanity run

```bash
bash scripts/run_v2_quick.sh
```

Equivalent commands:

```bash
python -m aegisswarm.cli search-v2 \
  --quick \
  --out artifacts/policy_v2_quick.json

python -m aegisswarm.cli decode-v2 \
  --genome artifacts/policy_v2_quick.json

python -m aegisswarm.cli prove-v2 \
  --genome artifacts/policy_v2_quick.json \
  --episodes 20 \
  --out artifacts/policy_v2_quick_test.json
```

The quick run is only an integration check. Do not treat its score as evidence.

### Full v2 search

```bash
bash scripts/run_v2.sh
```

Equivalent search command:

```bash
python -m aegisswarm.cli search-v2 \
  --epochs 20 \
  --population 256 \
  --samples-per-epoch 256 \
  --train-steps 500 \
  --screen-scenarios 16 \
  --train-scenarios 64 \
  --validation-scenarios 32 \
  --validation-candidates 12 \
  --local-search-trials 4 \
  --archive-size 32 \
  --out artifacts/policy_v2.json
```

Inspect the selected champion:

```bash
python -m aegisswarm.cli decode-v2 \
  --genome artifacts/policy_v2.json
```

Only after search is finished, evaluate the champion on untouched test seeds:

```bash
python -m aegisswarm.cli prove-v2 \
  --genome artifacts/policy_v2.json \
  --episodes 500 \
  --out artifacts/policy_v2_test.json
```

---

## 3. How v2 search works

The v2 optimizer deliberately separates policy discovery from final testing:

```text
random + archived policies
        ↓
small training-seed screen
        ↓
promising candidates
        ↓
larger training-seed evaluation
        ↓
elite genomes
        ↓
train causal transformer
        ↓
sample new 20-token policies
        ↓
local hill-climb refinement
        ↓
train re-ranking
        ↓
validation evaluation of top candidates
        ↓
validation-ranked hall of fame
        ↓
repeat
```

**Test seeds are never used inside `search-v2`.** The selected champion is the policy with the strongest validation fitness in the persistent archive.

### Hierarchical evaluation

The default serious run uses:

- 16 training seeds for cheap screening
- 64 training seeds for stronger ranking
- 32 validation seeds for champion selection
- 500 held-out test seeds only after search ends

This makes it possible to explore many candidates without paying the full simulation cost for every proposal.

---

## 4. Adaptive 20-gene policy

The first eight genes preserve the v1 policy controls:

1. urgency weight
2. defender-distance weight
3. threat-type weight
4. speed weight
5. assignment stickiness
6. resource-preservation weight
7. decoy penalty
8. reserve threshold

The next twelve genes make the policy state-dependent:

9. high-threat-density threshold
10. high-density urgency boost
11. high-density speed boost
12. low-resource threshold
13. low-resource conservation boost
14. low-resource reserve boost
15. imminent-threat distance threshold
16. imminent-threat urgency boost
17. asset-damage threshold
18. damaged-asset urgency boost
19. damaged-asset stickiness boost
20. overall assignment aggressiveness/bias

The policy therefore changes its coordination behavior as observable scenario conditions change rather than using the same eight weights for the entire episode.

---

## 5. Hall of fame

`artifacts/policy_v2.json` contains:

- the validation-selected champion
- decoded adaptive policy parameters
- epoch history
- the persistent hall-of-fame archive
- training and validation metrics for archived policies
- exact screen/train/validation seed lists
- confirmation that no test seeds were used during search

The transformer state is saved beside it as `artifacts/policy_v2.pt`.

---

## 6. Experiment splits

The code defines these non-overlapping seed pools:

| Split | Seed pool | Purpose |
|---|---:|---|
| train | 0–255 | candidate search and training |
| validation | 1000–1099 | policy/champion selection |
| test | 2000–2499 | final held-out evaluation |
| stress | separate families/seeds | later robustness analysis |

Search commands may use subsets of these pools, but the roles must not be mixed. In particular, do not use test seeds to tune the policy.

---

## 7. Core simulator metrics

Primary KPI:

- `asset_survival_rate`

Secondary metrics:

- containment rate
- penetrations
- cumulative abstract damage
- defensive resource use
- mean response delay

The current fitness function is dominated by asset survival, followed by containment, with smaller penalties for damage, resource use, and response delay.

---

## 8. Legacy v1 workflow

The previous commands remain available for reproducibility:

```bash
python -m aegisswarm.cli all --quick
bash scripts/run_full.sh
```

Individual v1 commands remain:

```bash
python -m aegisswarm.cli benchmark
python -m aegisswarm.cli train-rl
python -m aegisswarm.cli train-local
python -m aegisswarm.cli train-axplorer
python -m aegisswarm.cli prove
python -m aegisswarm.cli stress
```

The v1 Axplorer implementation still uses an 8-token genome. `axplorer_lite.py` has been generalized so the same transformer machinery can also generate the 20-token v2 genome without breaking the legacy path.

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
│   ├── strategy.py          # v1 fixed 8-gene policy
│   ├── strategy_v2.py       # adaptive 20-gene policy
│   ├── scoring.py           # v1 scoring
│   ├── scoring_v2.py        # v2 scoring
│   ├── archive.py           # persistent validation-ranked hall of fame
│   ├── search_v2.py         # hierarchical v2 optimizer
│   ├── rl.py
│   ├── axplorer_lite.py     # shared causal transformer machinery
│   ├── benchmark.py
│   ├── stress.py
│   ├── service.py
│   └── cli.py
├── configs/default.json
├── scripts/run_v2_quick.sh
├── scripts/run_v2.sh
├── scripts/run_quick.sh
├── scripts/run_full.sh
├── tests/
├── Dockerfile
└── pyproject.toml
```

---

## 10. What remains after v2

The next major modeling improvements are separate from this policy-search upgrade:

1. replace ground-truth detected-threat state with a proper noisy observation/track model
2. add uncertainty/confidence features that the adaptive policy can legitimately observe
3. broaden the policy language beyond weighted assignment rules if v2 saturates
4. add curriculum/domain-randomized scenario search
5. run large repeated search campaigns with different optimizer seeds
6. perform final stress testing and baseline comparisons only after strong champions are found

The immediate workflow is therefore: **run v2 search, inspect the archive/champion, evaluate the champion on held-out test scenarios, then decide whether the policy language needs another expansion.**
