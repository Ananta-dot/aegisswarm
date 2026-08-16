# Structured Rule-Program Experiment

This branch adds a larger structured strategy space specifically to test whether the Axplorer-style transformer contributes beyond local/evolutionary search.

The original 8-gene strategy remains unchanged as a legacy baseline.

## 1. Pull the branch

```bash
git fetch origin
git checkout agent/structured-rule-program
pip install -e ".[dev,serve]"
pytest -q
```

## 2. Train structured local search

```bash
python -m aegisswarm.rule_cli train-local \
  --generations 10 \
  --population 64 \
  --train-scenarios 16 \
  --out artifacts/rule_local.json
```

## 3. Train structured Axplorer

```bash
python -m aegisswarm.rule_cli train-axplorer \
  --epochs 10 \
  --population 64 \
  --samples-per-epoch 64 \
  --train-steps 200 \
  --train-scenarios 16 \
  --out artifacts/rule_axplorer.json
```

## 4. Compare everything on the exact same 100 held-out scenarios

```bash
python -m aegisswarm.rule_cli prove \
  --episodes 100 \
  --rl-table artifacts/qtable.json \
  --legacy-local artifacts/local_search.json \
  --legacy-axplorer artifacts/axplorer_best.json \
  --rule-local artifacts/rule_local.json \
  --rule-axplorer artifacts/rule_axplorer.json \
  --out artifacts/rule_ablation.json
```

The output labels are explicit:

- `legacy_local`: prior 8-gene evolutionary/local-search policy
- `legacy_axplorer`: prior 8-gene transformer + local-search policy
- `rule_local`: structured 12-rule evolutionary/local-search policy
- `rule_axplorer`: structured 12-rule transformer + local-search policy

## Validation target

The current legacy local-search benchmark is approximately 74.5% held-out asset survival on the previously used 100 test scenarios. The structured experiment should be judged against that fixed reference, not against training scores.

Do not change simulator dynamics, scoring weights, or test seeds during this comparison.
