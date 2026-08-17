# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/rolling-horizon-planning`  
**Active protocol:** `aegisswarm-rolling-horizon-screen-v1`

Read `docs/AEGISSWARM_SKILL.md` for full history. This file is the latest-state overlay.

## Latest completed experiment — optimizer-native V2

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

## Fresh planning evidence

- `13000–13399`: planning development;
- `14000–14399`: reserved planning confirmation — **do not inspect**.

Quick screen uses `13000–13019`; those seeds are development data as soon as inspected.

## Immediate runbook

```bash
git checkout agent/rolling-horizon-planning
git pull origin agent/rolling-horizon-planning
pytest -q
python -m aegisswarm.rolling_horizon_cli --workers 5
```

Do not run `--full` yet. First inspect quick survival, paired difference, and runtime.

If the screen is promising, the next formal architecture stage is **planner-aware rule training**: retrain the same 60-token representation through the rolling-horizon executor under matched search seeds and candidate-evaluation budgets, using planning development data only.

## Evidence ledger

Consumed:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development.

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
- the 60-token rule representation is the strongest strategic representation tested so far.

Not yet supported:

- that rolling-horizon planning is better;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world effectiveness or deployment readiness.

## External target

The project is still working backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-check the official source before submission work.
