# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form history/methodology.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay.
3. [`ROLLING_HORIZON.md`](ROLLING_HORIZON.md) — active planning-screen protocol and V1/V2 planner history.

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

## Incumbent strategic representation

The optimizer-native representation track is closed. Optimizer-native V2 was materially worse than the 60-token state-reactive rule representation:

```text
rule_objective:        0.813
native_objective_v2:   0.701
native - rule:        -0.1120, CI [-0.1405, -0.08249], p=0.000050
```

Keep the 60-token rules. Do not build a V3 native vector and do not consume `12000–12399` confirmation.

## Rolling-horizon planner V1 — completed screen, did not pass

Full fixed-program development screen on consumed seeds `13000–13399`:

```text
fixed_optimizer:  0.310
rule_one_step:    0.782 CI=[0.7390, 0.81775]
rule_rolling_v1: 0.752 CI=[0.7125, 0.7900]
rolling - one:  -0.0300 CI=[-0.07775, +0.01826]
scenario-level sign-flip p=0.000700
runtime: 0.0125 s -> 0.1837 s/scenario
```

Interpretation: V1 did not demonstrate benefit, had a negative point estimate, and was ~15x slower. The scenario-level sign-flip test and hierarchical CI use different uncertainty units: the former averages over the five frozen programs before testing scenario consistency; the latter also resamples program-to-program variation.

Code inspection found one concrete V1 pathology: projected future states could receive *higher* rule utility solely because threats became more urgent/closer later. The MILP could therefore schedule a currently feasible action at `h>0`; because only `h=0` executes and the problem is re-solved, the controller could repeatedly defer action.

## Active experiment — rolling-horizon planner V2

Branch: `agent/rolling-horizon-planning`  
Protocol: `aegisswarm-rolling-horizon-screen-v2`

V2 makes one targeted correction only:

- projection still determines future reachability;
- if a defender/threat pair is already feasible and strategically positive now, its future utility is capped at its current utility before temporal discounting;
- therefore waiting cannot make an already-feasible pair more attractive merely because urgency grows.

The same five frozen rule programs remain the comparator. This is still a screening ablation, not planner-aware retraining.

Fresh V2 data:

- development: `15000–15399`
- reserved confirmation: `16000–16399`

Old planning blocks:

- `13000–13399`: consumed planner-V1 development
- `14000–14399`: untouched old V1 confirmation; do not silently repurpose it

Run V2 quick first. Only if the corrected planner is no longer materially harmful should the full V2 screen be run. If V2 still loses, stop this rolling-horizon formulation and retain one-step rule-guided Hungarian rather than creating a planner V3 by default.
