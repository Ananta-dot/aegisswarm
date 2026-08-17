# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN  
**Current completed protocol:** `aegisswarm-optimizer-native-objective-v2`  
**Current decision:** CLOSE REPRESENTATION TRACK; MOVE TO ROLLING-HORIZON PLANNING

This is the current-state overlay for `docs/AEGISSWARM_SKILL.md`. Read the long-form skill for project history and this file for the latest experiment/decision.

## Strong incumbent before the representation experiment

The completed optimizer-aware hybrid-objective development protocol on seeds `5000–5399` produced:

```text
fixed_optimizer survival: 0.320
hybrid_local survival:    0.805
hybrid_axplorer survival:  0.810
Axplorer - local:         +0.0055 CI=[-0.0235, +0.0320], p=0.507075
```

Interpretation: searching a strategic objective for the optimizer is valuable, but Axplorer did not add a material advantage over local/evolutionary search. The 60-token state-reactive rule representation plus optimizer-aware local/evolutionary search became the incumbent architecture for further ablation.

## Optimizer-native V1 — rejected

V1 was a 10-parameter continuous objective. Full development on consumed seeds `9000–9399` produced:

```text
fixed_optimizer survival: 0.310
rule_objective survival:  0.787 CI=[0.75449375, 0.81675]
native_v1 survival:       0.359 CI=[0.30475, 0.43125625]
native - rule:           -0.4280 CI=[-0.4845, -0.3590]
paired p-value:            0.000050
```

V1 also showed severe train/development generalization failure and had a semantic design defect: its zero-centred utility could reject reachable assignments that the rule-guided comparator gave positive structural utility. V1 is permanently rejected and `9000–9399` is consumed development data.

## Optimizer-native V2 — full development completed, representation hypothesis rejected

V2 corrected the semantic defect, inherited the same structural base utility as `RuleGuidedHungarianPolicy`, and searched 14 smooth state modifiers. It used fresh development seeds `11000–11399`.

Full development result:

```text
fixed_optimizer survival:      0.320
rule_objective survival:       0.813 CI=[0.78149375, 0.841]
native_objective_v2 survival:  0.701 CI=[0.66275, 0.7355]
native - rule:                -0.1120 CI=[-0.1405, -0.08249375]
paired p-value:                0.000050
```

### Interpretation

1. The semantically corrected continuous optimizer-native representation is **materially worse** than the existing 60-token state-reactive rule representation under the matched protocol.
2. The effect is large: **-11.2 percentage points** asset survival, with the entire paired hierarchical 95% interval below zero.
3. This is not a reason for a V3 vector. The representation track has now received a fair corrected test and lost decisively.
4. Keep the 60-token rule representation as the incumbent strategic representation.
5. Do **not** run optimizer-native V2 confirmation on `12000–12399`; the candidate architecture did not earn a freeze.
6. Do not repurpose older reserved confirmation blocks as fresh development evidence.

## Current architectural conclusion

The project has now tested multiple proposer and representation variants while strong rule-based optimizer-aware systems repeatedly remain around the low-80% survival region on their respective development/formal blocks.

The evidence now points more strongly to the **one-step/myopic planning horizon** as the next bottleneck.

The next research question is:

> **Holding the winning 60-token state-reactive rule objective fixed, can a short rolling-horizon planner that allocates scarce resources across several future abstract timesteps outperform the same rule objective executed by per-step Hungarian matching?**

This is a planning ablation, not another representation or proposer experiment.

## Incumbent components for the next protocol

Keep fixed initially:

- synthetic simulator semantics;
- scalar fitness;
- 12-rule / 60-token strategic representation;
- optimizer-aware local/evolutionary search as the offline strategy learner;
- same scenario generation and metrics;
- same abstract defensive/simulation-only scope.

Change only:

- executor/planning horizon: one-step Hungarian assignment -> short rolling-horizon time-indexed planner.

The first planning experiment should compare:

```text
fixed one-step Hungarian baseline
searched 60-token rules + one-step Hungarian
searched 60-token rules + rolling-horizon planner
```

For the primary causal comparison, retrain the same 60-token representation through each executor under matched search seeds/budgets rather than swapping an executor under an old policy artifact.

## Planning implementation direction

Prefer a small time-indexed optimization problem rather than another scoring heuristic. With current dependencies (`scipy>=1.11`), a short-horizon MILP/linear optimization formulation is available without adding a new solver dependency.

At an abstract level, the planner may optimize assignments across a horizon such as 3–5 synthetic timesteps with constraints on:

- at most one assignment per defender per planning step;
- at most one planned assignment per threat per step;
- cumulative defender-use/resource limits;
- predicted reachability from current synthetic state;
- no-op options;
- reserve/resource opportunity cost.

Only the first-step assignment is executed; the problem is re-solved after the next observation, i.e. receding-horizon/MPC-style control.

Keep prediction and utility abstract. Do not add real platform guidance, interceptor physics, or engagement engineering.

## Seed/evidence ledger

Consumed development/evidence blocks:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development.

Untouched reserved blocks that belong to older abandoned/unfrozen protocols:

- `6000–6399`: Axplorer V2 confirmation;
- `7000–7399`: executor-swap confirmation;
- `8000–8399`: hybrid-objective confirmation;
- `10000–10399`: old native-V1 confirmation;
- `12000–12399`: native-V2 confirmation — **do not run**.

The new rolling-horizon protocol must receive a **fresh development block and a fresh reserved confirmation block**.

## Claims policy

Supported development-level conclusions:

- optimizer-aware search of a strategic objective substantially improves the current fixed hand-written myopic optimizer baseline in this synthetic simulator;
- Axplorer and conventional local/evolutionary search were statistically indistinguishable under the matched hybrid-objective protocol;
- optimizer-native V1 failed badly and had a representation defect;
- the corrected optimizer-native V2 representation was still materially worse than the 60-token rule representation by 11.2 percentage points on its fresh 400-scenario development block;
- the 60-token state-reactive rule representation remains the strongest strategic representation tested so far.

Not supported:

- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world counter-swarm effectiveness;
- deployment readiness;
- a claim that the planning horizon is already proven to be the bottleneck; it is the next hypothesis to test.

## Immediate decision

**NO OPTIMIZER-NATIVE CONFIRMATION. NO V3 VECTOR.**

Start a new rolling-horizon planning protocol with the 60-token rules as incumbent and fresh evidence blocks.

## External target

The project continues to work backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-verify the official source before submission work.
