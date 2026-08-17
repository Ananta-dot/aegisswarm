# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/optimizer-native-objective`  
**Active protocol:** `aegisswarm-optimizer-native-objective-v2`

This is the current-state overlay for `docs/AEGISSWARM_SKILL.md`. Read the long-form skill for project history and this file for the latest experiment/decision.

## Strongest completed full-development result before the active representation track

Hybrid-objective protocol `aegisswarm-hybrid-objective-v1`, consumed development seeds `5000–5399`:

```text
fixed_optimizer survival: 0.320
hybrid_local survival:    0.805 CI=[0.77624375, 0.83100625]
hybrid_axplorer survival: 0.810 CI=[0.77775, 0.841]
Axplorer - local:         +0.0055 CI=[-0.0235, +0.0320]
paired p-value:           0.507075
```

Decision:

- optimizer-aware objective search is highly valuable relative to the current fixed hand-written objective;
- Axplorer does not demonstrate a material increment over optimizer-aware local/evolutionary search;
- proposer choice is deprioritized;
- architecture remains unfrozen;
- do not run the old `8000–8399` hybrid-objective confirmation block.

## Current bottleneck hypothesis

Several serious architectures have repeatedly clustered around roughly 80–81% survival on their respective development/formal blocks. These are different seed blocks, so do not compare them as a single leaderboard, but the repeated plateau motivates:

> **The strategic representation and/or the myopic one-step assignment layer is now a more plausible bottleneck than proposer choice.**

## Optimizer-native V1 — FULL DEVELOPMENT COMPLETED, THEN INVALIDATED

The original 10-parameter optimizer-native representation used a zero-centred utility instead of inheriting the rule-guided policy's positive structural base utility. It also omitted useful state-reactive signals.

Quick mode first showed a pathological gap. Before the V2 patch was pulled locally, the full V1 campaign also completed on seeds `9000–9399`:

```text
fixed_optimizer survival: 0.310
rule_objective survival:  0.787 CI=[0.75449375, 0.81675]
native_v1 survival:       0.359 CI=[0.30475, 0.43125625]
native - rule:           -0.4280 CI=[-0.4845, -0.3590]
paired p-value:            0.000050
```

The final V1 training log also showed one native run reaching about `0.812` survival on its 16 training scenarios while the five-run development evaluation averaged only `0.359`, indicating severe generalization failure in addition to the representation defect.

### Correct interpretation

This is a valid **negative result for optimizer-native V1**, but not evidence that optimizer-native strategic objectives are intrinsically inferior.

V1 is invalidated as the candidate architecture because:

1. its utility semantics were not comparable to the rule-guided comparator;
2. it could reject reachable threats as non-positive/no-op candidates before learning meaningful rankings;
3. it omitted target-damage and richer reserve/release state signals;
4. it generalized very poorly from the small training bundle to the 400-scenario development block.

Do not rerun or tune V1. Do not use `9000–9399` as fresh evidence again.

## Active experiment — optimizer-native V2

Protocol: `aegisswarm-optimizer-native-objective-v2`

V2 keeps the representation hypothesis but fixes the semantics. It shares the exact structural base used by `RuleGuidedHungarianPolicy`:

```text
2 * abstract threat-type prior
+ inverse target-asset distance term
+ inverse defender/threat distance term
```

Search then learns 14 smooth state modifiers covering:

- urgency;
- protected-asset value;
- threat-class modifiers;
- defender/threat closeness;
- defender capacity;
- resource scarcity;
- reserve threshold;
- urgency threshold that releases reserve;
- assignment persistence;
- speed;
- target-asset damage state;
- urgency × scarcity interaction.

The optimizer still owns feasible one-to-one assignment and no-op choices.

Both V2 native and the 60-token rule comparator start from stochastic candidates and use the same local/evolutionary search family, matched seeds, simulator, fitness, Hungarian executor, and candidate-evaluation budget.

### Fresh V2 evidence blocks

Because the entire V1 development block was inspected and directly informed V2 design, V2 has fresh blocks:

- `11000–11399`: **V2 development**;
- `12000–12399`: **V2 reserved confirmation**.

`10000–10399` remains untouched but belongs to the abandoned V1 evidence plan. Do not silently repurpose it as V2 confirmation.

V2 uses separate artifact paths:

```text
artifacts/optimizer_native_v2_quick/
artifacts/optimizer_native_v2_dev/
artifacts/optimizer_native_v2_confirm/
```

## Immediate runbook

First pull the V2 code. The expected logs must say `optimizer-native-v2`, `native-v2-local`, and `OPTIMIZER-NATIVE OBJECTIVE V2`.

```bash
git checkout agent/optimizer-native-objective
git pull origin agent/optimizer-native-objective
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

Do **not** launch full development if the output still says `native-local` or saves to `artifacts/optimizer_native_quick`; that means the checkout is stale.

If quick V2 is no longer pathologically worse, then run:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do not run `--confirm` until the full V2 development result is interpreted and an explicit freeze decision is recorded.

## Decision tree

### V2 materially beats the 60-token rules

Inspect secondary metrics, run stability, runtime, and the primary estimand. Freeze only if the gain is operationally meaningful and robust; then consider `12000–12399` confirmation once.

### V2 ties the rule representation near the plateau

Stop representation tuning. Move to a new protocol for a short rolling-horizon/MPC-style abstract planner.

### V2 remains materially worse

Keep the 60-token representation and move to planning. Do not keep adding vector parameters merely to force a representation win.

## Seed ledger update

Consumed:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development, fully consumed and invalidated as an architecture.

Untouched older reserved blocks:

- `6000–6399`: Axplorer V2 confirmation;
- `7000–7399`: executor-swap confirmation;
- `8000–8399`: hybrid-objective confirmation;
- `10000–10399`: old V1-native reserved confirmation; do not repurpose silently.

Active V2:

- `11000–11399`: development;
- `12000–12399`: reserved confirmation.

## Claims policy

Supported development-level statement:

> In the current synthetic simulator, optimizer-aware search of a strategic objective substantially improves the current myopic fixed-objective Hungarian baseline. Axplorer and local/evolutionary search were statistically indistinguishable under the completed hybrid-objective protocol. A first compact optimizer-native V1 representation generalized very poorly and was rejected; a semantically corrected V2 representation is now being evaluated on fresh development data.

Not supported:

- Axplorer superiority;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world counter-swarm effectiveness;
- deployment readiness.

## External target

The project continues to work backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-verify the official source before submission work.
