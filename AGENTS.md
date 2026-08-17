# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read:

- [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical project context, experiment ledger, current hypothesis, decision gates, deadlines, and operating rules.

## Non-negotiable operating rules

1. **Do not treat the current architecture as final.** We are still testing how learned strategy, local/evolutionary search, constrained optimization, rules, and later online adaptation should compose.
2. **Do not consume reserved confirmation seeds for development.** Check the seed ledger in `docs/AEGISSWARM_SKILL.md` and `aegisswarm/splits.py` first.
3. **Do not tune on a holdout after looking at it.** Once a block is inspected, it becomes development evidence and must never be described as untouched confirmation evidence.
4. **Do not change simulator/scoring/budgets mid-protocol** unless the experiment is explicitly invalidated and restarted under a new protocol ID.
5. **Compare components by ablation, not ideology.** Optimization, local search, RL, rules, and learned models are candidate components of AegisSwarm, not frameworks the product must defeat individually.
6. **Use equal simulator-evaluation budgets** when comparing search methods unless the experiment explicitly studies compute scaling.
7. **Do not overclaim.** The current environment is synthetic and abstract. Existing RL and Hungarian baselines are deliberately simple and are not state-of-the-art representatives of their entire fields.
8. **Keep the project defensive and simulation-first.** Do not turn this repository into real-world weapon guidance, payload, targeting, interceptor engineering, or platform-specific engagement logic.
9. **Preserve reproducibility.** Record protocol IDs, seeds, budgets, source branch/commit, output artifacts, confidence intervals, and any architecture change prompted by inspected results.
10. **GitHub is the source of truth.** Prefer changes on the active `agent/*` branch and keep the handoff document updated when a major experiment finishes or the research direction changes.

## Current research question

The immediate question is no longer "can Axplorer beat optimization?" It is:

> Can AegisSwarm learn a better strategic objective for a constrained optimizer, and does a learned generative proposer add value beyond equally budgeted conventional search when both use the same optimizer?

Current active branch: `agent/hybrid-objective-learning`.

Current active protocol: `aegisswarm-hybrid-objective-v1`.

Do **not** run confirmation merely because development completes. First interpret the development result, decide whether the architecture/hyperparameters are frozen, and record that decision.
