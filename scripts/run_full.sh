#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts

python -m aegisswarm.cli benchmark \
  --episodes 100 \
  --split test \
  --out artifacts/baselines.json

python -m aegisswarm.cli train-local \
  --generations 12 \
  --population 96 \
  --train-scenarios 24 \
  --out artifacts/local_search.json

python -m aegisswarm.cli train-rl \
  --episodes 1500 \
  --out artifacts/qtable.json

python -m aegisswarm.cli train-axplorer \
  --epochs 20 \
  --population 256 \
  --samples-per-epoch 256 \
  --train-steps 500 \
  --train-scenarios 32 \
  --out artifacts/axplorer_best.json

python -m aegisswarm.cli prove \
  --episodes 500 \
  --rl-table artifacts/qtable.json \
  --genome artifacts/axplorer_best.json \
  --out artifacts/proof.json

python -m aegisswarm.cli stress \
  --episodes 200 \
  --rl-table artifacts/qtable.json \
  --genome artifacts/axplorer_best.json \
  --out artifacts/stress.json
