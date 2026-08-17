# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form project context, experiment ledger, methodology, deadlines, and operating rules.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay. This is newer than the skill's current-status section when they differ.

## Non-negotiable operating rules

1. **Do not treat the current architecture as final.** We are still testing how learned strategy, local/evolutionary search, constrained optimization, rules, and later online adaptation should compose.
2. **Do not consume reserved confirmation seeds for development.** Check the seed ledger in the handoff documents and `aegisswarm/splits.py` first.
3. **Do not tune on a holdout after looking at it.** Once a block is inspected, it becomes development evidence and must never be described as untouched confirmation evidence.
4. **Do not change simulator/scoring/budgets mid-protocol** unless the experiment is explicitly invalidated and restarted under a new protocol ID.
5. **Compare components by ablation, not ideology.** Optimization, local search, RL, rules, and learned models are candidate components of AegisSwarm, not frameworks the product must defeat individually.
6. **Use equal simulator-evaluation budgets** when comparing search methods unless the experiment explicitly studies compute scaling.
7. **Do not overclaim.** The current environment is synthetic and abstract. Existing RL and Hungarian baselines are deliberately simple and are not state-of-the-art representatives of their entire fields.
8. **Keep the project defensive and simulation-first.** Do not turn this repository into real-world weapon guidance, payload, targeting, interceptor engineering, or platform-specific engagement logic.
9. **Preserve reproducibility.** Record protocol IDs, seeds, budgets, source branch/commit, output artifacts, confidence intervals, and any architecture change prompted by inspected results.
10. **GitHub is the source of truth.** Keep the handoff/status documents updated when a major experiment finishes or the research direction changes.

## Current research conclusion

The completed `aegisswarm-hybrid-objective-v1` development run produced:

```text
fixed_optimizer: 0.320
hybrid_local:     0.805
hybrid_axplorer:  0.810
Axplorer-local:  +0.0055, CI [-0.0235, +0.0320], p=0.507075
```

Interpretation:

- optimizer-aware strategy/objective search is useful relative to the current fixed hand-written objective;
- Axplorer is statistically tied with optimizer-aware local/evolutionary search under the current protocol;
- the repeated ~80–81% plateau suggests the next bottleneck is likely strategic representation and/or myopic planning, not proposer choice;
- **architecture remains unfrozen**;
- **do not run `8000–8399` confirmation**.

Current branch: `agent/hybrid-objective-learning`.

Current decision: **NO FREEZE. NO CONFIRMATION. Move next toward a new representation/planning hypothesis under a new protocol.**
