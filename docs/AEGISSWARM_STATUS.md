# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** ACTIVE RELIABILITY-AWARE EXECUTOR DEVELOPMENT; NOT FROZEN FOR EXTERNAL CLAIMS  
**Active branch:** `agent/reliability-aware-assignment`  
**Active protocol:** `aegisswarm-reliability-aware-screen-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `EVIDENCE_HARDENING.md` for the completed headroom protocol, and `RELIABILITY_AWARE.md` for the active executor experiment.

## Incumbent entering the active screen

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

## Why reliability is now the primary hypothesis

Completed Simulator V2 headroom development on fresh seeds `17000–17399` found:

```text
incumbent v2 normal:              0.801
perfect sensing diagnostic:      0.801
deterministic interaction diag:  0.999
best-of-5 oracle v2:              0.938
sensing headroom:                -0.0005 CI=[-0.00225, 0.0]
interaction headroom:            +0.1980 CI=[0.166, 0.23625]
```

Normal program-scenario episodes averaged `15.661` failed real interaction attempts, exhausted all abstract uses in `85.15%` of episodes, had zero undetected penetrations, and used comparatively few resources on decoys. The deterministic-success relaxation is a loose diagnostic, not a deployable or mathematical upper-bound claim.

This motivates explicit success-probability-aware allocation before any new proposer, representation, planner, or sensing work.

## Active reliability-aware screen

The same five frozen rule programs are compared under:

1. **incumbent** — ordinary rule-guided one-to-one Hungarian;
2. **reliability weighted** — same one-to-one matching but pair score = strategic utility × abstract success probability;
3. **contingent backup** — one-step set-packing executor that may select an ordered primary+backup pair for a threat. Under existing Simulator V2 sequential resolution, the backup consumes a use only if the threat remains active after the primary attempt.

No strategy retraining occurs in this screen.

## Quick development result — PASSED GATE

Quick subset: `19000–19019`, five frozen programs, Simulator V2 indexed randomness.

```text
incumbent survival:               0.810
reliability-weighted survival:    0.835
contingent-backup survival:       0.860
weighted - incumbent:            +0.0250 CI=[-0.065, +0.120125]
backup - incumbent:              +0.0500 CI=[-0.035, +0.135]
backup - weighted:               +0.0250 CI=[-0.060, +0.115125]
per-program weighted deltas:      [0.000, 0.000, 0.000, +0.025, +0.100]
per-program backup deltas:        [-0.025, +0.025, +0.100, +0.075, +0.075]
resources consumed inc/wgt/bak:   31.940 / 31.990 / 32.110
real interaction failures:        15.270 / 15.910 / 16.100
runtime inc/wgt/bak:              0.0217s / 0.0216s / 0.0443s
```

### Interpretation

- This is a 20-scenario development gate only; all survival CIs cross zero.
- Both reliability-aware variants have positive point estimates.
- Backup is positive on four of five independently discovered programs and negative on one.
- The +5 pp backup point estimate is large enough to justify the full fresh development screen.
- Raw interaction-failure counts rise slightly while survival improves. Do **not** interpret that as reduced reliability: the variants can change attempt volume and contingency behavior. Full interpretation must consider survival, attempts/failure rate, resource exhaustion, penetrations/damage, and resource use together.
- Backup roughly doubles executor runtime but remains small in absolute terms in the current synthetic setup.

## Fresh evidence blocks

- `19000–19399`: reliability-aware development — active
- `20000–20399`: reserved reliability-aware confirmation — **do not inspect**

`18000–18399` remains untouched and tied to the evidence-hardening protocol. Do not repurpose it.

## Immediate runbook

The quick gate has passed. Pull current reporting/docs and run the full fixed-program development screen:

```bash
git checkout agent/reliability-aware-assignment
git pull origin agent/reliability-aware-assignment
pytest -q
python -m aegisswarm.reliability_cli --full --workers 14
```

Do not retrain strategies and do not inspect `20000–20399`.

## Decision after full development

### Reliability weighted materially improves; backup adds little

Retain one-to-one success-probability-aware pairing and avoid backup complexity.

### Backup materially improves beyond incumbent/weighted

Contingent reliability allocation becomes the leading executor candidate. Inspect resource use, exhaustion, interaction attempts/failure rate, damage/penetrations, per-program stability, and runtime before deciding whether to train the 60-token strategy through it.

### Both roughly tie

The large deterministic-interaction headroom exists but is not captured by this simple executor. Stop executor variants and move to stochastic/risk-aware training objectives or repeated-outcome evaluation.

### Both worsen

Retain the incumbent executor; close this formulation.

No confirmation block is consumed during architecture development.

## Secondary future track

The completed best-of-5 oracle reached `0.938`, a `+13.62` pp gap over mean incumbent performance. Context-dependent strategy selection remains a justified secondary experiment after the reliability track, using its own fresh seeds.

## Closed tracks

- optimizer-native V2: materially worse; no V3; do not use `12000–12399` confirmation;
- rolling-horizon V1/V2: no useful gain and much slower; no planner V3; do not use `16000–16399` confirmation;
- sensing as the immediate bottleneck: not supported by Simulator V2 headroom development.

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- optimizer-native V2 was materially worse;
- corrected rolling-horizon execution did not improve the incumbent;
- perfect-sensing headroom was essentially zero on `17000–17399`;
- deterministic valid interactions showed large diagnostic headroom (`+19.8` pp, CI entirely positive);
- best-of-5 frozen-program oracle showed substantial scenario-selection headroom (`+13.62` pp);
- reliability-aware weighted and backup executors passed a 20-scenario development gate with positive point estimates, but superiority is not established.

Not supported:

- deterministic interaction success as an attainable assumption;
- reliability-aware executor superiority before the full fresh development screen;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
