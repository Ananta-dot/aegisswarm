# AegisSwarm Hybrid Architecture

## Objective

AegisSwarm should combine complementary methods rather than force one method to
replace all others. Learned search is used for strategic structure discovery;
optimization is used for exact constrained assignment; local search is used for
offline improvement; explicit rules preserve interpretable state-reactive
behavior.

## Current hybrid boundary

```text
scenario state
    |
    v
strategic rule program
    |  pair utility + reserve intent
    v
Hungarian assignment optimizer
    |  globally consistent one-to-one assignment
    v
simulator action
```

The first hybrid implementation intentionally changes only the execution layer.
The same discovered programs are evaluated under:

1. greedy rule execution;
2. rule-guided Hungarian execution.

This isolates the optimizer contribution before any hybrid-specific retraining.

## First ablation

Using paired local-search and Axplorer V2 programs:

- optimizer_only
- local_greedy
- local_hybrid
- v2_greedy
- v2_hybrid

Primary questions:

1. `local_hybrid - local_greedy`: does optimization improve a conventional-search strategy?
2. `v2_hybrid - v2_greedy`: does optimization improve a learned-search strategy?
3. `v2_greedy - local_greedy`: what does V2 strategy discovery add without optimization?
4. `v2_hybrid - local_hybrid`: what does V2 strategy discovery add once optimization is present?

## Data discipline

- V1 final holdout `2100-2499`: consumed; never reuse as unseen evidence.
- V2 development `3000-3399`: V2 architecture development.
- Hybrid development `4000-4399`: hybrid architecture development.
- V2 confirmation `6000-6399`: reserved.
- Hybrid confirmation `7000-7399`: reserved.

## Next stage after the execution ablation

If rule-guided optimization is beneficial, train strategic programs directly
against the hybrid executor, still under matched simulator-evaluation budgets.
Then compare:

- optimizer only;
- hybrid + local strategy search;
- hybrid + Axplorer V2 strategy search.

Only after that architecture is frozen should the hybrid confirmation block be
used.
