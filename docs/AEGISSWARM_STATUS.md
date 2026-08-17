# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** EPISODE-LEVEL SELECTION CLOSED; PPO V1 QUICK NEUTRAL; FROZEN PPO GENERALIZATION ACTIVE  
**Active branch:** `agent/ppo-adaptive-control`  
**Active protocols:** `aegisswarm-hierarchical-ppo-v1` and `aegisswarm-hierarchical-ppo-v1-frozen-extension`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `PPO_ADAPTIVE_CONTROL.md` for PPO V1, `PPO_FROZEN_EXTENSION.md` for the active no-retraining gate, and `ORACLE_DECOMPOSITION.md` for the completed oracle diagnostic.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested proposer, compact representation, planner, reliability executor, repeated-tape training scheme, static selector or RL controller has robustly replaced this incumbent.

## Oracle decomposition — episode-level selection closed

Full frozen diagnostic on `30000–30399`, 400 structural worlds and 8 independent indexed tapes/world:

```text
single-tape oracle - fixed:      +0.1037 CI=[+0.0825,+0.12625]
expected oracle - fixed:         +0.0495 CI=[+0.0421875,+0.056875]
cross-tape oracle - fixed:       -0.0150 CI=[-0.024375,-0.0053125]
cross-tape choice agreement:      0.305
```

The raw ~93–94% best-of-five oracle is substantially hindsight-driven. Per-world frozen-program identity does not generalize across stochastic tapes. Episode-level preselection is closed; `31000–31399` remains untouched.

## Why online RL remains a legitimate hypothesis

Simulator V2 evidence-hardening previously found:

```text
normal incumbent:              0.801
perfect sensing:               0.801
deterministic interactions:    0.999
interaction headroom:         +0.1980 CI=[+0.166,+0.23625]
```

The useful information appears during the episode: realized failures, resource depletion, overload, damage and penetrations. Hierarchical PPO therefore controls tactical mode selection online while retaining the frozen strategic program and constrained assignment layer.

## Hierarchical PPO V1 architecture

PPO never directly chooses defender-threat assignments. It chooses one of six tactical modes each simulator step:

```text
0 incumbent
1 urgency
2 conserve
3 reliability
4 backup
5 failure_recovery
```

All modes use frozen base program index `1`. Observations contain detected/known state plus realized history only; hidden undetected threat state, future outcomes, scenario seed and oracle information are forbidden and regression-tested.

Reward:

```text
r_t = (established_score_t - established_score_{t-1}) / 10
```

with `gamma=1.0`, so undiscounted shaped return telescopes to final established score minus the common initial score.

## PPO V1 quick — neutral on survival

Quick used model seeds `42101/42102`, 100,000 environment steps/model, calibration `32000–32099`, and fresh evaluation `33000–33019`.

```text
calibrated static best mode:     4 (backup)
incumbent survival:              0.800
static-best survival:            0.800
PPO adaptive survival:           0.800
static best - incumbent:        +0.0000 CI=[-0.125,+0.125]
PPO - incumbent:                +0.0000 CI=[-0.075,+0.075]
PPO - static best:              +0.0000 CI=[-0.0875,+0.100]
PPO per-run survival deltas:     [0.0,0.0]
```

The learned policies are not behaviorally collapsed:

```text
seed 42101: mostly conserve + failure_recovery
seed 42102: mostly failure_recovery + reliability, with incumbent/backup use
```

From the printed aggregate metric means, PPO's established score is approximately `-0.10` points versus incumbent and `+1.68` points versus always-backup. This is descriptive only because the original quick reporter did not compute row-wise score uncertainty.

Decision: do **not** spend the old five-model × 500k full budget yet.

## Active gate — frozen PPO generalization extension

No retraining or tuning occurs. Evaluate the exact two saved quick PPO models on 100 additional untouched PPO-development scenarios:

```text
33020–33119
```

The extension reports:

- incumbent / static-best / PPO survival;
- row-wise established scalar reward;
- hierarchical survival and reward deltas across the two training seeds;
- per-training-run deltas;
- interaction attempts/failures and aggregate failure rate;
- resource exhaustion, overload and resources remaining;
- PPO tactical-mode proportions.

Run:

```bash
pytest -q
python -m aegisswarm.adaptive_rl_frozen_cli
```

No PPO training occurs in that command.

## PPO evidence blocks

```text
32000–32999  PPO training / calibration
33000–33019  PPO quick evaluation — inspected
33020–33119  frozen-model generalization extension — active
33120–33399  remaining PPO development
34000–34399  PPO confirmation — DO NOT INSPECT
```

## Decision after frozen extension

### Positive survival/reward signal

Keep RL online adaptation alive, but define a fresh longer-training V2 protocol before changing the training budget. Do not simply score larger models on already-inspected evidence.

### Essentially tied with incumbent

Close hierarchical PPO V1 at this six-mode resolution. More timesteps alone are not justified.

### Worse than incumbent

Close V1. If RL is revisited, change the learning abstraction rather than only increasing model size or rollout budget.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the incumbent;
- deterministic interaction relaxation shows large synthetic headroom while perfect sensing does not;
- reliability weighting, backup, rolling horizon, repeated-tape training and static selector variants have not robustly replaced the incumbent;
- episode-level frozen-program selection is unstable across stochastic tapes and is closed;
- PPO V1 learned nontrivial switching behavior but showed no survival advantage on the first 20 fresh scenarios.

Not supported:

- PPO superiority;
- raw oracle performance as attainable;
- deterministic interaction success as attainable;
- superiority to RL or optimization generally;
- real-world effectiveness or deployment readiness.
