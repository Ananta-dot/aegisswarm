# AegisSwarm Optimizer-Native Objective Experiment

**Status:** architecture development; not frozen  
**Branch:** `agent/optimizer-native-objective`  
**Protocol:** `aegisswarm-optimizer-native-objective-v1`

## Why this experiment exists

Several serious AegisSwarm variants have clustered around roughly 80–81% asset survival on their respective development/formal blocks. The previous optimizer-aware experiment also showed that Axplorer V2 and conventional local/evolutionary search were statistically tied while both strongly outperformed the current fixed hand-written objective.

The next hypothesis is therefore that the bottleneck is no longer the search proposer. It may be the **strategic representation** supplied to the optimizer.

This experiment changes only that representation.

## Representation ablation

The control representation is the current 12-rule / 60-token program executed through `RuleGuidedHungarianPolicy`.

The new representation is a compact 10-parameter optimizer-native strategic objective:

1. urgency weight
2. protected-asset value weight
3. FAST-class weight
4. DIRECT-class weight
5. DECOY-class weight
6. defender/threat distance weight
7. resource-scarcity penalty
8. reserve threshold
9. assignment-persistence weight
10. abstract speed weight

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
- fresh development scenarios `9000–9399`.

The experiment retrains the 60-token representation from scratch under the same seeds/budget instead of comparing against old artifacts.

## Primary comparison

```text
fixed hand-written objective + optimizer
60-token searched rule objective + optimizer
10-parameter searched optimizer-native objective + optimizer
```

The primary effect is:

```text
optimizer-native objective - 60-token rule objective
```

Asset survival is primary; containment, penetration, damage, resource use, response delay, and runtime remain secondary metrics.

## Development decision gate

A useful result would be an operationally meaningful positive representation effect, preferably several percentage points with a paired hierarchical confidence interval supporting a real gain.

If the optimizer-native representation clearly improves over the 60-token representation, freeze only after checking secondary metrics and run-to-run stability.

If the representations remain tied near the existing ~80–81% region, treat that as evidence that the **myopic one-step optimizer/planning horizon** is the next bottleneck. Do not respond by adding another proposer model.

## Seeds

- development: `9000–9399`
- reserved confirmation: `10000–10399`

The confirmation block is code-gated by `architecture_frozen` in the development protocol. Do not enable it until an explicit freeze decision.

## Commands

Quick integration check:

```bash
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

Full development:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do **not** run confirmation after development automatically.
