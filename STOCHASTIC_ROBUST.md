# AegisSwarm Stochastic-Robust Training V1

**Status:** architecture development; not frozen  
**Branch:** `agent/stochastic-robust-training`  
**Protocol:** `aegisswarm-stochastic-robust-training-v1`

## Why this experiment exists

Simulator V2 headroom development showed a large stochastic-interaction gap:

```text
incumbent normal survival:          0.801
deterministic interaction diag:    0.999
interaction headroom:             +0.1980 CI=[0.166, 0.23625]
```

A subsequent fixed-program executor screen found:

```text
incumbent:                 0.809
reliability weighted:      0.810
contingent backup:         0.825
weighted-incumbent:       +0.0003 CI=[-0.0165,+0.01775]
backup-incumbent:         +0.0155 CI=[-0.00625,+0.03575625]
```

Simple one-step reliability heuristics therefore capture only a small fraction of the measured stochastic headroom.

The current 60-token programs were originally discovered under the legacy simulator using one stochastic realization per training scenario. V1 tests whether the **training distribution itself** is the problem.

## Hypothesis

> Training each candidate strategy across multiple matched Simulator V2 random tapes per structural scenario will produce 60-token strategies that generalize better to fresh stochastic scenarios.

## What is held fixed

- 60-token rule representation;
- conventional local/evolutionary search family;
- mutation/crossover mechanics;
- established scalar fitness weights;
- Simulator V2 sensing, motion and interaction laws;
- candidate budget within each compared training arm.

No Axplorer comparison is included in V1. No CVaR or explicit risk-weight hyperparameter is optimized in V1.

## Structural worlds vs stochastic tapes

Each training structural scenario is generated once from a **world seed**. It is then cloned across several policy-independent indexed random tapes.

For a world seed `w` and replication `r`, the tape seed is deterministic and independent of candidate evaluation order. Every candidate in both training arms sees the same world×tape bundle.

This provides common-random-number coupling while exposing each candidate to repeated stochastic interaction outcomes.

## Training arms

Two paired local/evolutionary searches use the same search seed, initial search mechanics, candidate budget, structural worlds and tape bundle:

1. `robust_local_incumbent` — candidate programs execute through `RuleGuidedHungarianPolicy`;
2. `robust_local_backup` — candidate programs execute through `ReliabilityAwareBackupPolicy`.

The backup executor is not assumed superior; it is retained as an ablation because the fixed-program screen had a small positive point estimate.

## V1 objective

For each candidate, metrics are averaged across all world×tape rollouts. The established scalar loss is then applied:

```text
loss = 100(1-survival)
     + 40(1-containment)
     + 3*damage
     + 0.15*resources
     + 0.05*response_delay
fitness = max(0, 200-loss)
```

Worst-quartile survival and rollout variance are recorded only as diagnostics. They are **not** part of V1 fitness.

## Quick protocol

```text
search runs:          2 paired seeds
candidate budget:     128 per arm/run
training worlds:      4
random tapes/world:   2
rollouts/candidate:   8
evaluation scenarios: 22000–22019
```

Run:

```bash
python -m aegisswarm.stochastic_robust_cli --workers 14
```

Do not run `--full` until the quick output is inspected.

## Full development protocol

If quick is valid/promising:

```text
search runs:          5 paired seeds
candidate budget:     1800 per arm/run
training worlds:      12
random tapes/world:   3
rollouts/candidate:   36
development eval:     22000–22399
```

Run:

```bash
python -m aegisswarm.stochastic_robust_cli --full --workers 14
```

## Evaluation matrix

Fresh evaluation performs a 2×2 cross:

```text
program trained with incumbent executor × incumbent executor
program trained with incumbent executor × backup executor
program trained with backup executor    × incumbent executor
program trained with backup executor    × backup executor
```

This separates:

- strategy adaptation caused by stochastic-replicated training;
- executor effect;
- co-adaptation between program and executor.

The five old frozen incumbent programs are also reported under incumbent and backup execution as **descriptive references only**, because they were trained under an older simulator generation and different search protocol.

## Fresh evidence blocks

- training structural worlds: `21000–21031` (V1 full uses the first 12);
- robust development evaluation: `22000–22399`;
- reserved robust confirmation: `23000–23399` — **do not inspect during development**.

Do not repurpose `20000–20399`; it remains the untouched confirmation block of the rejected/unfrozen reliability-executor protocol.

## Decision gate

### Robust incumbent training improves materially

Stochastic-replicated training itself is useful. Keep incumbent execution unless backup adds a clear incremental effect.

### Robust backup co-adaptation materially improves

Training and contingent execution are complementary. This becomes a candidate architecture for a later frozen confirmation protocol.

### Training arms tie old frozen references

Repeated-tape mean training is not enough. The next principled move would be an explicit risk/tail objective or a different adaptive strategy mechanism, not more executor micro-tuning.

### Performance worsens

Close V1. The current training representation/objective cannot exploit stochastic headroom under this replication scheme.

No confirmation is authorized by a quick or ambiguous development result.
