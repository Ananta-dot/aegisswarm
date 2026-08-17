# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** STOCHASTIC-ROBUST V1 QUICK CLOSED; MATCHED STOCHASTIC-TRAINING ABLATION V2 ACTIVE  
**Active branch:** `agent/stochastic-training-ablation`  
**Active protocol:** `aegisswarm-stochastic-training-ablation-v2`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `EVIDENCE_HARDENING.md` for Simulator V2 headroom evidence, `RELIABILITY_AWARE.md` for the completed executor screen, and `STOCHASTIC_ROBUST.md` for V1 history.

## Incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

No tested proposer, compact representation, rolling planner, reliability weighting, or contingent-backup variant has robustly replaced this incumbent.

## Evidence motivating stochastic training

Simulator V2 headroom development on `17000–17399`:

```text
incumbent normal:              0.801
perfect sensing:              0.801
deterministic interactions:    0.999
interaction headroom:         +0.1980 CI=[+0.166,+0.23625]
best-of-5 oracle:              0.938
```

This identifies stochastic abstract interaction outcomes under scarce resources as the dominant measured headroom source. Deterministic success is only a loose counterfactual diagnostic.

Reliability-aware executor development on `19000–19399`:

```text
incumbent:                    0.809
weighted:                     0.810
contingent backup:            0.825
weighted-incumbent:          +0.0003 CI=[-0.0165,+0.01775]
backup-incumbent:            +0.0155 CI=[-0.00625,+0.03575625]
```

Weighting-only is a null result. Backup is a weak positive and did not earn confirmation. Do not inspect `20000–20399`.

## Stochastic-robust V1 quick — CLOSED

Quick V1 used two paired search runs, 4 structural worlds × 2 tapes/world, 128 candidates per arm/run and fresh evaluation scenarios `22000–22019`.

```text
frozen incumbent reference:      0.680
frozen backup reference:         0.745
robust inc / inc executor:       0.713
robust inc / backup executor:    0.625
robust backup / inc executor:    0.600
robust backup / backup executor: 0.625
co-adapted backup - incumbent:   -0.0875 CI=[-0.225,+0.05]
executor effect on inc-programs: -0.0875 CI=[-0.275,+0.05]
program effect under incumbent:  -0.1125 CI=[-0.275,+0.025]
program effect under backup:     +0.0000 CI=[-0.125,+0.15]
main per-run deltas:             [-0.05,-0.125]
```

Decision:

- backup/co-adaptation fails the quick gate;
- do not run stochastic-robust V1 `--full`;
- do not inspect `23000–23399` confirmation;
- `21000–21003` training worlds and `22000–22019` evaluation scenarios were inspected;
- because the protocol changes after this result, do not reuse the remainder of the V1 training/development blocks as unseen V2 evidence.

The apparent `0.713` robust-incumbent result versus the frozen `0.680` reference is descriptive only. Those groups were trained under different simulator/search protocols and contain different numbers of independent trained policies, so the comparison does not isolate stochastic replication.

## Active experiment — matched stochastic-training ablation V2

Primary question:

> Holding the incumbent executor, 60-token representation, local/evolutionary search, search seeds, structural worlds, candidate budget and scalar score fixed, does evaluating each candidate over repeated matched Simulator V2 random tapes improve fresh-scenario performance relative to one tape per structural world?

Two paired training arms:

1. **single-tape V2 training** — one indexed tape per structural world;
2. **repeated-tape V2 training** — the exact same replicate-0 tape plus additional indexed tapes for every structural world.

Both use `RuleGuidedHungarianPolicy`. Backup is removed from V2 so the only intended algorithmic difference is stochastic replication during candidate evaluation.

V2 intentionally does not compute-match simulator rollouts: repeated-tape evaluation costs more per candidate. If it produces a real gain, a later compute-efficiency ablation can ask whether the gain survives equal rollout budgets.

### Fresh V2 blocks

- `24000–24031`: structural training worlds
- `25000–25399`: development evaluation
- `26000–26399`: reserved confirmation — do not inspect

### Quick V2 protocol

```text
paired search runs:           2
candidate budget/arm/run:     128
structural worlds:            4
single arm:                   1 tape/world = 4 rollouts/candidate
repeated arm:                 2 tapes/world = 8 rollouts/candidate
evaluation:                   25000–25019
```

Run only:

```bash
python -m aegisswarm.stochastic_training_ablation_cli --workers 14
```

Do not run `--full` until quick V2 is inspected.

### Full V2 only if quick passes

```text
paired search runs:           5
candidate budget/arm/run:     1800
structural worlds:            12
single arm:                   12 rollouts/candidate
repeated arm:                 36 rollouts/candidate
development evaluation:       25000–25399
```

## Decision gate

- repeated-tape materially beats single-tape with mostly positive per-run effects -> stochastic replication is useful; run full development;
- rough tie -> repeated evaluation does not justify 2–3x rollout cost; stop V2 before full;
- repeated-tape worse -> close mean-replication training and consider the separate strategy-selection signal rather than adding more stochastic objective complexity immediately.

## Secondary track

The frozen best-of-5 oracle reached `0.938`, a `+13.62` pp gap over mean incumbent performance. Context-dependent strategy selection remains the strongest separate architecture hypothesis if stochastic-training V2 does not improve.

## Evidence hygiene

Consumed or partially consumed current-generation blocks:

- `17000–17399`: evidence-hardening development
- `19000–19399`: reliability-aware executor development
- V1 quick inspected `21000–21003` training worlds and `22000–22019` evaluation scenarios; treat the associated V1 blocks as unavailable for changed V2 evidence

Reserved older protocol blocks remain untouched and must not be repurposed silently, including `18000–18399`, `20000–20399`, and `23000–23399`.

## Claims policy

Supported development-level conclusions include zero useful sensing headroom in the measured Simulator V2 protocol, large deterministic-interaction diagnostic headroom, a null reliability-weighting result, a small uncertain contingent-backup point estimate, and a negative V1 quick co-adaptation result.

Not supported: repeated-tape training superiority before V2 runs, deterministic interaction success as attainable, backup superiority, superiority to optimization or RL generally, or real-world effectiveness/deployment readiness.
