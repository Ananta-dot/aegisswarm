# AegisSwarm Hybrid Objective Learning

This experiment changes the training loop, not merely the executor used at evaluation time.

Every candidate rule program is evaluated through `RuleGuidedHungarianPolicy`, so search learns strategic utilities and reserve behavior specifically for optimized assignment.

## Hypotheses

1. A searched strategic objective should materially outperform the current fixed hand-written Hungarian objective.
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

- Development: seeds `5000-5399` — **consumed**.
- Reserved confirmation: seeds `8000-8399` — **untouched; do not run**.

## Full development result

```text
fixed_optimizer survival: 0.320
hybrid_local survival:    0.805 CI=[0.77624375, 0.83100625]
hybrid_axplorer survival: 0.810 CI=[0.77775, 0.841]
difference (A-L):         +0.0055 CI=[-0.0235, 0.0320]
paired p-value:           0.507075
```

## Decision

**NO FREEZE. NO CONFIRMATION.**

Interpretation:

- optimizer-aware strategic search is materially stronger than the current fixed hand-written objective in this synthetic simulator;
- Axplorer does not show a meaningful advantage over optimizer-aware local/evolutionary search under this protocol;
- the repeated ~80–81% performance region across several architectures suggests a strategic-representation and/or myopic-planning bottleneck rather than a proposer bottleneck;
- do not spend `8000–8399` on confirmation of this architecture.

For current direction, read `docs/AEGISSWARM_STATUS.md` after the full project skill.

## Historical commands

Integration check:

```bash
pytest -q
python -m aegisswarm.hybrid_objective_cli --quick --workers 4 --device mps
```

Full development:

```bash
python -m aegisswarm.hybrid_objective_cli --workers 6 --device mps
```

The confirmation command exists but must remain blocked/unrun until a future explicit freeze decision:

```bash
python -m aegisswarm.hybrid_objective_cli --confirm --workers 6
```
