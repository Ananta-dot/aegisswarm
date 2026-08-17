# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** STOCHASTIC-TRAINING V2 QUICK FAILED; STRATEGY SELECTION IS NEXT  
**Active branch:** `agent/stochastic-training-ablation`  
**Completed quick protocol:** `aegisswarm-stochastic-training-ablation-v2`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `EVIDENCE_HARDENING.md` for Simulator V2 headroom evidence, `RELIABILITY_AWARE.md` for the reliability-executor screen, `STOCHASTIC_ROBUST.md` for robust-training V1, and `STOCHASTIC_TRAINING_ABLATION.md` for V2.

## Incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested proposer, compact representation, planner, reliability executor, or repeated-tape training protocol has robustly replaced this incumbent.

## Completed evidence that determines the next step

### Simulator V2 headroom — `17000–17399`

```text
normal incumbent:              0.801
perfect sensing:               0.801
deterministic interactions:    0.999
interaction headroom:         +0.1980 CI=[+0.166,+0.23625]
best-of-5 oracle:              0.938
```

The deterministic-success relaxation is a loose counterfactual diagnostic, not an attainable-policy claim. The best-of-5 oracle is also non-deployable; it is evidence that the frozen strategies specialize across scenarios.

On the same evidence block, frozen-program survival rates were approximately:

```text
[0.7438, 0.8313, 0.8063, 0.8150, 0.8100]
```

So the oracle `0.938` is about `+10.7 pp` above the strongest fixed frozen program on that block, not merely above the mean program performance.

### Reliability-aware executor screen — `19000–19399`

```text
incumbent:                    0.809
reliability weighted:         0.810
contingent backup:            0.825
weighted-incumbent:          +0.0003 CI=[-0.0165,+0.01775]
backup-incumbent:            +0.0155 CI=[-0.00625,+0.03575625]
```

Decision: weighting-only is null; backup is a weak positive but did not earn confirmation. Do not inspect `20000–20399`.

### Stochastic-robust V1 quick — CLOSED

V1 mixed repeated stochastic candidate evaluation with backup-executor co-adaptation. Quick result on inspected `22000–22019`:

```text
robust inc/inc:          0.713
robust backup/backup:    0.625
co-adapted delta:       -0.0875 CI=[-0.225,+0.05]
per-run deltas:         [-0.05,-0.125]
```

Do not run full V1 and do not inspect `23000–23399`.

### Stochastic-training V2 quick — CLOSED

V2 cleanly isolated repeated stochastic candidate evaluation under the same incumbent executor. Quick result on fresh `25000–25019`:

```text
frozen reference:               0.795
single-tape training:           0.787
repeated-tape training:         0.725
repeated - single:             -0.0625 CI=[-0.200,+0.050]
per-run deltas:                 [-0.100,-0.025]
training rollouts/candidate:    4 / 8
runtime single/repeated:        0.0171s / 0.0166s
```

Decision:

- repeated-tape candidate evaluation fails the quick gate;
- both paired search-run effects are negative;
- do **not** run V2 `--full`;
- do **not** inspect `26000–26399` confirmation;
- stop repeated-tape training as the next performance direction by default.

The frozen reference is descriptive only and is not used to infer the repeated-tape effect.

## Next experiment — observability-safe strategy selection

The strongest remaining empirical signal is frozen-strategy specialization. The earlier best-of-5 oracle reached `0.938`, while the strongest individual frozen program on that block was about `0.831`.

Next question:

> Can a selector using only information observable before the first action choose among the five existing frozen 60-token programs better than committing to one globally fixed program?

The first selector experiment should be deliberately simple and interpretable:

- keep all five frozen programs unchanged;
- use Simulator V2 indexed randomness;
- take a feature snapshot after the simulator's first sensing step and before the first assignment;
- features may use only detected active threats plus known assets, defenders, sensors and resource state;
- never use undetected threat type/position, future trajectories, realized interaction outcomes, or oracle labels at evaluation time;
- fit one fixed ridge reward model per program from development-training scenarios;
- choose the program with highest predicted established scalar reward;
- compare against the **best fixed program selected on selector-training data**, not against the mean of five programs;
- report the non-deployable oracle on fresh development only as remaining headroom.

Use new blocks because this architecture is motivated by inspected oracle results and failed stochastic-training experiments.

## Evidence ledger

Consumed/inspected blocks include:

- `2000–2099`: structured development-test
- `2100–2499`: V1 formal holdout
- `3000–3399`: Axplorer V2 development
- `4000–4399`: hybrid-executor development
- `5000–5399`: hybrid-objective development
- `9000–9399`: optimizer-native V1 development
- `11000–11399`: optimizer-native V2 development
- `13000–13399`: rolling-horizon V1 development
- `15000–15399`: rolling-horizon V2 development
- `17000–17399`: evidence-hardening/headroom development
- `19000–19399`: reliability-aware executor development
- `21000–21003`: stochastic-robust V1 quick training worlds inspected
- `22000–22019`: stochastic-robust V1 quick evaluation inspected
- `24000–24003`: stochastic-training V2 quick training worlds inspected
- `25000–25019`: stochastic-training V2 quick evaluation inspected

Reserved blocks tied to abandoned/unfrozen protocols must not be repurposed silently, including `18000–18399`, `20000–20399`, `23000–23399`, and `26000–26399`.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- optimizer-native V2 was materially worse;
- corrected rolling-horizon execution did not improve the incumbent;
- perfect-sensing headroom was essentially zero on `17000–17399`;
- deterministic valid interactions showed large diagnostic headroom (`+19.8` pp, CI entirely positive);
- the five frozen strategies exhibit substantial best-of-set scenario specialization;
- reliability-weighted Hungarian did not improve full-screen survival;
- contingent backup produced only a small uncertain positive point estimate;
- repeated-tape stochastic candidate evaluation failed its clean V2 quick gate.

Not supported:

- strategy-selector superiority before the next experiment;
- deterministic interaction success as attainable;
- contingent-backup executor superiority;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
