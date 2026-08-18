#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts

python -m aegisswarm.cli search-v2 \
  --quick \
  --out artifacts/policy_v2_quick.json

python -m aegisswarm.cli decode-v2 \
  --genome artifacts/policy_v2_quick.json

python -m aegisswarm.cli prove-v2 \
  --genome artifacts/policy_v2_quick.json \
  --episodes 20 \
  --out artifacts/policy_v2_quick_test.json
