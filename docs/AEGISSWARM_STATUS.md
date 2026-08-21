# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** NOT FROZEN FOR EXTERNAL CLAIMS; CURRENT INCUMBENT SELECTED FOR EVIDENCE HARDENING  
**Active branch:** `agent/rolling-horizon-planning`  
**Completed protocol:** `aegisswarm-rolling-horizon-screen-v2`  
**Current decision:** STOP EXECUTOR/REPRESENTATION ITERATION; HARDEN EVIDENCE AND MEASURE HEADROOM

Read `docs/AEGISSWARM_SKILL.md` for full history. This file is the latest-state overlay and supersedes older current-status wording.

## Incumbent architecture

The strongest architecture currently justified by development evidence is:

```text
60-token state-reactive rule representation
        +
optimizer-aware local/evolutionary offline search
        +
one-step RuleGuidedHungarianPolicy executor
```

Axplorer remains an optional proposer but did not materially outperform local/evolutionary search. The compact optimizer-native representation was materially worse. Two rolling-horizon executor formulations did not improve the incumbent on full development screens.

## Optimizer-native V2 — representation track closed

Fresh development seeds `11000–11399`:

```text
fixed_optimizer survival:      0.320
rule_objective survival:       0.813 CI=[0.78149375, 0.841]
native_objective_v2 survival:  0.701 CI=[0.66275, 0.7355]
native - rule:                -0.1120 CI=[-0.1405, -0.08249375]
paired p-value:                0.000050
```

Decision: keep the 60-token rules; no optimizer-native V3; do not consume `12000–12399` confirmation.

## Rolling-horizon planner V1 — rejected

Full fixed-program development screen on consumed seeds `13000–13399`:

```text
fixed_optimizer survival: 0.310
rule_one_step survival:   0.782 CI=[0.739, 0.81775]
rule_rolling_v1 survival: 0.752 CI=[0.7125, 0.7900]
rolling - one_step:      -0.0300 CI=[-0.07775, +0.01825625]
scenario sign-flip p:     0.000700
runtime one-step/rolling: 0.0125 s / 0.1837 s
```

Inspection found a concrete receding-horizon procrastination defect: projected future urgency could make an already-feasible action more valuable later, encouraging repeated deferral.

## Rolling-horizon planner V2 — full screen completed, planning track closed

V2 fixed only the diagnosed deferral incentive by capping the future strategic value of an already-feasible pair at its current value before discounting. It was evaluated on fresh development seeds `15000–15399`.

Full result:

```text
fixed_optimizer survival: 0.329
rule_one_step survival:   0.808 CI=[0.776, 0.83575]
rule_rolling_v2 survival: 0.801 CI=[0.76174375, 0.837]
rolling - one_step:      -0.0065 CI=[-0.0325, +0.01825]
per-program deltas:       [-0.025, -0.03625, +0.0225, -0.0075, +0.01375]
scenario sign-flip p:     0.333083
runtime one-step/rolling: 0.0128 s / 0.1774 s
```

### Interpretation

1. Corrected rolling-horizon execution is statistically consistent with a small loss/tie, not a useful positive gain.
2. The point estimate is `-0.65` percentage points and the primary hierarchical interval crosses zero.
3. Program-level effects are mixed: three of five incumbent programs became worse and two became better.
4. Rolling-horizon execution is roughly 14x slower per scenario than the incumbent one-step executor.
5. This does **not** justify planner-aware 1,800-candidate training.
6. Do not build planner V3 by default and do not consume `16000–16399` confirmation.
7. Retain one-step `RuleGuidedHungarianPolicy` as the executor incumbent.

## What the repeated ~80–81% plateau means now

The project has tested proposer choice, strategic representation, executor swapping, optimizer-aware objective training, and two rolling-horizon formulations. Strong variants repeatedly remain around the low-80% survival region on their respective development blocks.

It is now inefficient to keep assuming another architecture tweak will break the plateau.

The next question should be:

> **How much achievable headroom actually exists in the current simulator, and how robust is the incumbent advantage when exogenous randomness is coupled consistently across policies?**

## Next protocol — evidence hardening / headroom measurement

Do not change the incumbent policy architecture initially.

### 1. Policy-independent stochastic evaluation

Build a simulator/evaluation V2 with indexed random draws so shared exogenous events are independent of policy call order. At minimum, random draws should be reproducibly indexed by scenario seed plus event identity for:

- detection events;
- threat motion noise;
- abstract interaction outcomes.

The goal is stronger common-random-number coupling for paired comparisons, not to make the simulator easier or harder.

This is a new simulator/evidence version. Old results remain valid for their old simulator version but should not be mixed numerically with V2 evidence without labeling the environment change.

### 2. Measure environment headroom

Before inventing another learner, quantify where survival is lost using clearly labeled relaxation diagnostics, for example:

- incumbent under ordinary sensing/stochastic interaction;
- perfect-sensing diagnostic;
- deterministic-interaction-success diagnostic;
- perfect-sensing + deterministic-success loose upper-envelope diagnostic;
- best-of-incumbent-programs per scenario under a fixed random tape as a policy-class headroom diagnostic.

These are diagnostics/upper envelopes, not deployable policies and not claims of operational performance.

### 3. Align statistical estimands

Primary architecture claims should report:

- mean effect;
- hierarchical interval across independent training/search runs and scenarios;
- per-training-run effects;
- scenario-conditional effects separately when useful;
- runtime and secondary metrics.

With only five independently trained programs, training-run uncertainty is a real limitation. For a final evidence package, consider increasing independent training seeds rather than treating thousands of scenarios as thousands of independent learned policies.

### 4. Only then choose the next algorithmic investment

If the headroom diagnostic is large, target the identified source of loss (e.g. sensing/uncertainty, robustness/generalization, sequential adaptation). If headroom is small, stop optimizing the same simulator and shift effort to richer scenario families, robustness, tail risk, scaling, and stronger external baselines.

## Seed/evidence ledger

Consumed development/evidence blocks include:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development;
- `13000–13399`: rolling-horizon planner V1 development;
- `15000–15399`: rolling-horizon planner V2 development.

Untouched reserved blocks tied to older unfrozen/abandoned protocols must not be silently repurposed as confirmation:

- `6000–6399`;
- `7000–7399`;
- `8000–8399`;
- `10000–10399`;
- `12000–12399`;
- `14000–14399`;
- `16000–16399` — planner V2 confirmation; **do not run**.

A new simulator/evidence-hardening protocol should receive fresh development and reserved evidence blocks.

## Supported development-level conclusions

- optimizer-aware searched 60-token rule strategies substantially outperform the current fixed hand-written myopic objective in this synthetic simulator;
- Axplorer did not materially outperform conventional local/evolutionary search under the matched hybrid-objective protocol;
- optimizer-native V2 was 11.2 percentage points worse than the 60-token rule representation on fresh development data;
- rolling-horizon V1 was worse and exposed a concrete action-deferral flaw;
- corrected rolling-horizon V2 was effectively tied/slightly worse than one-step execution and about 14x slower, so planner-aware retraining is not justified;
- the 60-token state-reactive rules + optimizer-aware local search + one-step Hungarian executor remain the incumbent architecture.

Not supported:

- that ~81% is the true attainable simulator ceiling;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world counter-swarm effectiveness;
- deployment readiness.

## External target

The project is still working backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-check the official source before submission work.
