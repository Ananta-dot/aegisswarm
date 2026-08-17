# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `STRATEGY_SELECTOR.md` — active selector protocol.
4. `STOCHASTIC_TRAINING_ABLATION.md` — closed repeated-tape V2.
5. `STOCHASTIC_ROBUST.md` — closed robust-training V1.
6. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
7. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
8. `ROLLING_HORIZON.md` — completed planner history.

## Non-negotiable rules

1. Never consume reserved confirmation seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside a protocol.
4. Compare components by ablation, not ideology.
5. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
6. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
7. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
8. Keep handoff/status docs current after major experiments.
9. Do not run confirmation merely because a quick or development point estimate is positive.
10. Legacy `Simulator` and `SimulatorV2` are different protocol generations; label them explicitly.
11. Selector features must never expose undetected threat state, scenario seed, future outcomes or oracle information.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

No tested proposer, compact representation, planner, reliability executor, or repeated-tape training scheme has robustly replaced it.

## Evidence that matters now

Simulator V2 headroom on `17000–17399`:

```text
normal mean:                  0.801
perfect sensing:             0.801
deterministic interactions:  0.999
best-of-5 frozen oracle:     0.938
program survivals:           [0.7438,0.8313,0.8063,0.8150,0.8100]
```

The oracle is about `+10.7 pp` above the strongest fixed frozen program on that block, motivating strategy selection. It is non-deployable hindsight.

Reliability executor on `19000–19399`: weighting null; backup `+1.55 pp` with CI crossing zero. Do not inspect `20000–20399`.

Stochastic-robust V1 quick: co-adapted backup minus incumbent `-8.75 pp`; V1 closed. Do not inspect `23000–23399`.

Clean stochastic-training V2 quick:

```text
single tape:       0.787
repeated tape:     0.725
repeated-single:  -0.0625 CI=[-0.200,+0.050]
per-run deltas:   [-0.100,-0.025]
```

V2 closed. Do not inspect `26000–26399`.

## Active phase — observable strategy selector V1

Branch: `agent/strategy-selector`  
Protocol: `aegisswarm-observable-strategy-selector-v1`

Frozen policy set: the same five incumbent 60-token programs.

Selector timing:

```text
SimulatorV2 t=0 sensing
    -> observable feature snapshot
    -> choose one frozen program
    -> commit for episode
```

Allowed features use detected threats plus known assets/defenders/sensors/resources. Undetected threat state is forbidden and tested for leakage.

V1 model: five fixed ridge reward regressors (`alpha=1.0`, untuned). Each predicts the established scalar episode reward of one frozen program from the t=0 observable feature vector.

Primary comparator: the best globally fixed frozen program selected on selector-training data. Do not compare primarily against the mean of five programs.

Development oracle: best-of-5 in hindsight on the fresh evaluation block; report as headroom only.

Fresh blocks:

- `27000–27399`: selector training
- `28000–28399`: selector development
- `29000–29399`: selector confirmation — **do not inspect**

Quick uses `27000–27099` training and `28000–28019` evaluation.

Run only:

```bash
pytest -q
python -m aegisswarm.strategy_selector_cli --workers 14
```

Do not use `--full` until quick output is inspected.
