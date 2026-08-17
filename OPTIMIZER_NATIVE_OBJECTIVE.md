# AegisSwarm Optimizer-Native Objective Experiment

**Status:** architecture development; not frozen  
**Branch:** `agent/optimizer-native-objective`  
**Protocol:** `aegisswarm-optimizer-native-objective-v2`

## Why this experiment exists

Several serious AegisSwarm variants have clustered around roughly 80–81% asset survival on their respective development/formal blocks. The previous optimizer-aware experiment also showed that Axplorer V2 and conventional local/evolutionary search were statistically tied while both strongly outperformed the current fixed hand-written objective.

The next hypothesis is therefore that the bottleneck is no longer the search proposer. It may be the **strategic representation** supplied to the optimizer.

This experiment changes only that representation.

## V1 quick diagnosis — invalidated before full development

The first compact native representation was tested only in quick mode on the first 20 development scenarios:

```text
fixed_optimizer survival: 0.350
rule_objective survival:  0.688 CI=[0.400, 0.925]
native_objective survival:0.300 CI=[0.175, 0.425]
native - rule:            -0.3875 CI=[-0.650, -0.075]
paired p-value:            0.000100
```

The result exposed a representation defect rather than a useful architecture comparison:

- V1 computed a zero-centred weighted utility while the rule-guided policy always received a positive structural base utility;
- reachable threats could therefore be rejected as non-positive/no-op candidates before search had learned useful ranking structure;
- V1 also omitted state-reactive signals available to the rule comparator, including target damage and explicit reserve/release interaction.

V1 was therefore **stopped before full development**. Do not interpret its quick result as evidence that optimizer-native objectives are intrinsically inferior.

## V2 representation ablation

The control representation remains the current 12-rule / 60-token program executed through `RuleGuidedHungarianPolicy`.

V2 is a compact **14-parameter smooth optimizer-native objective**. It shares the rule-guided policy's structural base utility and learns continuous state modifiers for:

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

The shared structural base is:

```text
2 * abstract threat-type prior
+ inverse target-asset distance term
+ inverse defender/threat distance term
```

This is deliberately the same base used by the rule-guided Hungarian policy, so the representation comparison is about strategic modifiers rather than whether a candidate learns to assign any positive utility at all.

These are synthetic coordination preferences, not platform parameters or real-world engagement doctrine.

The Hungarian layer remains responsible for feasible one-to-one assignment and explicit no-op choices.

## Fairness controls

Full development uses:

- five matched search seeds: `44001–44005`;
- the same 16 training scenarios;
- 1,800 unique candidate evaluations per representation/run;
- the same local/evolutionary search family;
- the same simulator;
- the same scalar fitness function;
- the same per-step Hungarian executor;
- development scenarios `9000–9399`.

The 60-token representation is retrained from scratch under the same seeds/budget instead of comparing against old artifacts.

V2 native search does **not** receive a hand-written warm start.

## Primary comparison

```text
fixed hand-written objective + optimizer
60-token searched rule objective + optimizer
14-parameter searched optimizer-native V2 objective + optimizer
```

The primary effect is:

```text
optimizer-native V2 objective - 60-token rule objective
```

Asset survival is primary; containment, penetration, damage, resource use, response delay, and runtime remain secondary metrics.

## Development decision gate

If V2 clearly improves over the 60-token representation by an operationally meaningful amount, inspect secondary metrics and run-to-run stability before considering a freeze.

If V2 and the rule representation remain tied around the existing plateau, stop representation tuning and move to the **myopic one-step optimizer/planning horizon** as the next bottleneck hypothesis.

If V2 remains materially worse, keep the 60-token representation and move to planning. Do not keep adding parameters merely to force a representation win.

## Seeds

- development: `9000–9399`
- reserved confirmation: `10000–10399`

The first 20 development seeds have already been inspected by the invalidated V1 quick experiment. That is acceptable because this whole block is development-only; it must never be called untouched confirmation evidence.

The confirmation block remains untouched and is code-gated by `architecture_frozen` in the development protocol.

## Artifacts

V2 uses separate output directories so V1 quick artifacts cannot be resumed accidentally:

```text
artifacts/optimizer_native_v2_quick/
artifacts/optimizer_native_v2_dev/
artifacts/optimizer_native_v2_confirm/
```

## Commands

After pulling the latest branch:

```bash
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

If V2 quick is no longer pathologically worse, run full development:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do **not** run confirmation after development automatically.
