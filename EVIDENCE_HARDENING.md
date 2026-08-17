# AegisSwarm Evidence Hardening / Headroom Protocol

**Status:** development; architecture not frozen  
**Branch:** `agent/evidence-hardening`  
**Protocol:** `aegisswarm-evidence-hardening-v1`

## Why this phase exists

The current architecture search has reached a stable incumbent without a demonstrated gain from further proposer, representation, or short rolling-horizon variants:

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

Before another algorithmic change, this protocol asks:

> How much performance headroom exists in the current synthetic simulator, and which simulator-level limitations account for asset-loss episodes?

It also fixes an evaluation weakness in the legacy simulator: stochastic draws are consumed from one sequential RNG stream, so policy-dependent control flow can shift the random numbers associated with later events.

## Simulator V2

`aegisswarm/simulator_v2.py` is an **opt-in evaluation simulator**. It does not replace or modify legacy `Simulator`, because old evidence must remain reproducible under its original semantics.

Simulator V2 uses `IndexedRandomTape`, which derives draws from event identity rather than call order.

Current keys are conceptually:

```text
detection:   (seed, "detect", timestep, threat_id)
motion:      (seed, "motion", timestep, threat_id, axis)
interaction: (seed, "interaction", timestep, defender_id, threat_id)
```

The same event therefore receives the same stochastic draw regardless of unrelated policy-dependent random calls.

This is common-random-number hardening, not a claim that every counterfactual action has identical randomness.

## Frozen incumbent artifacts

The headroom screen loads the five independently discovered incumbent programs from:

```text
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44001.json
...
artifacts/optimizer_native_v2_dev/runs/rule_objective_seed_44005.json
```

No strategies are trained or tuned in this protocol.

## Diagnostic environments

For the same programs and scenarios, evaluate:

1. `legacy_incumbent_reference` — descriptive legacy-Simulator reference only;
2. `fixed_optimizer_v2` — fixed Hungarian baseline under Simulator V2;
3. `incumbent_v2_normal` — incumbent under indexed randomness;
4. `incumbent_v2_perfect_sensing` — all active threats observable at each sense step;
5. `incumbent_v2_deterministic_interactions` — every valid abstract interaction succeeds;
6. `incumbent_v2_combined_relaxation` — perfect sensing + deterministic interactions;
7. `best_of_5_oracle_v2` — per-scenario non-deployable oracle selecting the best of the five frozen programs.

The sensing/interaction variants are **diagnostic relaxations**, not deployable assumptions and not mathematical upper bounds. The existing policy can react differently under a relaxed environment, so these are headroom probes only.

The best-of-5 oracle is also not deployable. It measures how much scenario-dependent strategy-selection headroom already exists inside the current five-program portfolio.

## Failure attribution

For program/scenario episodes with asset loss, the suite first checks whether survival improves under the paired diagnostic relaxations. Residual failures are then labeled from direct Simulator V2 counters such as:

- undetected penetrations;
- real interaction failures;
- resource exhaustion;
- decoy resource use;
- overload steps;
- no in-range defender;
- penetrations despite remaining reachable resources.

The resulting categories are development diagnostics, not causal proof. They are intended to decide what architecture or simulator capability to investigate next.

## Evidence blocks

- development: `17000–17399`
- reserved evidence/confirmation: `18000–18399`

Quick mode uses `17000–17019`. Once inspected, those seeds are development data.

Do **not** inspect `18000–18399` while designing the simulator-v2 protocol or choosing the next algorithm.

## Run

```bash
git checkout agent/evidence-hardening
git pull origin agent/evidence-hardening
pytest -q
python -m aegisswarm.evidence_hardening_cli --workers 14
```

Expected quick artifact:

```text
artifacts/evidence_hardening_quick
```

Do not run `--full` until the quick output is inspected for simulator bugs, pathological distribution shifts, and diagnostic sanity.

If quick is valid:

```bash
python -m aegisswarm.evidence_hardening_cli --full --workers 14
```

## Interpretation gate

### Large best-of-5 headroom

Investigate a context-dependent strategy selector/meta-policy before inventing another low-level executor.

### Large perfect-sensing headroom

Prioritize state estimation/sensor allocation/observation modeling.

### Large deterministic-interaction headroom

Prioritize robustness/risk-aware objectives and stochastic-replication evaluation rather than simply increasing policy complexity.

### Large residual resource/overload headroom

Sequential resource policy or stronger long-horizon/adaptive methods become better motivated.

### Small headroom across relaxations

Stop optimizing the current benchmark toward an arbitrary higher survival target. Shift toward richer scenarios, robustness, stress/tail-risk evaluation, stronger baselines, and external calibration.

## Claims boundary

Simulator V2 is a new protocol generation. Never silently mix legacy-Simulator and Simulator-V2 results as if they were produced by one frozen stochastic process.
