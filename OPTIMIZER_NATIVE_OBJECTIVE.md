# AegisSwarm Optimizer-Native Objective Experiment

**Status:** architecture development; not frozen  
**Branch:** `agent/optimizer-native-objective`  
**Protocol:** `aegisswarm-optimizer-native-objective-v2`

## Why this experiment exists

Several serious AegisSwarm variants have clustered around roughly 80–81% asset survival on their respective development/formal blocks. The previous optimizer-aware experiment also showed that Axplorer V2 and conventional local/evolutionary search were statistically tied while both strongly outperformed the current fixed hand-written objective.

The current hypothesis is that the bottleneck may be the **strategic representation** supplied to the optimizer rather than proposer choice.

## V1 — completed development, then rejected

The first 10-parameter native representation used a zero-centred utility while the rule-guided comparator always inherited a positive structural base. It also omitted useful state-reactive signals.

The full V1 development campaign on `9000–9399` completed before the V2 patch was pulled locally:

```text
fixed_optimizer survival: 0.310
rule_objective survival:  0.787 CI=[0.75449375, 0.81675]
native_v1 survival:       0.359 CI=[0.30475, 0.43125625]
native - rule:           -0.4280 CI=[-0.4845, -0.3590]
paired p-value:            0.000050
```

A final V1 training log showed one native run at about `0.812` survival on its 16 training scenarios while the five-run 400-scenario development mean was only `0.359`, reinforcing severe generalization failure.

V1 is therefore a useful negative experiment but is **not** the architecture to continue. Do not rerun/tune it, and never call `9000–9399` fresh again.

## V2 representation ablation

The control remains the current 12-rule / 60-token program executed through `RuleGuidedHungarianPolicy`.

V2 is a **14-parameter smooth optimizer-native objective**. It shares the rule-guided policy's structural base:

```text
2 * abstract threat-type prior
+ inverse target-asset distance term
+ inverse defender/threat distance term
```

and learns continuous modifiers for:

1. urgency
2. protected-asset value
3. FAST-class modifier
4. DIRECT-class modifier
5. DECOY-class modifier
6. defender/threat closeness
7. defender capacity
8. resource-scarcity penalty
9. reserve threshold
10. urgency threshold that releases reserve
11. assignment persistence
12. abstract speed
13. target-asset damage state
14. urgency × scarcity interaction

The Hungarian layer remains responsible for feasible one-to-one assignment and explicit no-op choices.

## Fairness controls

Full V2 development uses:

- five matched search seeds `44001–44005`;
- the same 16 training scenarios;
- 1,800 unique candidate evaluations per representation/run;
- the same local/evolutionary search family;
- the same simulator;
- the same scalar fitness;
- the same per-step Hungarian executor.

The 60-token comparator is retrained from scratch. V2 receives no hand-written warm start.

## Primary comparison

```text
fixed hand-written objective + optimizer
60-token searched rule objective + optimizer
14-parameter optimizer-native V2 objective + optimizer
```

Primary effect:

```text
optimizer-native V2 - 60-token rule objective
```

Asset survival is primary; containment, penetration, damage, resource use, response delay, and runtime remain secondary.

## Fresh V2 evidence blocks

Because the entire V1 development block was inspected and directly informed V2 design, V2 does **not** reuse it.

- V2 development: `11000–11399`
- V2 reserved confirmation: `12000–12399`

The old `10000–10399` V1 confirmation block remains untouched but should not be silently repurposed as V2 confirmation.

Confirmation is code-gated by `architecture_frozen`.

## Artifacts

```text
artifacts/optimizer_native_v2_quick/
artifacts/optimizer_native_v2_dev/
artifacts/optimizer_native_v2_confirm/
```

If output instead uses `artifacts/optimizer_native_dev` or prints `[native-local ...]`, the local checkout is stale V1 code.

## Decision gate

If V2 clearly improves over the 60-token representation by an operationally meaningful amount, inspect secondary metrics and run stability before considering a freeze.

If V2 and rule remain tied near the existing plateau, stop representation tuning and move to the **myopic planning horizon**.

If V2 remains materially worse, keep the 60-token representation and move to planning rather than adding parameters merely to force a win.

## Commands

```bash
git checkout agent/optimizer-native-objective
git pull origin agent/optimizer-native-objective
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

The quick output must say `OPTIMIZER-NATIVE OBJECTIVE V2`.

If quick V2 is no longer pathologically worse:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do **not** run confirmation automatically after development.
