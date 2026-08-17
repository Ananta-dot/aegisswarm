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

Decision: retain the 60-token state-reactive rule representation; no native V3; do not consume `12000–12399` confirmation.

## Rolling-horizon planner V1 — completed and rejected

V1 held five trained rule programs fixed and changed only execution to a horizon-4 receding-horizon MILP.

Full development on consumed seeds `13000–13399`:

```text
fixed_optimizer survival: 0.310
rule_one_step survival:   0.782 CI=[0.739, 0.81775]
rule_rolling_v1 survival: 0.752 CI=[0.7125, 0.7900]
rolling - one_step:      -0.0300 CI=[-0.07775, +0.01825625]
scenario sign-flip p:     0.000700
runtime one-step/rolling: 0.0125 s / 0.1837 s
```

V1 did not earn planner-aware retraining. Inspection found a receding-horizon procrastination defect: projected future states could make an already-feasible threat more valuable later, encouraging the planner to schedule action at `h>0`, execute nothing now, then defer again after replanning.

## Planner V2 — targeted correction

V2 changes one semantic only:

- projection still determines future reachability and predicted target arrival;
- if a defender/threat pair is already positive and feasible now, its future strategic value is capped at its current value;
- temporal discounting is then applied;
- future-only reachable pairs can still enter the horizon normally.

This removes the diagnosed incentive to wait merely because urgency grows.

## Planner V2 quick screen — PASSED DEVELOPMENT GATE

Fresh quick-development subset `15000–15019`, five frozen incumbent rule programs, horizon 4:

```text
fixed_optimizer survival: 0.250
rule_one_step survival:   0.805 CI=[0.715, 0.890]
rule_rolling_v2 survival: 0.840 CI=[0.740, 0.920125]
rolling - one_step:      +0.0350 CI=[-0.025, +0.105]
per-program deltas:       [0.000, 0.000, +0.100, +0.050, +0.025]
scenario sign-flip p:     0.149193
runtime one-step/rolling: 0.0130 s / 0.1846 s
```

### Interpretation

1. This 20-scenario result is a development screen, not superiority evidence.
2. V2 has removed the pathological negative behavior seen in planner V1.
3. The point estimate is +3.5 percentage points, but the hierarchical 95% interval still crosses zero substantially.
4. Per-program effects are non-negative across all five frozen strategies: two ties and three positive effects. That is encouraging for an executor-level screen because the gain is not produced by one strategy being rescued while others degrade.
5. Runtime remains about 14–15x one-step execution, but absolute mean runtime remains below 0.2 s/scenario in the current synthetic setup.
6. Planner V2 therefore **passes the quick development gate** and warrants the full fresh `15000–15399` screen.

## Active next experiment

Run the full fixed-program Planner V2 screen on all development seeds `15000–15399`.

```bash
python -m aegisswarm.rolling_horizon_cli --full --workers 14
```

This still does **not** retrain rules through the planner.

The full-screen decision must use:

- rolling minus one-step mean survival;
- hierarchical 95% CI as the primary architecture-level uncertainty summary;
- five per-program survival deltas;
- penetrations, damage, resource consumption and response delay where available;
- runtime.

### Decision gate after full V2 screen

**Useful positive effect:** if the full screen shows a meaningful gain with broadly non-negative per-program behavior and acceptable secondary/runtime tradeoffs, build exactly one planner-aware rule-training protocol under a matched simulator-evaluation budget.

**Tie:** inspect secondary metrics and per-program effects. A tie alone does not automatically justify training.

**Materially worse:** stop this rolling-horizon formulation. Keep one-step `RuleGuidedHungarianPolicy`; do not create planner V3 by default.

## Evidence ledger

Consumed development/evidence:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development;
- `13000–13399`: rolling-horizon planner V1 development;
- `15000–15019`: inspected planner V2 quick subset (part of V2 development).

Untouched reserved blocks tied to older abandoned/unfrozen protocols:

- `6000–6399`;
- `7000–7399`;
- `8000–8399`;
- `10000–10399`;
- `12000–12399`;
- `14000–14399`.

Active Planner V2:

- `15000–15399`: development;
- `16000–16399`: reserved confirmation — **do not inspect**.

## Claims policy

Supported development-level conclusions:

- optimizer-aware searched rule strategies substantially improve the current fixed hand-written myopic optimizer baseline in this synthetic simulator;
- Axplorer did not materially outperform local/evolutionary search under the matched hybrid-objective protocol;
- optimizer-native V2 was 11.2 percentage points worse than the 60-token rule representation on fresh development data;
- the 60-token rule representation remains the strategic incumbent;
- rolling-horizon planner V1 did not improve the incumbent frozen strategies and exposed a concrete action-deferral defect;
- corrected planner V2 passed a 20-scenario development gate with a +3.5 pp point estimate and non-negative effects across all five frozen strategies, but its CI crosses zero and it is not yet evidence of superiority.

Not supported:

- that rolling-horizon planning is superior;
- that the planning horizon is definitively the bottleneck;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world effectiveness or deployment readiness.

## External target

The project is still working backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-check the official source before submission work.
