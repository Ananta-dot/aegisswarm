# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form history/methodology.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay; this supersedes older current-status wording.
3. [`ROLLING_HORIZON.md`](ROLLING_HORIZON.md) — completed planner V1/V2 screening history.

## Non-negotiable rules

1. Never consume reserved confirmation seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside an evidence protocol.
4. Compare components by ablation, not ideology.
5. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
6. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
7. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
8. Keep the handoff/status docs current after major experiments.
9. Do not run a reserved confirmation merely because a development result is positive.
10. Old simulator-version results must remain labeled if a new stochastic/evaluation model is introduced.

## Current incumbent architecture

Use this as the incumbent unless a new controlled experiment demonstrates otherwise:

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy execution
```

Why:

- hybrid-objective development: optimizer-aware local `0.805`, Axplorer `0.810`, Axplorer-local `+0.0055`, CI `[-0.0235,+0.0320]`;
- optimizer-native V2: rules `0.813` vs native `0.701`, native-rule `-0.1120`, CI `[-0.1405,-0.08249]`;
- rolling-horizon V2: one-step `0.808` vs rolling `0.801`, rolling-one-step `-0.0065`, CI `[-0.0325,+0.01825]`, roughly 14x slower.

## Closed tracks

### Optimizer-native representation

Closed. No V3 vector. Do not consume `12000–12399` confirmation.

### Rolling-horizon planner V1/V2

V1 was worse and exposed a receding-horizon procrastination defect. V2 corrected the defect, but the full fresh development screen still produced no useful gain:

```text
fixed_optimizer:   0.329
rule_one_step:     0.808
rule_rolling_v2:   0.801
rolling - one:    -0.0065 CI=[-0.0325,+0.01825]
per-program deltas [-0.025,-0.03625,+0.0225,-0.0075,+0.01375]
scenario p=0.333083
runtime 0.0128s -> 0.1774s/scenario
```

Do not run planner-aware 1,800-candidate training. Do not create planner V3 by default. Do not consume `16000–16399` confirmation.

## Current research direction — evidence hardening and headroom

The repeated low-80% plateau has survived proposer, representation and executor changes. Before another algorithmic branch, determine whether the simulator itself leaves meaningful headroom and make paired comparisons statistically cleaner.

Priority sequence:

1. Build a new simulator/evaluation version with policy-independent indexed random draws for detection, motion noise and abstract interaction outcomes.
2. Keep the incumbent architecture fixed initially and reproduce baseline/incumbent behavior under the new stochastic coupling.
3. Run clearly labeled headroom diagnostics such as perfect sensing, deterministic interaction success, their combination as a loose upper envelope, and best-of-incumbent-programs per scenario under a fixed random tape.
4. Align primary statistics to both independent training/search-run uncertainty and scenario uncertainty; report per-run effects explicitly.
5. Only after measuring headroom choose the next algorithmic investment: sensing/uncertainty, robustness/generalization, sequential adaptation, or richer scenario families.

The next simulator/evidence protocol must use fresh development and reserved evidence blocks. Do not silently repurpose old reserved confirmations.
