# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/rolling-horizon-planning`  
**Active protocol:** `aegisswarm-rolling-horizon-screen-v1`

Read `docs/AEGISSWARM_SKILL.md` for full history. This file is the latest-state overlay.

## Latest completed architecture result — optimizer-native V2

Fresh development seeds `11000–11399`:

```text
fixed_optimizer survival:      0.320
rule_objective survival:       0.813 CI=[0.78149375, 0.841]
native_objective_v2 survival:  0.701 CI=[0.66275, 0.7355]
native - rule:                -0.1120 CI=[-0.1405, -0.08249375]
paired p-value:                0.000050
```

Decision:

- optimizer-native V2 is materially worse than the incumbent 60-token state-reactive rule representation;
- close the optimizer-native representation track;
- no V3 vector;
- do not consume `12000–12399` confirmation;
- retain the 60-token rules as the strategic representation incumbent.

The result also reinforces the earlier conclusions that Axplorer is not currently the important bottleneck and that optimizer-aware local/evolutionary search is a strong default offline learner.

## Active hypothesis — planning horizon

The next question is:

> **Holding the strong 60-token strategy fixed, can short receding-horizon planning outperform the same strategy executed by one-step Hungarian matching?**

The project is now testing temporal allocation/planning, not proposer choice or another representation.

## Active screening experiment

Implementation:

- `aegisswarm/rolling_horizon.py`
- `aegisswarm/rolling_horizon_ablation.py`
- `aegisswarm/rolling_horizon_cli.py`
- `ROLLING_HORIZON.md`

The planner reuses the existing `RuleGuidedHungarianPolicy` pair utility and adds a short time-indexed binary allocation over projected synthetic timesteps. Only the first planned action is executed; the planner re-solves after each new observation.

This first stage holds five already-trained strong rule programs fixed. It is only a **screening ablation** to decide whether planner-aware retraining is worth the cost.

Comparison:

```text
fixed hand-written one-step optimizer
same frozen rule programs + one-step Hungarian
same frozen rule programs + rolling-horizon planning
```

Default screen settings:

- horizon: 4 synthetic timesteps;
- discount: 0.90;
- per-solve time limit: 0.25 s;
- source strategies: `artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44001..44005.json`.

### Quick screen — PASSED AS A DEVELOPMENT GATE

Quick screen on planning-development seeds `13000–13019`:

```text
fixed_optimizer survival: 0.300
rule_one_step survival:   0.820 CI=[0.700, 0.910]
rule_rolling survival:    0.830 CI=[0.730, 0.915]
rolling - one_step:       +0.0100 CI=[-0.090, +0.100125]
paired p-value:           0.883656
runtime one-step/rolling: 0.0130 s / 0.1866 s
```

Interpretation:

1. This is a 20-scenario integration/development screen, not evidence of superiority.
2. The rolling-horizon planner is **not pathologically worse** than one-step execution and has a small positive survival point estimate (+1 pp).
3. The interval is far too wide and p-value far too large to infer a performance advantage.
4. Rolling-horizon execution is substantially slower than one-step execution, but absolute runtime remains sub-second in this synthetic screen, so runtime does not yet kill the hypothesis.
5. The planning hypothesis therefore **passes the quick gate** and justifies the full 400-scenario development screen before any planner-aware retraining.

## Fresh planning evidence

- `13000–13399`: planning development; first 20 seeds are now inspected development data;
- `14000–14399`: reserved planning confirmation — **do not inspect**.

## Immediate runbook

The next command is the full fixed-policy planning screen:

```bash
python -m aegisswarm.rolling_horizon_cli --full --workers 5
```

This is still a screening ablation with frozen existing rule programs. It does **not** retrain strategies through the planner.

After the 400-scenario result:

- if rolling horizon produces a meaningful positive effect without unacceptable runtime/resource tradeoffs, build a new **planner-aware rule-training protocol** using fresh development/confirmation blocks and matched candidate-evaluation budgets;
- if it is essentially tied, inspect penetrations, damage, resource consumption and runtime before deciding whether planner-aware training is worth one formal attempt;
- if it is materially worse, diagnose the planning formulation once and then prefer the one-step executor rather than blindly increasing horizon/complexity.

Do not consume `14000–14399` during this screening stage.

## Evidence ledger

Consumed:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development;
- `13000–13019`: rolling-horizon quick development subset.

Untouched older reserved blocks, each tied to an older unfrozen/abandoned protocol:

- `6000–6399`;
- `7000–7399`;
- `8000–8399`;
- `10000–10399`;
- `12000–12399`.

Active planning:

- `13000–13399`: development;
- `14000–14399`: reserved confirmation.

## Claims policy

Supported development-level claims:

- optimizer-aware searched rule strategies strongly outperform the current fixed hand-written myopic objective in this synthetic simulator;
- Axplorer did not materially outperform local/evolutionary search under the matched hybrid-objective protocol;
- optimizer-native V2 was 11.2 percentage points worse than the 60-token rule representation on fresh development data;
- the 60-token rule representation is the strongest strategic representation tested so far;
- a 20-scenario rolling-horizon quick screen completed successfully with survival in the same regime as one-step rule-guided execution, justifying a larger development screen.

Not yet supported:

- that rolling-horizon planning is better;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world effectiveness or deployment readiness.

## External target

The project is still working backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-check the official source before submission work.
