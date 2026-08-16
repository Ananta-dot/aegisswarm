#!/usr/bin/env bash
set -euo pipefail

python -m aegisswarm.cli smoke
python -m aegisswarm.cli all --quick
