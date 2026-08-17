# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/hybrid-objective-learning`  
**Active completed development protocol:** `aegisswarm-hybrid-objective-v1`

This file is the **current-state overlay** for `docs/AEGISSWARM_SKILL.md`. Read the skill first for full history, then read this file for the most recent experiment and decision. When they differ on current status, this file is newer.

## Latest full development result

Hybrid-objective development, 5 matched search seeds, 16 training scenarios, 1,800 unique candidate evaluations per search method/run, evaluated on development seeds `5000–5399`:

```text
fixed_optimizer survival: 0.320
hybrid_local survival:    0.805 CI=[0.77624375, 0.83100625]
hybrid_axplorer survival: 0.810 CI=[0.77775, 0.841]
Axplorer - local:         +0.0055 CI=[-0.0235, +0.0320]
paired p-value:           0.507075
```

## Interpretation

1. **Optimizer-aware strategy search is useful relative to the current hand-written fixed objective.** Both searched strategies are far stronger than the current fixed-objective Hungarian baseline in this synthetic simulator.
2. **Axplorer does not add a demonstrated material advantage over optimizer-aware local/evolutionary search.** The point estimate is only +0.55 percentage points, the paired hierarchical interval crosses zero, and p=0.507.
3. This is **development evidence**, not confirmation. Seeds `5000–5399` are now consumed development data.
4. **Do not run `8000–8399` confirmation.** The architecture is not frozen and the Axplorer increment is not compelling enough to justify spending the reserved block.
5. Do not say "AegisSwarm beats optimization." The fixed optimizer is a deliberately simple, myopic, hand-designed-objective baseline. The result instead supports the narrower statement that **objective/strategy design matters substantially for the current optimizer**.

## Major architectural conclusion

Across several generations, the strongest serious variants are clustering around roughly 80–81% survival on their respective development/formal blocks:

- structured local: about 80%
- structured Axplorer V1/V2: about 81%
- optimizer-aware hybrid local: 80.5%
- optimizer-aware hybrid Axplorer: 81.0%

Do not compare those percentages as if they came from identical evaluation blocks, but the repeated plateau is a strong development signal.

The project should therefore stop treating **search proposer choice** as the primary bottleneck. Another round of Axplorer-only tuning is low priority unless a specific diagnosis justifies it.

The next bottleneck hypothesis is:

> **The current strategic representation and/or myopic per-step optimizer is limiting performance more than the choice between local search and Axplorer.**

## Provisional method decision

For the next architecture stage, use optimizer-aware local/evolutionary search as the **strong default offline search engine** because it is simpler, cheaper, and statistically tied with Axplorer under the current protocol.

Do not delete Axplorer. Keep it as an optional proposer/ablation and revisit it if the next representation becomes sufficiently structured/high-dimensional that learned proposal could plausibly help.

## Recommended next experiment

Do **one architectural change at a time**.

Preferred next step: create a new protocol around a more optimizer-native strategic objective rather than another generic 60-token rule-program iteration.

The abstract strategy should parameterize quantities such as:

- urgency/risk weighting;
- protected-asset importance;
- abstract threat-class weighting;
- distance/cost weighting;
- resource-scarcity and reserve preference;
- assignment persistence;
- uncertainty/risk-aversion terms.

The optimizer remains responsible for feasible assignment. Keep the representation abstract and defensive.

First compare:

```text
fixed objective + current optimizer
searched optimizer-native objective + current optimizer
```

using local/evolutionary search only. This isolates whether the **objective representation** itself breaks the ~80% plateau.

Only if that representation improves the system should we then compare Axplorer or another learned proposer in the new space.

After that, the next major hypothesis is a short rolling-horizon/planning optimizer rather than the current purely myopic assignment layer. That should be a separate protocol because it changes execution semantics.

## Seed ledger update

`5000–5399` is now **consumed hybrid-objective development**.

Keep untouched:

- `6000–6399`: reserved V2 confirmation; do not use casually.
- `7000–7399`: reserved executor-swap confirmation; likely obsolete unless that architecture is revived.
- `8000–8399`: reserved hybrid-objective confirmation; **do not consume** because current architecture is not frozen.

A materially new objective representation should receive a **new development block and new reserved confirmation block** rather than reusing `8000–8399`.

## Claims update

Supported development-level statement:

> In the current synthetic simulator, searching the strategic objective used by the per-step Hungarian assignment layer yields substantially better asset survival than the current fixed hand-written objective. Under equal candidate-evaluation budgets, Axplorer V2 and conventional local/evolutionary search produce statistically indistinguishable optimizer-aware strategies on the 400-scenario development block.

Not supported:

- Axplorer superiority.
- superiority to optimization generally.
- superiority to state-of-the-art RL/MARL.
- real-world counter-swarm effectiveness.
- deployment readiness.

## Immediate decision

**NO FREEZE. NO CONFIRMATION.**

The next work should target the representation/planning bottleneck, not another proposer-only iteration.
