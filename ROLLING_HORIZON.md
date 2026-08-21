# AegisSwarm Rolling-Horizon Planning Screen

**Status:** architecture development; not frozen  
**Branch:** `agent/rolling-horizon-planning`  
**Active protocol:** `aegisswarm-rolling-horizon-screen-v2`

## Why this track exists

The corrected optimizer-native V2 representation was materially worse than the incumbent 60-token state-reactive rule representation. The representation track is therefore closed and the incumbent strategy remains the 60-token rule program executed through optimization.

The next hypothesis is temporal: can short receding-horizon planning improve scarce-resource allocation relative to the current one-step Hungarian executor?

## Planner V1 — completed fixed-program screen

V1 held the five strong rule programs fixed and changed only execution:

```text
same 60-token strategy + one-step Hungarian
same 60-token strategy + horizon-4 rolling planner
```

Full development on consumed seeds `13000–13399`:

```text
fixed_optimizer survival: 0.310
rule_one_step survival:   0.782 CI=[0.739, 0.81775]
rule_rolling survival:    0.752 CI=[0.7125, 0.7900]
rolling - one_step:      -0.0300 CI=[-0.07775, +0.01825625]
scenario-level sign-flip p-value: 0.000700
runtime one-step/rolling: 0.0125 s / 0.1837 s
```

V1 did **not** earn planner-aware retraining.

The small p-value and hierarchical interval crossing zero summarize different uncertainty structures: the scenario-level sign-flip test averages over the five frozen programs first; the hierarchical interval resamples both programs and scenarios. Treat the hierarchical interval plus per-program effects as the primary architecture-level uncertainty summary.

## V1 diagnosis — receding-horizon action deferral

V1 projected each detected threat forward and then re-evaluated the existing state-reactive rule utility on those projected states.

That allowed a currently feasible threat to receive a larger h>0 score simply because it would be closer to its protected asset and might satisfy stronger urgency rules later. The MILP could schedule that action in the future. Because only h=0 is executed and the plan is recomputed on the next step, the action could repeatedly be pushed forward.

This is a standard receding-horizon procrastination pathology.

## Planner V2 — targeted correction

V2 changes one semantic only.

For each defender/threat pair:

1. compute its current rule-derived pair utility;
2. project the threat forward to determine future reachability and whether it is predicted to have reached its synthetic target;
3. compute projected utility;
4. if the pair is already feasible and strategically positive now, cap every future strategic value at the current value;
5. apply temporal discounting;
6. optimize the horizon allocation;
7. execute h=0 only and replan after the next observation.

Thus an already-feasible assignment cannot become more attractive merely by waiting. Future-only reachable opportunities are still represented normally.

The planner remains abstract and synthetic. It does not add real-world platform guidance, interceptor physics, payloads, or engagement engineering.

## Evidence blocks

Planner V1:

- development `13000–13399` — consumed;
- old reserved confirmation `14000–14399` — untouched but tied to V1, do not repurpose silently.

Planner V2:

- development `15000–15399`;
- reserved confirmation `16000–16399`.

Quick V2 uses `15000–15019` and is development-only.

## Incumbent strategy artifacts

V2 still holds fixed the five rule programs trained during optimizer-native V2 development:

```text
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44001.json
...
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44005.json
```

This means the V2 screen still isolates executor/planner semantics. It is **not** planner-aware strategy training.

## Commands

```bash
git checkout agent/rolling-horizon-planning
git pull origin agent/rolling-horizon-planning
pytest -q
python -m aegisswarm.rolling_horizon_cli --workers 5
```

Expected header and artifact:

```text
AegisSwarm rolling-horizon V2 screen
=== ROLLING-HORIZON V2 SCREEN ===
Saved: artifacts/rolling_horizon_v2_quick
```

V2 additionally prints the five per-program survival deltas.

Do not run the 400-scenario V2 screen until the fresh quick screen is interpreted.

## Decision gate

### V2 materially positive / clearly no longer harmful

Run the full `15000–15399` development screen. Planner-aware 60-token training is considered only after that full result.

### V2 rough tie

Inspect per-program deltas, penetrations, damage, resource use and runtime. A tie by itself does not justify an expensive planner-aware search campaign.

### V2 still materially worse

Stop this rolling-horizon formulation. Retain the one-step `RuleGuidedHungarianPolicy` executor and move to another bottleneck rather than repeatedly increasing horizon/complexity.

## Confirmation discipline

Do not inspect `16000–16399` unless a later planner-aware architecture is explicitly frozen. A positive screening result alone is not sufficient to consume confirmation data.
