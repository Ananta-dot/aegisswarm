# AegisSwarm Rolling-Horizon Planning Screen

**Status:** architecture development; not frozen  
**Branch:** `agent/rolling-horizon-planning`  
**Protocol:** `aegisswarm-rolling-horizon-screen-v1`

## Why this experiment exists

The corrected optimizer-native V2 representation was materially worse than the incumbent 60-token state-reactive rule representation:

```text
rule_objective survival:       0.813
native_objective_v2 survival:  0.701
native - rule:                -0.1120
95% CI:                        [-0.1405, -0.08249]
p-value:                        0.000050
```

The representation track is therefore closed. The next hypothesis is that the current one-step Hungarian executor is too myopic.

## Screening question

Before paying for another 5 x 1,800 candidate training campaign, hold the five strong discovered rule programs fixed and compare only their execution:

```text
same 60-token strategy + one-step Hungarian
same 60-token strategy + short rolling-horizon planner
```

This is a screen, not final evidence. A positive screen justifies planner-aware retraining; it does not establish the final architecture.

## Planner

`RuleGuidedRollingHorizonPolicy` reuses the exact rule-derived pair utility from `RuleGuidedHungarianPolicy`.

At each simulator step it:

1. projects currently detected synthetic threats linearly for a short horizon;
2. builds a time-indexed binary allocation problem;
3. constrains each defender to at most one planned assignment per timestep;
4. constrains cumulative planned uses by each defender's remaining abstract capacity;
5. gives each threat at most one deterministic planned attempt over the short horizon;
6. maximizes discounted rule-derived utility;
7. executes only the first-step assignments;
8. discards the rest of the plan and re-solves after the next observation.

This is an abstract receding-horizon/MPC-style decision experiment, not real-world guidance or engagement engineering.

## Evidence blocks

- planning development: `13000–13399`
- reserved planning confirmation: `14000–14399`

Quick mode uses `13000–13019`; once inspected those are simply part of planning development.

Do not inspect `14000–14399` during architecture iteration.

## Incumbent strategy artifacts

The screen loads the five rule programs trained during optimizer-native V2 development:

```text
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44001.json
...
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44005.json
```

These are held fixed so the screen changes execution only.

## Commands

```bash
git checkout agent/rolling-horizon-planning
git pull origin agent/rolling-horizon-planning
pytest -q
python -m aegisswarm.rolling_horizon_cli --workers 5
```

Expected header:

```text
AegisSwarm rolling-horizon screen
```

Expected summary:

```text
=== ROLLING-HORIZON SCREEN ===
fixed_optimizer survival: ...
rule_one_step survival:   ...
rule_rolling survival:    ...
difference (R-O):         ...
paired p-value:           ...
runtime one-step/rolling: ...
```

Do not run the full 400-scenario screen until quick output and runtime are inspected.

## Decision gate

### Promising

If rolling horizon improves survival or produces a useful survival/resource tradeoff without pathological runtime, build a new planner-aware training protocol in which every candidate 60-token program is scored through the rolling-horizon executor.

### Rough tie

A tie can still justify planner-aware training if the planning screen reveals better resource preservation/tail behavior, but do not assume it will improve after training.

### Clearly worse

Diagnose the planning formulation once. If the corrected planner remains materially worse, keep one-step rule-guided Hungarian as the executor and move to a different bottleneck such as simulator uncertainty/state estimation rather than endlessly increasing horizon complexity.
