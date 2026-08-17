# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `STOCHASTIC_ROBUST.md` — active robust-training protocol.
4. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
5. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
6. `ROLLING_HORIZON.md` — completed planner history.

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

## Completed evidence that matters now

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
```

Decision:

- weighting-only is a null result;
- backup is a weak positive but does not establish superiority;
- do not use `20000–20399` confirmation;
- do not declare backup the incumbent;
- stop one-step executor micro-tuning by default.

## Active phase — stochastic-robust training V1

Branch: `agent/stochastic-robust-training`  
Protocol: `aegisswarm-stochastic-robust-training-v1`

Hypothesis:

> Does training each 60-token strategy over multiple matched Simulator V2 random tapes per structural scenario improve expected performance on fresh stochastic scenarios?

V1 constraints:

- 60-token representation unchanged;
- local/evolutionary search only;
- scoring weights unchanged;
- structural world seed separated from random-tape seed inside the training evaluator;
- common random tapes across all candidate programs and both training arms;
- no CVaR/risk coefficient yet;
- paired arms: train through incumbent executor vs train through contingent-backup executor;
- 2×2 cross-evaluation after search to separate program adaptation and executor effect.

Fresh blocks:

- `21000–21031`: training structural worlds;
- `22000–22399`: robust development evaluation;
- `23000–23399`: reserved robust confirmation — **do not inspect**.

Quick protocol:

```text
2 paired search runs
128 candidate evaluations/arm/run
4 structural worlds
2 tapes/world
8 rollouts/candidate
20 evaluation scenarios (22000–22019)
```

Run only:

```bash
python -m aegisswarm.stochastic_robust_cli --workers 14
```

Do not run `--full` until the quick result is inspected.

## Secondary track

Best-of-5 oracle headroom is `+13.62` pp. Context-dependent strategy selection remains justified later, but robust stochastic training is first because the interaction headroom is larger and directly diagnosed.
