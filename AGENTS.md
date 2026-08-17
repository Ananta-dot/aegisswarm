# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form project context, experiment ledger, methodology, deadlines, and operating rules.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay. This is newer than the skill's current-status section when they differ.
3. [`OPTIMIZER_NATIVE_OBJECTIVE.md`](OPTIMIZER_NATIVE_OBJECTIVE.md) — active representation-ablation protocol.

## Non-negotiable operating rules

1. **Do not treat the current architecture as final.** We are still testing how learned/search-based strategy, optimization, rules, and later online adaptation should compose.
2. **Do not consume reserved confirmation seeds for development.** Check the seed ledger in the handoff documents and `aegisswarm/splits.py` first.
3. **Do not tune on a holdout after looking at it.** Once a block is inspected, it becomes development evidence and must never be described as untouched confirmation evidence.
4. **Do not change simulator/scoring/budgets mid-protocol** unless the experiment is explicitly invalidated and restarted under a new protocol ID.
5. **Compare components by ablation, not ideology.** Optimization, local search, RL, rules, and learned models are candidate components of AegisSwarm, not frameworks the product must defeat individually.
6. **Use equal simulator-evaluation budgets** when comparing search methods or representations unless the experiment explicitly studies compute scaling.
7. **Do not overclaim.** The current environment is synthetic and abstract. Existing RL and Hungarian baselines are deliberately simple and are not state-of-the-art representatives of their entire fields.
8. **Keep the project defensive and simulation-first.** Do not turn this repository into real-world weapon guidance, payload, targeting, interceptor engineering, or platform-specific engagement logic.
9. **Preserve reproducibility.** Record protocol IDs, seeds, budgets, source branch/commit, output artifacts, confidence intervals, and any architecture change prompted by inspected results.
10. **GitHub is the source of truth.** Keep the handoff/status documents updated when a major experiment finishes or the research direction changes.

## Most recent completed full-development conclusion

`aegisswarm-hybrid-objective-v1` produced:

```text
fixed_optimizer: 0.320
hybrid_local:     0.805
hybrid_axplorer:  0.810
Axplorer-local:  +0.0055, CI [-0.0235, +0.0320], p=0.507075
```

Conclusion:

- optimizer-aware strategy/objective search is valuable relative to the current fixed hand-written objective;
- Axplorer is statistically tied with optimizer-aware local/evolutionary search;
- proposer choice is now deprioritized;
- repeated ~80–81% performance suggests a representation and/or planning ceiling;
- `5000–5399` is consumed development data;
- do not run `8000–8399` confirmation.

## Optimizer-native V1 quick diagnosis

The first native representation was stopped before full development after quick mode produced:

```text
fixed_optimizer: 0.350
rule_objective:  0.688
native_v1:       0.300
native-rule:    -0.3875, CI [-0.650, -0.075], p=0.000100
```

This quick result exposed a malformed zero-centred native utility that frequently preferred no-op assignments and omitted state-reactive information already available to the rule comparator. **Do not interpret it as evidence against optimizer-native objectives generally.** V1 was invalidated before the full campaign.

## Current active experiment

Branch: `agent/optimizer-native-objective`  
Protocol: `aegisswarm-optimizer-native-objective-v2`

Question:

> Does a smooth, state-reactive optimizer-native strategic objective outperform the current 60-token rule representation when both are retrained from scratch under the same local/evolutionary search seeds, candidate budget, simulator, fitness, and Hungarian executor?

V2 shares the rule-guided policy's positive structural base utility and learns continuous modifiers for urgency, asset value, threat class, distance, capacity, scarcity, reserve/release behavior, persistence, speed, target damage, and urgency-scarcity interaction.

Development: `9000–9399` (development-only; first 20 already inspected during invalidated V1 quick).  
Reserved confirmation: `10000–10399` (untouched).

V2 uses new `artifacts/optimizer_native_v2_*` paths so V1 quick artifacts cannot be resumed.

Do **not** run confirmation after development automatically. Interpret the development result and make an explicit freeze/no-freeze decision first.
