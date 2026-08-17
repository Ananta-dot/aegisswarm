# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** EPISODE-LEVEL SELECTION CLOSED; HIERARCHICAL PPO ONLINE ADAPTATION ACTIVE  
**Active branch:** `agent/ppo-adaptive-control`  
**Active protocol:** `aegisswarm-hierarchical-ppo-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `PPO_ADAPTIVE_CONTROL.md` for the active protocol, `ORACLE_DECOMPOSITION.md` for the completed oracle diagnostic, and the selector/reliability/stochastic/planning docs for closed experiments.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested proposer, compact representation, planner, reliability executor, repeated-tape training scheme, or static selector has robustly replaced this incumbent.

## Completed oracle decomposition — EPISODE-LEVEL SELECTION CLOSED

Full frozen diagnostic used `30000–30399`, 400 structural worlds and 8 independently keyed stochastic tapes/world:

```text
program mean survivals:          [0.7522, 0.8370, 0.8192, 0.8131, 0.8214]
single-tape fixed survival:      0.833
single-tape oracle survival:     0.936
single-tape oracle - fixed:     +0.1037 CI=[+0.0825,+0.12625]
expected fixed survival:         0.837
expected oracle survival:        0.887
expected oracle - fixed:        +0.0495 CI=[+0.0421875,+0.056875]
cross-tape fixed survival:       0.837
cross-tape oracle survival:      0.822
cross-tape oracle - fixed:      -0.0150 CI=[-0.024375,-0.0053125]
cross-tape choice agreement:     0.305
tape-oracle modal fraction:      0.501
stable fraction of raw gap:     -0.145
```

Decision:

- the raw `~93–94%` best-of-five oracle is a hindsight statistic strongly inflated by realization-specific stochastic outcomes;
- the per-world best frozen program does not generalize across independent stochastic tapes;
- episode-level frozen-program selection is closed;
- do **not** inspect `31000–31399`; independent replication is unnecessary for this architecture decision;
- stop using raw best-of-five survival as a realistic selector target.

## Why PPO is now justified

Earlier Simulator V2 evidence-hardening found:

```text
normal incumbent:              0.801
perfect sensing:               0.801
deterministic interactions:    0.999
interaction headroom:         +0.1980 CI=[+0.166,+0.23625]
```

Static reliability weighting, contingent backup, rolling horizon, repeated-tape training and t=0 strategy selection did not capture that headroom robustly.

The oracle decomposition shows that static episode identity is also not stable. The information that can matter is instead **realized during the episode**: failed interactions, resource depletion, overload, damage and penetrations.

Therefore the next question is:

> Can a learned online controller adapt tactical behavior from realized observable state while retaining the incumbent rule program and constrained assignment layer?

## Active experiment — hierarchical PPO V1

PPO does **not** assign defenders directly. It chooses one of six tactical modes each simulator step:

```text
0 incumbent
1 urgency
2 conserve
3 reliability
4 backup
5 failure_recovery
```

All modes share frozen base program index `1` and the existing constrained one-step assignment machinery.

The PPO observation uses detected/known state plus realized interaction/resource history only. Undetected threat state, future outcomes, scenario seed and oracle information are forbidden. Regression tests enforce the hidden-state boundary.

The reward is a scaled step-to-step difference in the established episode score. PPO uses `gamma=1.0`, making the undiscounted shaped return telescope to final established score minus the common initial score.

### Fair comparators

Fresh development compares:

1. incumbent tactical mode;
2. the best single fixed tactical mode selected only on PPO training/calibration seeds;
3. PPO online adaptive switching.

PPO must beat the fixed tactical comparator to establish value from online learning rather than merely discovering a better always-on mode.

## Fresh PPO blocks

```text
32000–32999  PPO training / tactical calibration
33000–33399  PPO development
34000–34399  reserved PPO confirmation — DO NOT INSPECT
```

Quick V1:

```text
model seeds:               42101, 42102
training budget/model:     100,000 environment steps
static calibration:        32000–32099
fresh evaluation:          33000–33019
```

Install once:

```bash
pip install -e '.[rl]'
```

Then run:

```bash
pytest -q
python -m aegisswarm.adaptive_rl_cli --workers 14
```

Do **not** use `--full` until the quick output is inspected.

## Decision gate

### PPO beats incumbent and training-selected static-best

Run full development with five PPO training seeds and 500k steps/model. If the full result remains useful, freeze architecture/hyperparameters before confirmation.

### PPO beats incumbent but not static-best

This is not evidence for RL adaptation. Prefer the simpler fixed mode and investigate it separately.

### PPO ties/worsens

Do not immediately increase model size/training budget. Inspect mode collapse and learning behavior first; close V1 if there is no credible adaptive signal.

## Evidence ledger additions

Consumed/inspected through this phase:

- `27000–27399`, `28000–28399`: observable selector V1 full development
- `30000–30399`: oracle decomposition full development

Reserved and untouched blocks include `29000–29399`, `31000–31399`, and new PPO confirmation `34000–34399`.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- deterministic interaction relaxation shows large synthetic headroom while perfect sensing does not;
- reliability weighting, backup, rolling horizon, repeated-tape training and static selector variants have not robustly replaced the incumbent;
- episode-level frozen-program selection is unstable across stochastic tapes and is closed;
- hierarchical PPO online adaptation is a new, unproven active hypothesis.

Not supported:

- PPO superiority before the active experiment runs;
- raw oracle performance as attainable;
- deterministic interaction success as attainable;
- superiority to RL or optimization generally;
- real-world effectiveness or deployment readiness.
