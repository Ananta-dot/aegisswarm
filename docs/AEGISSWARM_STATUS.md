# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Active branch:** `agent/optimizer-native-objective`  
**Active protocol:** `aegisswarm-optimizer-native-objective-v2`

This is the current-state overlay for `docs/AEGISSWARM_SKILL.md`. Read the skill for full history, then this file for the latest experiment and decision.

## Most recent completed full development result

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

Current hypothesis:

> **The strategic representation and/or the myopic one-step assignment layer is limiting performance more than proposer choice.**

## Optimizer-native V1 quick — INVALIDATED BEFORE FULL DEVELOPMENT

The first compact optimizer-native representation was tested only in quick mode on 20 development scenarios. It produced:

```text
fixed_optimizer survival: 0.350
rule_objective survival:  0.688 CI=[0.400, 0.925]
native_objective survival:0.300 CI=[0.175, 0.425]
native - rule:            -0.3875 CI=[-0.650, -0.075]
paired p-value:            0.000100
```

This result is **not formal evidence**. It exposed a design defect before the expensive development campaign:

- the native utility was zero-centred while the rule-guided policy always inherited a positive structural base utility;
- many native candidates therefore learned/produced no-op assignments rather than competing on strategic ranking quality;
- the compact vector also discarded important state-reactive information already available to the rule representation, notably target damage state and thresholded reserve/release behavior.

Therefore **do not run the V1 full campaign** and do not interpret the -38.75 pp quick gap as evidence that optimizer-native objectives are intrinsically inferior.

The V1 quick result consumed only part of the already-designated development block and legitimately informed architecture iteration. The development block remains development data.

## Active experiment — optimizer-native objective V2

Protocol: `aegisswarm-optimizer-native-objective-v2`

V2 keeps the clean representation ablation but fixes the malformed parameterization.

Both searched representations are still trained under:

- the same simulator;
- the same scalar fitness;
- the same per-step Hungarian executor;
- the same local/evolutionary search family;
- five matched search seeds in full development;
- 16 fixed training scenarios;
- 1,800 unique candidate evaluations per representation/run.

Comparison:

```text
fixed hand-written objective + optimizer
60-token searched state-reactive rule objective + optimizer
14-parameter searched optimizer-native V2 objective + optimizer
```

### What V2 changes

The native policy now uses the **same structural base utility** as `RuleGuidedHungarianPolicy`:

```text
2 * threat-type prior
+ inverse asset distance term
+ inverse defender distance term
```

Search then learns smooth modifiers for:

- urgency;
- protected-asset value;
- abstract threat class;
- defender/threat closeness;
- defender capacity;
- resource scarcity;
- reserve threshold;
- urgency threshold that releases reserve;
- assignment persistence;
- speed;
- target-asset damage state;
- urgency × scarcity interaction.

The optimizer remains responsible for feasible one-to-one assignment and explicit no-op choices.

V2 does **not** receive a hand-written warm start. The 60-token comparator and V2 native representation both start from stochastic candidates.

V2 also writes to new artifact directories (`optimizer_native_v2_*`) so malformed V1 quick artifacts cannot be resumed accidentally.

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

Current representation experiment:

- `9000–9399`: **optimizer-native development**; first 20 seeds were already inspected in the invalidated V1 quick run, so this entire block is development-only;
- `10000–10399`: **reserved optimizer-native confirmation**, still untouched.

Do not consume `10000–10399` automatically. Confirmation is code-gated by an explicit `architecture_frozen` flag.

## Decision tree

### If V2 native clearly beats 60-token rules

Inspect secondary metrics and run stability. If the effect is several percentage points and robust, freeze the representation before confirmation.

### If V2 native and 60-token rules tie near ~80–81%

Stop representation tuning. The next protocol should target the **myopic planning horizon**, using the stronger/simpler representation with a short rolling-horizon/MPC-style abstract planner.

### If V2 native remains materially worse

Keep the 60-token representation and move to planning. Do not keep expanding the vector merely to force a win.

## Immediate runbook

Because V2 uses new artifact paths, no deletion of V1 quick artifacts is required.

```bash
git pull origin agent/optimizer-native-objective
pytest -q
python -m aegisswarm.optimizer_native_cli --quick --workers 4
```

If V2 quick is no longer pathologically worse, then run full development:

```bash
python -m aegisswarm.optimizer_native_cli --workers 6
```

Do not run `--confirm` until the full development result is interpreted and an explicit freeze decision is recorded.

## Claims policy

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
