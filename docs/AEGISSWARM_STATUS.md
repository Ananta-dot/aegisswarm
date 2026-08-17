# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/optimizer-native-objective`  
**Active protocol:** `aegisswarm-optimizer-native-objective-v1`

This is the current-state overlay for `docs/AEGISSWARM_SKILL.md`. Read the skill for full history, then this file for the latest experiment and decision.

## Most recent completed development result

Hybrid-objective protocol `aegisswarm-hybrid-objective-v1`, evaluated on consumed development seeds `5000–5399`:

```text
fixed_optimizer survival: 0.320
hybrid_local survival:    0.805 CI=[0.77624375, 0.83100625]
hybrid_axplorer survival: 0.810 CI=[0.77775, 0.841]
Axplorer - local:         +0.0055 CI=[-0.0235, +0.0320]
paired p-value:           0.507075
```

Decision from that experiment:

- optimizer-aware objective search is highly valuable relative to the current fixed hand-written objective in this synthetic simulator;
- Axplorer V2 does **not** demonstrate a material advantage over optimizer-aware local/evolutionary search;
- **NO FREEZE; NO CONFIRMATION** for the hybrid-objective architecture;
- keep `8000–8399` untouched;
- use optimizer-aware local/evolutionary search as the default offline search engine for the next architecture stage.

## Current bottleneck hypothesis

Several serious variants have repeatedly landed around roughly 80–81% survival on their respective development/formal blocks. Those percentages are not directly comparable across different blocks, but the repeated plateau is a strong development signal.

The project should therefore stop treating proposer choice as the primary bottleneck.

Current hypothesis:

> **The strategic representation and/or the myopic one-step assignment layer is limiting performance more than the choice between local search and Axplorer.**

## Active experiment — optimizer-native objective representation

Branch: `agent/optimizer-native-objective`  
Protocol: `aegisswarm-optimizer-native-objective-v1`

The experiment holds the following fixed:

- simulator;
- scalar fitness;
- per-step Hungarian executor;
- local/evolutionary search family;
- five matched search seeds in full development;
- 16 training scenarios;
- 1,800 unique candidate evaluations per representation/run.

It changes only the strategic representation searched by the optimizer-aware learner.

Comparison:

```text
fixed hand-written objective + optimizer
60-token searched rule objective + optimizer
10-parameter searched optimizer-native objective + optimizer
```

The 60-token representation is retrained from scratch under the same search seeds and budget; old artifacts are not used for the primary representation comparison.

### Optimizer-native vector

The compact representation controls abstract preferences for:

- urgency;
- protected-asset value;
- abstract threat class;
- defender/threat distance;
- resource scarcity;
- reserve threshold;
- assignment persistence;
- abstract speed.

The optimizer remains responsible for feasible one-to-one assignment and no-op choices.

This is synthetic decision research, not real-world platform or engagement parameterization.

## Active seed ledger

Consumed development/evidence blocks remain consumed:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: V2 development;
- `4000–4399`: hybrid executor development;
- `5000–5399`: hybrid-objective development.

Keep untouched unless the exact older architecture is deliberately revived/frozen:

- `6000–6399`: V2 confirmation;
- `7000–7399`: hybrid-executor confirmation;
- `8000–8399`: hybrid-objective confirmation.

Current experiment:

- `9000–9399`: **optimizer-native development**;
- `10000–10399`: **reserved optimizer-native confirmation**.

Do not consume `10000–10399` automatically after development. Confirmation is code-gated by an explicit `architecture_frozen` flag.

## Decision tree for the active experiment

### If optimizer-native representation clearly beats 60-token rules

A meaningful target is several percentage points with stable per-run behavior and a paired hierarchical interval supporting a genuine improvement.

Then:

1. inspect secondary metrics and runtime;
2. decide whether the representation/hyperparameters are genuinely frozen;
3. only then enable and run `10000–10399` once;
4. do not tune on the confirmation result.

### If optimizer-native and 60-token objectives remain tied near the plateau

Do not tune Axplorer again.

Treat the result as evidence that the next bottleneck is the **myopic planning horizon**. The next architecture protocol should test a short rolling-horizon/MPC-style abstract planner while keeping the strongest objective representation fixed.

### If optimizer-native representation is worse

Keep the stronger 60-token representation. Negative results are useful. The end goal is the best hybrid system, not validating a preferred representation.

## Immediate runbook

Quick integration check:

```bash
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

If quick completes, full development:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do not run `--confirm` until we interpret the full development result.

## Current claims policy

Supported development-level conclusion from the completed hybrid-objective experiment:

> In the current synthetic simulator, searching the strategic objective used by the per-step Hungarian assignment layer yields substantially better asset survival than the current fixed hand-written objective. Under equal candidate-evaluation budgets, Axplorer V2 and conventional local/evolutionary search produced statistically indistinguishable optimizer-aware strategies on the 400-scenario development block.

Not supported:

- Axplorer superiority;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world counter-swarm effectiveness;
- deployment readiness.

## External target

The project continues to work backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-verify the official source before submission work.
