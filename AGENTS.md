# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form history/methodology.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay.
3. [`ROLLING_HORIZON.md`](ROLLING_HORIZON.md) — active planning-screen protocol.

## Non-negotiable rules

1. Architecture is not final.
2. Never consume reserved confirmation seeds for development.
3. Once inspected, a block is never untouched again.
4. Do not silently change simulator/scoring/budgets inside a formal protocol.
5. Compare components by ablation, not ideology.
6. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
7. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
8. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
9. Keep the handoff/status docs current after major experiments.
10. Do not run a reserved confirmation merely because a development result is positive.

## Strong current conclusion

The optimizer-native representation track is closed.

Optimizer-native V2 full development on fresh seeds `11000–11399`:

```text
fixed_optimizer:       0.320
rule_objective:        0.813
native_objective_v2:   0.701
native - rule:        -0.1120, CI [-0.1405, -0.08249], p=0.000050
```

Keep the 60-token state-reactive rule representation. Do not build V3 native vectors and do not consume `12000–12399` confirmation.

## Active track — rolling-horizon planning

Branch: `agent/rolling-horizon-planning`  
Active screening protocol: `aegisswarm-rolling-horizon-screen-v1`

Question:

> Holding the already-discovered strong 60-token strategies fixed, does a short receding-horizon time-indexed planner improve over the same strategies executed with one-step Hungarian assignment?

This is a **screening ablation** before expensive planner-aware retraining.

Fresh planning development:

- `13000–13399`: planning development
- `14000–14399`: reserved planning confirmation; do not inspect yet

Quick screening uses the first 20 planning-development scenarios and the five incumbent rule programs from `artifacts/optimizer_native_v2_dev/runs/`.

If the planner is promising, the next formal protocol must retrain 60-token rules through the rolling-horizon executor under a matched candidate-evaluation budget. If the screen is clearly harmful or computationally unreasonable, diagnose the planning formulation before spending a full search campaign.
