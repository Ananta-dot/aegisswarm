#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts

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

python -m aegisswarm.cli decode-v2 \
  --genome artifacts/policy_v2.json

python -m aegisswarm.cli prove-v2 \
  --genome artifacts/policy_v2.json \
  --episodes 500 \
  --out artifacts/policy_v2_test.json
