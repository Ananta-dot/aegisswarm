# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/rolling-horizon-planning`  
**Active protocol:** `aegisswarm-rolling-horizon-screen-v2`

Read `docs/AEGISSWARM_SKILL.md` for full history. This file is the latest-state overlay.

## Incumbent architecture before planning

The optimizer-native representation track is closed. On fresh development seeds `11000–11399`:

```text
fixed_optimizer survival:      0.320
rule_objective survival:       0.813 CI=[0.78149375, 0.841]
native_objective_v2 survival:  0.701 CI=[0.66275, 0.7355]
native - rule:                -0.1120 CI=[-0.1405, -0.08249375]
paired p-value:                0.000050
```

Decision:

- retain the 60-token state-reactive rule representation;
- no optimizer-native V3;
- do not consume `12000–12399` confirmation;
- proposer/representation tuning is deprioritized.

## Rolling-horizon planner V1 — full screen completed

The first planning screen held the five already-trained strong 60-token rule programs fixed and changed only execution from one-step Hungarian matching to a horizon-4 receding-horizon MILP.

Full development screen on consumed seeds `13000–13399`:

```text
fixed_optimizer survival: 0.310
rule_one_step survival:   0.782 CI=[0.739, 0.81775]
rule_rolling survival:    0.752 CI=[0.7125, 0.7900]
rolling - one_step:      -0.0300 CI=[-0.07775, +0.01825625]
scenario-level sign-flip p-value: 0.000700
runtime one-step/rolling: 0.0125 s / 0.1837 s per scenario
```

### Interpretation

1. Planner V1 **did not earn planner-aware retraining**. The point estimate is -3.0 percentage points and runtime is about 15x one-step execution.
2. The paired hierarchical interval crosses zero, so the architecture-level effect is not robustly separated from zero once variation across the five frozen programs is included.
3. The very small sign-flip p-value is not directly contradictory: that test first averages the five program-specific differences for each scenario and tests scenario-level consistency, whereas the hierarchical interval resamples both programs and scenarios.
4. There is therefore no positive evidence for V1. The correct action is diagnose the formulation once, not train through it or increase horizon blindly.

## Concrete V1 defect found — receding-horizon procrastination

V1 projected threats into future states and then called the existing state-reactive rule utility on those future states.

That creates a temporal incentive problem:

- a threat can be reachable and worth acting on now;
- at h>0 it is projected closer to the protected asset and may trigger stronger urgency-conditioned rules;
- its future utility can therefore exceed its current utility despite temporal discounting;
- the MILP may schedule it for h>0;
- only h=0 is actually executed;
- on the next simulator step the problem is solved again and the action can again be pushed into the future.

This is a receding-horizon action-deferral/procrastination pathology. It is a planner formulation issue, not evidence that temporal planning in general is useless.

## Active experiment — rolling-horizon planner V2

Protocol: `aegisswarm-rolling-horizon-screen-v2`

V2 changes one planning semantic only:

> Projection controls future reachability, but an already-feasible defender/threat pair is not allowed to become more valuable merely because execution is delayed.

Implementation rule:

- compute current rule-derived pair utility;
- compute projected future utility/reachability;
- if the pair is already positive/feasible now, cap each h>0 strategic value at the current value;
- then apply temporal discounting;
- future-only reachable pairs may still enter the horizon normally.

This preserves the winning 60-token strategic representation and the same planning structure while directly removing the diagnosed deferral incentive.

## Fresh planner V2 evidence

Because V2 was designed after inspecting the entire V1 development screen, it receives fresh blocks:

- `15000–15399`: **planner V2 development**;
- `16000–16399`: **planner V2 reserved confirmation**.

Do not reuse:

- `13000–13399`: consumed planner-V1 development;
- `14000–14399`: untouched but tied to the abandoned planner-V1 evidence plan; do not silently repurpose it.

## Statistical reporting change

Planner V2 reports all three of the following for survival:

1. paired mean effect and hierarchical 95% CI across programs + scenarios;
2. the five per-program mean survival deltas;
3. scenario-level sign-flip p-value.

The hierarchical interval is the primary architecture-level uncertainty summary because the five rule programs represent independent discovered strategies. The scenario-level sign-flip result is supplementary.

## Immediate runbook

Pull the V2 code and run tests:

```bash
git checkout agent/rolling-horizon-planning
git pull origin agent/rolling-horizon-planning
pytest -q
```

Then run the fresh V2 quick screen only:

```bash
python -m aegisswarm.rolling_horizon_cli --workers 5
```

Expected markers:

```text
AegisSwarm rolling-horizon V2 screen
=== ROLLING-HORIZON V2 SCREEN ===
Saved: artifacts/rolling_horizon_v2_quick
```

Do **not** run `--full` until the V2 quick result is inspected.

## V2 decision gate

### V2 no longer harmful / positive signal

Run the full `15000–15399` screen. Planner-aware rule training is considered only if the full screen then shows a useful effect or compelling secondary-metric tradeoff.

### V2 remains materially worse

Stop this rolling-horizon formulation. Keep one-step `RuleGuidedHungarianPolicy` as the incumbent executor and move to another bottleneck rather than building a planner V3 by default.

### V2 roughly ties

Use per-program deltas, penetrations, damage, resources and runtime to decide whether one planner-aware training attempt is justified. A tie alone does not earn a training campaign.

## Evidence ledger

Consumed:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development;
- `13000–13399`: rolling-horizon planner V1 development.

Untouched older reserved blocks tied to abandoned/unfrozen protocols:

- `6000–6399`;
- `7000–7399`;
- `8000–8399`;
- `10000–10399`;
- `12000–12399`;
- `14000–14399`.

Active planner V2:

- `15000–15399`: development;
- `16000–16399`: reserved confirmation.

## Claims policy

Supported development-level conclusions:

- optimizer-aware searched rule strategies substantially improve the current fixed hand-written myopic optimizer baseline in this synthetic simulator;
- Axplorer did not materially outperform local/evolutionary search under the matched hybrid-objective protocol;
- optimizer-native V2 was 11.2 percentage points worse than the 60-token rule representation on fresh development data;
- the 60-token rule representation is the strongest strategic representation tested so far;
- rolling-horizon planner V1 did not improve the incumbent frozen rule strategies and had a -3.0 pp point estimate with materially higher runtime;
- V1 exposed a concrete receding-horizon action-deferral flaw now being tested in corrected planner V2 on fresh development data.

Not supported:

- that rolling-horizon planning is superior;
- that the planning horizon is definitively the bottleneck;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world effectiveness or deployment readiness.

## External target

The project is still working backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-check the official source before submission work.
