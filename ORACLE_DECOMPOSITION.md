# AegisSwarm Oracle Decomposition

Protocol: `aegisswarm-oracle-decomposition-v1`

## Motivation

The observable t=0 ridge selector failed full development on `28000–28399`:

```text
fixed best survival:      0.8275
selector survival:        0.8113
selector - fixed:        -0.0163 CI=[-0.0350,+0.0025]
selector - fixed reward: -2.960 CI=[-5.3340,-0.6094]
raw best-of-5 oracle:     0.9338
```

The large raw oracle gap cannot automatically be interpreted as predictable strategy specialization. `SimulatorV2` uses indexed interaction randomness keyed by `(timestep, defender_id, threat_id)`. Different programs choose different assignments and therefore encounter different stochastic interaction draws. A same-realization hindsight oracle can pick whichever program obtained the best realized path.

This protocol decomposes the oracle gap before any more selector complexity is introduced.

## Policies

No policy is trained or changed. The same five frozen 60-token incumbent programs are evaluated through `RuleGuidedHungarianPolicy`.

## Structural worlds and tapes

Fresh structural-world block:

- `30000–30399`: oracle-decomposition development
- `31000–31399`: reserved independent replication; do not inspect during development

For each structural world, the same generated scenario geometry is cloned across several independently keyed `IndexedRandomTape` instances.

Tape draws are policy-independent for a given event key, while different program action paths may expose different event keys.

## Reported quantities

### Single-tape hindsight oracle

Use tape 0 only. For each world, choose whichever program realized the highest established scalar reward on that same tape and score it on that same tape.

This intentionally reproduces the optimistic same-realization oracle behavior.

### Expected-outcome oracle

For each structural world, average each program's reward across all evaluation tapes, choose the best mean-reward program, then report that program's mean survival across those same tapes.

This reduces stochastic noise but still uses the same tapes for selection and scoring, so it remains optimistic.

### Cross-tape oracle — primary diagnostic

Split tapes into two halves.

1. Choose the best program for each structural world using mean reward on the first half; score that chosen program only on the second half.
2. Reverse the halves.
3. Average the two held-out evaluations.

The globally fixed comparator is cross-fitted in exactly the same way: select the best single global program on one half and score it on the other half, then reverse.

Primary statistic:

```text
cross-tape oracle survival - cross-tape fixed survival
```

This is still non-deployable because repeated outcomes for an identical structural world are unavailable at deployment, but it estimates how much of the raw oracle gap reflects stable structural specialization rather than same-tape luck.

### Stability diagnostics

The protocol also reports:

- agreement between first-half and second-half per-world best-program choices;
- mean modal fraction of tape-specific hindsight choices within each world;
- the fraction of the single-tape oracle gap retained by the cross-tape gap.

## Quick screen — COMPLETED

Quick used:

```text
worlds:       30000–30019 (20)
tapes/world:  4
programs:     5 frozen incumbents
```

Result:

```text
program mean survivals:          [0.7438, 0.8375, 0.8125, 0.7750, 0.8125]
single-tape fixed survival:      0.925
single-tape oracle survival:     0.975
single-tape oracle - fixed:     +0.0500 CI=[0.0000,+0.1250]
expected fixed survival:         0.8375
expected oracle survival:        0.9000
expected oracle - fixed:        +0.0625 CI=[+0.01875,+0.10625]
cross-tape fixed survival:       0.8375
cross-tape oracle survival:      0.8063
cross-tape oracle - fixed:      -0.0312 CI=[-0.0875,+0.03125]
cross-tape choice agreement:     0.450
tape-oracle modal fraction:      0.575
stable fraction of raw gap:     -0.625
```

### Quick interpretation

The optimistic oracle survives when choice and scoring use the same stochastic evidence, but does not survive held-out tapes. The primary cross-tape estimate is negative and the best-program identity is unstable between tape halves.

The negative stable-fraction statistic is not a literal negative-headroom claim. It indicates that the held-out estimate reverses sign relative to the positive same-realization oracle gap.

This is strong quick evidence that a large fraction of the raw oracle gap is stochastic hindsight rather than stable episode-level strategy specialization.

## Full development — AUTHORIZED

The purpose of this diagnostic is to decide whether episode-level specialization exists at all. Twenty structural worlds are insufficient to permanently close the direction because the cross-tape CI remains wide.

Freeze the implementation and run:

```text
worlds:       30000–30399 (400)
tapes/world:  8
programs:     5 frozen incumbents
```

```bash
python -m aegisswarm.oracle_decomposition_cli --full --workers 14
```

Do not inspect `31000–31399` unless an independent replication is explicitly justified after full development.

## Full-development interpretation gate

### Cross-tape gap becomes materially positive

If a substantial fraction of the raw oracle gap survives held-out tapes and best-program choices become reasonably stable, there is genuine structural strategy specialization. A richer observable or later-state gating architecture becomes scientifically justified.

### Cross-tape gap stays near zero or negative

Close episode-level frozen-program selection. Stop treating ~93–94% raw oracle survival as a realistic selector target. Prefer a robust global strategy or a policy that adapts from realized state over time.

### Same-tape/expected oracle stays large while cross-tape remains weak

Treat the difference as stochastic hindsight. Do not tune more selector models against the raw oracle labels.

## Claim boundary

This is a diagnostic of synthetic policy-class headroom. None of the oracle variants is deployable, and no result from this protocol establishes real-world effectiveness.
