# AegisSwarm Hybrid Objective Learning

This experiment changes the training loop, not merely the executor used at evaluation time.

Every candidate rule program is evaluated through `RuleGuidedHungarianPolicy`, so search learns strategic utilities and reserve behavior specifically for optimized assignment.

## Hypotheses

1. A learned strategic objective should materially outperform the fixed hand-written Hungarian objective.
2. Local search and Axplorer should be compared under the exact same optimizer-aware candidate-evaluation budget.
3. If Axplorer adds value, its advantage must be measured against optimizer-aware local search, not against a strategy trained for greedy execution.

## Frozen controls

- Same simulator.
- Same rule-program language.
- Same fitness equation.
- Same 16 training scenarios for full development runs.
- Same five matched search seeds.
- Same 1,800 unique candidate evaluations per method/run.
- Same Hungarian execution layer for every searched candidate.

## Data blocks

- Development: seeds `5000-5399`.
- Reserved confirmation: seeds `8000-8399`.

Do not run the confirmation block until development is complete and the architecture/hyperparameters are frozen.

## Commands

Integration check:

```bash
pytest -q
python -m aegisswarm.hybrid_objective_cli --quick --workers 4 --device mps
```

Full development:

```bash
python -m aegisswarm.hybrid_objective_cli --workers 6 --device mps
```

Reserved confirmation, only after an explicit freeze decision:

```bash
python -m aegisswarm.hybrid_objective_cli --confirm --workers 6
```
