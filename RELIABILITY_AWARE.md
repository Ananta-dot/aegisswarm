# AegisSwarm Reliability-Aware Assignment Screen

**Status:** architecture development; not frozen  
**Branch:** `agent/reliability-aware-assignment`  
**Protocol:** `aegisswarm-reliability-aware-screen-v1`

## Why this experiment exists

Evidence-hardening development on fresh Simulator V2 seeds `17000–17399` showed:

```text
incumbent normal survival:             0.801
perfect-sensing survival:              0.801
interaction-deterministic survival:    0.999
interaction headroom:                 +0.1980 CI=[0.166, 0.23625]
best-of-5 oracle survival:             0.938
```

Normal episodes averaged `15.661` failed real interaction attempts and were resource-exhausted in `85.15%` of program-scenario episodes. Undetected penetrations were zero and decoy resource use was small relative to total attempts.

This does **not** imply deterministic success is attainable. It motivates testing whether allocation that explicitly accounts for abstract success probability can use scarce resources more effectively.

## Frozen strategic layer

The same five previously discovered 60-token rule programs remain fixed. No candidate search or retraining occurs in this screen.

## Three executor variants

### 1. Incumbent

`RuleGuidedHungarianPolicy`

- rule-derived strategic pair utility;
- one defender per threat;
- one threat per defender;
- no explicit success-probability factor in the assignment objective.

### 2. Reliability-weighted Hungarian

`ReliabilityWeightedHungarianPolicy`

Preserves the incumbent one-to-one assignment semantics but multiplies each positive strategic utility by Simulator V2's abstract success probability.

This isolates the effect of choosing more reliable feasible pairings without introducing redundancy.

### 3. Reliability-aware contingent backup

`ReliabilityAwareBackupPolicy`

At each step the policy constructs mutually exclusive action groups:

- one defender assigned to one threat; or
- an ordered pair of defenders assigned to one threat, with the second acting as a contingent backup under existing Simulator V2 sequential resolution semantics.

For a single defender:

```text
expected score = u1 * p1
```

For an ordered primary/backup pair:

```text
expected score = u1*p1 + (1-p1)*u2*p2
```

where `u` is the incumbent rule-derived strategic utility and `p` is the abstract Simulator V2 success probability.

A small binary set-packing MILP chooses groups subject to:

- each defender appears in at most one selected group;
- each threat receives at most one selected group;
- maximum two defenders per threat;
- no future-horizon planning.

The backup is not an extra guaranteed interaction: it remains subject to the same stochastic Simulator V2 outcome if the primary fails.

## Evidence hygiene

Because this executor was designed after inspecting evidence-hardening development, it receives fresh blocks:

- `19000–19399`: reliability-aware development
- `20000–20399`: reserved reliability-aware confirmation

Do not inspect `20000–20399` during architecture development.

Do not repurpose `18000–18399`; it remains untouched and belongs to the completed evidence-hardening protocol.

## Runbook

```bash
git fetch origin
git checkout agent/reliability-aware-assignment
git pull origin agent/reliability-aware-assignment
pytest -q
python -m aegisswarm.reliability_cli --workers 14
```

Expected quick markers:

```text
AegisSwarm reliability-aware screen
=== RELIABILITY-AWARE ASSIGNMENT SCREEN ===
incumbent survival: ...
reliability-weighted survival: ...
contingent-backup survival: ...
weighted - incumbent: ...
backup - incumbent: ...
backup - weighted: ...
```

Do not run `--full` until the 20-scenario quick output is inspected.

## Decision gate

### Weighted improves, backup does not

Success-probability-aware pair selection is useful; retain one-to-one assignment and avoid extra backup complexity.

### Backup improves materially beyond weighted

Contingent redundancy is useful under scarce stochastic resources. Inspect resource consumption, interaction failures, per-program stability, and runtime before any strategy retraining.

### Both tie

The large deterministic-interaction headroom cannot be captured by this simple expected-value allocator. Stop this executor formulation rather than tuning it indefinitely; revisit robust stochastic objectives or repeated-scenario training.

### Both worsen

Retain the incumbent executor. The headroom remains environmental/stochastic but this allocation mechanism is not the solution.

No confirmation block is consumed during screening.
