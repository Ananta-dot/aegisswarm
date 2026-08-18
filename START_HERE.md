# START HERE

This repository is the single source of truth. Ignore the earlier M1–M5 ZIPs.

## Update and setup

```bash
git pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev,serve]"
```

## Verify

```bash
pytest -q
python -m aegisswarm.cli smoke
```

## Recommended: test the new adaptive search quickly

```bash
bash scripts/run_v2_quick.sh
```

This exercises the adaptive 20-gene policy, staged training evaluation, transformer proposals, local refinement, validation-ranked hall of fame, champion decoding, and a small held-out test evaluation.

## Then run the serious policy search

```bash
bash scripts/run_v2.sh
```

Main outputs:

```text
artifacts/policy_v2.json       # champion + archive + search history
artifacts/policy_v2.pt         # transformer state
artifacts/policy_v2_test.json  # final held-out champion result
```

## Useful individual commands

```bash
python -m aegisswarm.cli search-v2 --quick
python -m aegisswarm.cli decode-v2 --genome artifacts/policy_v2.json
python -m aegisswarm.cli prove-v2 --genome artifacts/policy_v2.json --episodes 500
```

The old v1 pipeline remains available with:

```bash
python -m aegisswarm.cli all --quick
bash scripts/run_full.sh
```

## Important workflow

1. keep this repository as the single source of truth;
2. modify it in place and use Git for checkpoints;
3. run `pytest -q` after changes;
4. use `scripts/run_v2_quick.sh` for integration checks;
5. use `scripts/run_v2.sh` for serious policy-discovery runs;
6. do not use held-out test scores to tune the policy.
