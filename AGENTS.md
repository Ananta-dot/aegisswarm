# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form history/methodology.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay; treat this as newer when current-status wording differs.
3. [`OPTIMIZER_NATIVE_OBJECTIVE.md`](OPTIMIZER_NATIVE_OBJECTIVE.md) — active representation-ablation protocol.

## Non-negotiable rules

1. Architecture is not final.
2. Never consume reserved confirmation seeds for development.
3. Once inspected, a block is never untouched again.
4. Do not silently change simulator/scoring/budgets inside a formal protocol.
5. Compare components by ablation, not ideology.
6. Use equal simulator-evaluation budgets for search/representation comparisons unless compute scaling is the experiment.
7. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
8. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
9. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
10. Keep the handoff/status docs current after major experiments.

## Completed hybrid-objective conclusion

```text
fixed_optimizer: 0.320
hybrid_local:     0.805
hybrid_axplorer:  0.810
Axplorer-local:  +0.0055, CI [-0.0235, +0.0320], p=0.507075
```

Optimizer-aware objective search is useful; Axplorer is statistically tied with local/evolutionary search. Proposer tuning is deprioritized.

## Optimizer-native V1 — rejected

The old V1 native representation completed the `9000–9399` development campaign before the V2 patch was pulled locally:

```text
fixed_optimizer: 0.310
rule_objective:  0.787
native_v1:       0.359
native-rule:    -0.4280, CI [-0.4845, -0.3590], p=0.000050
```

One V1 training run reached ~0.812 survival on its 16 training scenarios while the full development mean was only 0.359. Combined with V1's malformed zero-centred utility/no-op behavior and omitted state signals, this architecture is rejected. Do not rerun or tune it. `9000–9399` is fully consumed.

## Active experiment — optimizer-native V2

Branch: `agent/optimizer-native-objective`  
Protocol: `aegisswarm-optimizer-native-objective-v2`

V2 shares the rule-guided positive structural base utility and learns 14 smooth state-reactive strategic modifiers. Both V2 and the 60-token rule comparator use the same local/evolutionary search family, matched seeds, budget, simulator, fitness, and Hungarian executor.

Fresh V2 data:

- development: `11000–11399`
- reserved confirmation: `12000–12399`

The old `10000–10399` block remains untouched but belongs to the abandoned V1 evidence plan; do not silently repurpose it.

Expected V2 logs/artifacts contain `optimizer-native-v2`, `native-v2-local`, and `optimizer_native_v2_*`. If logs say `native-local` or save to `optimizer_native_dev`, the local checkout is stale.

Do not run confirmation automatically after development.
