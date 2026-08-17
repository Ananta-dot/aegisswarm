# AegisSwarm Stochastic Training Ablation V2

**Branch:** `agent/stochastic-training-ablation`  
**Protocol:** `aegisswarm-stochastic-training-ablation-v2`

## Motivation

Simulator V2 headroom development identified a large stochastic-interaction diagnostic gap, but the reliability-aware executor screen captured only a small uncertain fraction of it. Stochastic-robust V1 then mixed two changes at once: repeated-tape training and backup-executor co-adaptation. Its quick paired result was negative for the backup arm.

V2 removes that confound and tests stochastic replication directly.

## Primary hypothesis

Holding the incumbent executor, 60-token rule representation, local/evolutionary search family, search seeds, structural worlds, candidate budget and scalar score fixed, does evaluating candidates across repeated matched Simulator V2 random tapes improve fresh-scenario performance relative to one tape per structural world?

## Arms

### Single-tape training

- `RuleGuidedHungarianPolicy`
- one indexed random tape per structural world
- replicate index 0

### Repeated-tape training

- identical `RuleGuidedHungarianPolicy`
- same structural worlds
- includes the exact same replicate-0 tape
- adds further indexed tapes for each world

The repeated-tape bundle therefore strictly contains the single-tape bundle.

## What V2 does not change

- no backup executor;
- no reliability weighting;
- no Axplorer;
- no new rule tokens;
- no planning horizon;
- no sensing changes;
- no interaction-law changes;
- no CVaR/risk coefficient;
- no scoring-weight changes.

## Compute interpretation

V2 intentionally does not equalize simulator rollout count. The repeated arm spends more simulator rollouts per candidate while retaining the same number of unique candidate evaluations. Therefore a positive V2 result establishes value of repeated stochastic evaluation under a larger rollout budget, not compute efficiency. A later compute-matched ablation is required before claiming the extra rollouts are the most efficient use of training compute.

## Quick protocol

```text
search seeds:                 97001, 97002
candidate budget/arm/run:     128
population:                   16
structural worlds:            24000–24003
single tapes/world:           1
repeated tapes/world:         2
single rollouts/candidate:    4
repeated rollouts/candidate:  8
evaluation:                   25000–25019
```

Run:

```bash
git fetch origin
git checkout agent/stochastic-training-ablation
git pull origin agent/stochastic-training-ablation
pytest -q
python -m aegisswarm.stochastic_training_ablation_cli --workers 14
```

Do **not** run `--full` until quick output is inspected.

## Full development only if quick passes

```text
search seeds:                 47001–47005
candidate budget/arm/run:     1800
population:                   64
structural worlds:            24000–24011
single tapes/world:           1
repeated tapes/world:         3
single rollouts/candidate:    12
repeated rollouts/candidate:  36
evaluation:                   25000–25399
```

Reserved confirmation: `26000–26399` — do not inspect during development.

## Primary output

```text
=== STOCHASTIC TRAINING ABLATION V2 ===
frozen reference: ...
single-tape training: ...
repeated-tape training: ...
repeated - single: ... CI=[...]
per-run deltas: [...]
training rollouts/candidate: ... / ...
```

The frozen reference is descriptive only. The primary causal comparison is repeated-tape minus single-tape training.

## Decision gate

### Positive repeated-tape signal

If repeated-tape training materially exceeds single-tape training with mostly positive per-run effects, proceed to full V2 development. A later compute-matched ablation is required before final efficiency claims.

### Tie

If the arms are roughly tied, repeated stochastic evaluation does not justify its added rollout cost. Stop V2 before full development.

### Negative

If repeated-tape training is worse, close mean-replication training. The next separate architecture hypothesis is context-dependent strategy selection, motivated by the earlier best-of-5 oracle gap.

## Evidence hygiene

V1 quick inspected `21000–21003` and `22000–22019`; the V1 blocks are not reused for V2. V2 gets fresh training/development/confirmation blocks `24000`, `25000`, and `26000` respectively.
