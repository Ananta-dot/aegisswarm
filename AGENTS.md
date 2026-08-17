# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
4. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
5. `ROLLING_HORIZON.md` — completed planner history.

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

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

No tested proposer, compact representation, planner, or reliability executor has robustly replaced this architecture.

## Key completed evidence

### Optimizer-native V2

Rules `0.813` vs native `0.701`; native-rule `-0.1120`, CI `[-0.1405,-0.08249]`. Representation track closed.

### Rolling-horizon V2

One-step `0.808` vs rolling `0.801`; delta `-0.0065`, CI `[-0.0325,+0.01825]`, about 14x slower. Planner track closed.

### Simulator V2 headroom

Fresh `17000–17399`:

```text
normal incumbent:              0.801
perfect sensing:               0.801
deterministic interactions:    0.999
interaction headroom:         +0.1980 CI=[+0.166,+0.23625]
best-of-5 oracle:              0.938
```

The deterministic-success relaxation is a loose diagnostic, not an attainable claim. Normal episodes averaged ~15.66 failed real interaction attempts and exhausted abstract uses in ~85.15% of program-scenario episodes.

### Reliability-aware executor screen

Fresh `19000–19399`:

```text
incumbent:                    0.809
reliability weighted:         0.810
contingent backup:            0.825
weighted-incumbent:          +0.0003 CI=[-0.0165,+0.01775]
backup-incumbent:            +0.0155 CI=[-0.00625,+0.03575625]
backup-weighted:             +0.0152 CI=[-0.00825,+0.0375]
backup per-program deltas:   [-0.0025,+0.025,+0.020,+0.02875,+0.00625]
```

Decision:

- weighting-only is a null result;
- backup is a weak positive but does not establish superiority;
- do not use `20000–20399` confirmation;
- do not declare backup the incumbent;
- stop one-step executor micro-tuning by default.

## Next research direction — stochastic-robust training

The current rule programs were discovered under the legacy simulator with one stochastic realization per training scenario. Simulator V2 evidence shows stochastic interaction outcomes are the dominant measured loss source.

Next hypothesis:

> Does training each 60-token strategy over multiple matched Simulator V2 random tapes per scenario improve expected performance on fresh stochastic scenarios?

Protocol requirements:

- separate structural scenario seed from random-tape seed;
- preserve `SimulatorV2` default behavior for all completed protocols;
- use common random tapes across candidate programs within each search run;
- first version optimizes the existing scalar fitness averaged over all scenario×tape replications; no new CVaR/risk-weight hyperparameter yet;
- conventional local/evolutionary search only for the first screen; Axplorer is not needed;
- compare robust training through the incumbent executor against robust training through contingent backup under the same search seeds, candidate budget, structural worlds, and tape bundle;
- keep old frozen programs as descriptive references;
- use fresh training/development/confirmation blocks because this direction was selected after inspecting `17000–17399` and `19000–19399`.

## Secondary track

Best-of-5 oracle headroom is `+13.62` pp. Context-dependent strategy selection remains justified later, but robust stochastic training is first because the interaction headroom is larger and directly diagnosed.
