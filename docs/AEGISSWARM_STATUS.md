# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** ACTIVE RELIABILITY-AWARE EXECUTOR SCREEN; NOT FROZEN FOR EXTERNAL CLAIMS  
**Active branch:** `agent/reliability-aware-assignment`  
**Active protocol:** `aegisswarm-reliability-aware-screen-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `EVIDENCE_HARDENING.md` for the completed headroom protocol, and `RELIABILITY_AWARE.md` for the active experiment.

## Incumbent entering the active screen

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

## Why the active experiment exists

Completed Simulator V2 evidence-hardening development on fresh seeds `17000–17399`:

```text
legacy incumbent reference:       0.818
fixed optimizer v2:               0.326
incumbent v2 normal:              0.801
perfect sensing diagnostic:       0.801
deterministic interaction diag:   0.999
combined relaxation diagnostic:   0.999
best-of-5 oracle v2:              0.938
sensing headroom:                -0.0005 CI=[-0.00225, 0.0]
interaction headroom:            +0.1980 CI=[0.166, 0.23625]
combined headroom:               +0.1980 CI=[0.1645, 0.235]
```

Normal per-program survival:

```text
[0.7438, 0.8313, 0.8063, 0.8150, 0.8100]
```

Best-of-5 oracle gap: `+0.1362`. Oracle choices:

```text
{program0:63, program1:180, program2:77, program3:53, program4:27}
```

Normal diagnostic means:

```text
real interaction attempts:             30.202
real interaction failures:             15.661
decoy resource uses:                    1.3665
penetrations undetected:                0.0000
penetrations no in-range defender:      0.0000
penetrations in-range/no resource:      2.0450
penetrations with reachable resource:   0.4350
overload steps:                        42.696
resource uses remaining:                0.5315
resource exhausted fraction:            0.8515
```

Interpretation:

- sensing is not the immediate bottleneck in this simulator version;
- the dominant measured headroom is stochastic abstract interaction reliability under scarce capacity;
- deterministic-success is only a loose counterfactual diagnostic, not an attainable-policy claim;
- strategy specialization is also meaningful, but is a secondary track.

## Active reliability-aware screen

Question:

> Holding the same five frozen 60-token strategies fixed, can explicit abstract success-probability awareness improve allocation under Simulator V2?

Three executor variants are compared:

1. **Incumbent** — `RuleGuidedHungarianPolicy`.
2. **Reliability weighted** — same one-to-one Hungarian semantics, but pair score is strategic utility × abstract success probability.
3. **Contingent backup** — set-packing executor chooses either one defender or an ordered primary+backup pair per threat, with at most two defenders per threat. The backup is only consumed under existing Simulator V2 sequential resolution if the primary did not already resolve the threat.

No strategy retraining occurs in this screen.

## Fresh evidence blocks

- `19000–19399`: reliability-aware development
- `20000–20399`: reserved reliability-aware confirmation — **do not inspect**

Older `18000–18399` remains untouched and tied to the completed evidence-hardening protocol. Do not repurpose it.

Quick mode uses `19000–19019`.

## Immediate runbook

```bash
git fetch origin
git checkout agent/reliability-aware-assignment
git pull origin agent/reliability-aware-assignment
pytest -q
python -m aegisswarm.reliability_cli --workers 14
```

Expected quick summary:

```text
=== RELIABILITY-AWARE ASSIGNMENT SCREEN ===
incumbent survival: ...
reliability-weighted survival: ...
contingent-backup survival: ...
weighted - incumbent: ...
backup - incumbent: ...
backup - weighted: ...
per-program weighted deltas: ...
per-program backup deltas: ...
resources consumed inc/wgt/bak: ...
interaction failures inc/wgt/bak: ...
runtime inc/wgt/bak: ...
```

Do **not** run `--full` until the quick output is inspected.

## Decision gate

- weighted materially improves, backup does not -> keep one-to-one reliability weighting;
- backup materially improves beyond weighted -> contingent backup is promising; inspect resource use, failures, runtime, and program-level stability before full development;
- both tie or worsen -> close this executor formulation and move toward robust stochastic training/objectives rather than more executor tuning.

## Secondary future track

The best-of-5 oracle gap (`+13.62` pp) motivates a separate context-dependent strategy-selector experiment only after the reliability screen. It must use its own fresh evidence block.

## Closed tracks

- optimizer-native V2: materially worse; no V3; do not use `12000–12399` confirmation;
- rolling-horizon V1/V2: no useful gain and much slower; no planner V3; do not use `16000–16399` confirmation;
- sensing as immediate bottleneck: not supported by the Simulator V2 headroom evidence.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search is the strongest strategic representation/search combination tested so far;
- optimizer-native V2 was materially worse;
- corrected rolling-horizon execution did not improve the incumbent;
- Simulator V2 evidence shows essentially zero perfect-sensing survival headroom on `17000–17399`;
- deterministic valid interactions show large diagnostic headroom (`+19.8` pp, CI entirely positive);
- the best-of-5 frozen-program oracle shows substantial scenario-selection headroom (`+13.62` pp).

Not supported:

- that deterministic interaction success is attainable;
- that the reliability-aware executor is better before fresh testing;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
