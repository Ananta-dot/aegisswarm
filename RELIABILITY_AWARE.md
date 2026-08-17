# AegisSwarm Reliability-Aware Assignment Screen

**Status:** full development complete; not frozen  
**Branch:** `agent/reliability-aware-assignment`  
**Protocol:** `aegisswarm-reliability-aware-screen-v1`

## Motivation

Simulator V2 headroom development on fresh seeds `17000–17399` showed:

```text
incumbent normal survival:             0.801
perfect-sensing survival:              0.801
interaction-deterministic survival:    0.999
interaction headroom:                 +0.1980 CI=[0.166, 0.23625]
best-of-5 oracle survival:             0.938
```

This motivated testing whether explicit abstract success-probability awareness could use scarce resources more effectively. The deterministic-success result is only a loose counterfactual diagnostic.

## Frozen strategic layer

The same five previously discovered 60-token rule programs were held fixed. No search or retraining occurred.

## Variants

1. **Incumbent** — `RuleGuidedHungarianPolicy`.
2. **ReliabilityWeightedHungarianPolicy`** — same one-to-one assignment semantics, but positive strategic utility is multiplied by Simulator V2 abstract success probability.
3. **ReliabilityAwareBackupPolicy`** — one-step set-packing MILP may assign an ordered primary+backup pair to a threat. The backup consumes a use only if the primary does not already resolve the threat under existing Simulator V2 sequential resolution semantics.

For a primary/backup pair:

```text
expected score = u1*p1 + (1-p1)*u2*p2
```

## Fresh development result

Full development block `19000–19399`, five frozen programs:

```text
incumbent survival:               0.809
reliability-weighted survival:    0.810
contingent-backup survival:       0.825
weighted - incumbent:            +0.0003 CI=[-0.0165, +0.01775]
backup - incumbent:              +0.0155 CI=[-0.00625, +0.03575625]
backup - weighted:               +0.0152 CI=[-0.00825, +0.0375]
per-program weighted deltas:      [+0.0050, -0.0125, +0.00125, +0.00875, -0.00125]
per-program backup deltas:        [-0.0025, +0.0250, +0.0200, +0.02875, +0.00625]
resources consumed inc/wgt/bak:   31.492 / 31.494 / 31.547
real interaction failures:        15.422 / 15.460 / 15.908
runtime inc/wgt/bak:              0.0218s / 0.0219s / 0.0450s
```

## Interpretation

### Reliability weighting

Rejected as a useful executor change. The full-screen improvement is only `+0.03` percentage points and the interval is centered on zero.

### Contingent backup

A weak positive development signal only:

- `+1.55` pp mean survival vs incumbent;
- four of five per-program effects positive, one slightly negative;
- hierarchical CI crosses zero;
- actual abstract resource consumption is nearly unchanged;
- runtime roughly doubles, although absolute runtime remains small.

Raw interaction-failure counts are not failure rates because backup changes attempt volume. The result does not establish that backup reduces interaction failure probability; it only shows a small survival point estimate under the tested execution semantics.

## Decision

- Do not consume `20000–20399` confirmation.
- Do not declare backup the incumbent.
- Do not continue weighting/backup executor micro-tuning by default.
- The simple executor variants capture only a small fraction of the large stochastic-interaction headroom.
- Move to stochastic-robust training: evaluate each candidate across multiple policy-independent Simulator V2 random tapes per scenario under common random numbers.

The first robust-training version should keep the existing scalar fitness averaged over repeated tapes; do not add a CVaR/risk-weight hyperparameter yet. Compare robust training through the incumbent executor against robust training through contingent backup under the same candidate/tape budget.

## Evidence hygiene

Consumed:

- `19000–19399`: reliability-aware development.

Untouched:

- `20000–20399`: reserved reliability-aware confirmation. Leave untouched because the executor did not earn a freeze.
- `18000–18399`: reserved for the earlier evidence-hardening protocol. Do not repurpose.
