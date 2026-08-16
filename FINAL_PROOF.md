# AegisSwarm frozen final-proof protocol

This protocol exists because seeds `2000–2099` were already inspected during architecture development. They are now development-test seeds only.

The formal final holdout is frozen at **seeds `2100–2499` (400 scenarios)**.

Do not use those 400 seeds to tune the algorithm before the formal run.

## What the final runner does

For each of five matched search seeds, it independently trains:

- structured evolutionary/local search
- structured Axplorer transformer + local refinement

Both methods receive the same search-oracle budget:

- 16 fixed training scenarios per candidate
- 1,800 unique candidate-program evaluations per training run
- population 64
- five independent search seeds

This makes the main ablation budget-matched on the expensive simulator-scoring operation.

The runner also:

- trains a fresh 1,500-episode Q-learning baseline instead of reusing the smoke-test table
- evaluates heuristic, Hungarian, RL, and available legacy baselines
- evaluates all five structured-local and all five structured-Axplorer policies on the same 400 untouched holdout scenarios
- computes hierarchical bootstrap confidence intervals
- computes paired Axplorer-minus-local confidence intervals
- computes a paired scenario-level sign-flip p-value
- runs all five stress families on separate seed blocks
- records policy runtime and training-run variability

## 1. Update the branch

```bash
git checkout agent/structured-rule-program
git pull
pip install -e ".[dev,serve]"
pytest -q
```

## 2. Validate the machinery without touching the final holdout

```bash
python -m aegisswarm.final_cli --quick --workers 4
```

Quick mode uses validation seeds, a tiny search budget, and different stress seeds. It is only an integration check.

Expected output directory:

```text
artifacts/final_proof_quick/
```

Do not interpret quick-mode performance as evidence.

## 3. Formal final run

On the Mac Studio, use:

```bash
python -m aegisswarm.final_cli --workers 6
```

MPS is auto-detected for transformer training. You can make it explicit with:

```bash
python -m aegisswarm.final_cli --workers 6 --device mps
```

The command prints progress after every search round; it is not intentionally silent.

### Resume behavior

Each completed training seed is saved immediately. If the command is interrupted, rerun the same command:

```bash
python -m aegisswarm.final_cli --workers 6
```

Completed runs are loaded from disk and skipped. Do **not** add `--force-train` unless you intentionally want to discard and retrain all completed search runs.

## Outputs

The formal run writes:

```text
artifacts/final_proof/
├── protocol.json
├── final_qtable.json
├── results.json
├── final_summary.csv
├── final_raw_baselines.json
├── final_raw_structured.json
├── stress_raw_structured.json
├── REPORT.md
└── runs/
    ├── rule_local_seed_41001.json
    ├── rule_axplorer_seed_41001.json
    └── ... five paired seeds total
```

`REPORT.md` is the first file to read after completion.

## Primary statistical comparison

The formal primary endpoint is protected-asset survival.

The key result is reported as:

```text
mean(rule_axplorer - rule_local)
95% paired hierarchical bootstrap CI
paired sign-flip p-value
```

The hierarchical bootstrap resamples both training runs and final scenarios, so the confidence interval reflects both policy-search variability and scenario variability.

## Methodological freeze

Once the formal `2100–2499` results have been viewed, those seeds are no longer untouched.

If we change the algorithm because of anything observed on the final holdout, the modified algorithm must be confirmed on a new reserved seed block rather than repeatedly reusing `2100–2499` as a fresh test set.
