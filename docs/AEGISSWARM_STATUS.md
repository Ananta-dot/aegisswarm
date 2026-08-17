# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** STOCHASTIC-ROBUST TRAINING V1 ACTIVE; NOT FROZEN FOR EXTERNAL CLAIMS  
**Active branch:** `agent/stochastic-robust-training`  
**Active protocol:** `aegisswarm-stochastic-robust-training-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `EVIDENCE_HARDENING.md` for Simulator V2 headroom evidence, `RELIABILITY_AWARE.md` for the completed executor screen, and `STOCHASTIC_ROBUST.md` for the active protocol.

## Incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

The incumbent is not replaced by the reliability-aware executor screen.

## Evidence that motivates the active protocol

### Simulator V2 headroom — `17000–17399`

```text
incumbent v2 normal:              0.801
perfect sensing diagnostic:      0.801
deterministic interaction diag:  0.999
best-of-5 oracle v2:              0.938
sensing headroom:                -0.0005 CI=[-0.00225, 0.0]
interaction headroom:            +0.1980 CI=[0.166, 0.23625]
```

The deterministic-success result is a loose counterfactual diagnostic, not an attainable-policy or mathematical upper-bound claim. Normal episodes averaged `15.661` failed real interaction attempts and exhausted abstract uses in `85.15%` of program-scenario episodes.

### Reliability-aware executor screen — `19000–19399`

```text
incumbent survival:               0.809
reliability-weighted survival:    0.810
contingent-backup survival:       0.825
weighted - incumbent:            +0.0003 CI=[-0.0165, +0.01775]
backup - incumbent:              +0.0155 CI=[-0.00625, +0.03575625]
backup - weighted:               +0.0152 CI=[-0.00825, +0.0375]
per-program backup deltas:        [-0.0025, +0.0250, +0.0200, +0.02875, +0.00625]
runtime inc/wgt/bak:              0.0218s / 0.0219s / 0.0450s
```

Decision:

- reliability weighting is effectively a null result;
- contingent backup is only a weak positive and does not earn confirmation;
- do not inspect `20000–20399`;
- do not declare backup the incumbent;
- stop one-step executor micro-tuning by default.

## Active experiment — stochastic-robust strategy training V1

Question:

> Holding the 60-token representation, local/evolutionary search family and scalar score fixed, does evaluating each candidate across multiple matched Simulator V2 random tapes per structural scenario produce strategies that generalize better under stochastic interaction outcomes?

### What changes

Only the stochastic training distribution:

- structural scenario/world seed is separated from random-tape seed;
- every candidate in both training arms sees the same world×tape bundle;
- metrics are averaged across replications before applying the established scalar fitness.

V1 does **not** add CVaR, a risk coefficient, new rule tokens, Axplorer, a planning horizon, or a new interaction model.

### Paired training arms

1. `robust_local_incumbent` — search through `RuleGuidedHungarianPolicy`;
2. `robust_local_backup` — search through `ReliabilityAwareBackupPolicy`.

Both use the same search seeds, initial search mechanics, candidate budget, structural worlds and random tapes.

### 2×2 cross-evaluation

Fresh evaluation runs both discovered program sets under both executors:

```text
incumbent-trained program × incumbent executor
incumbent-trained program × backup executor
backup-trained program    × incumbent executor
backup-trained program    × backup executor
```

This separates program adaptation, executor effect and co-adaptation.

The five old frozen incumbent programs are reported under both executors as descriptive references only; they were trained under a different simulator generation/protocol.

## Quick protocol — run first

```text
paired search runs:      2
candidate budget:        128 per arm/run
training worlds:         4
random tapes/world:      2
rollouts/candidate:      8
evaluation:              22000–22019
```

```bash
python -m aegisswarm.stochastic_robust_cli --workers 14
```

Do **not** run `--full` until the quick output is inspected.

## Full development protocol — only if quick passes

```text
paired search runs:      5
candidate budget:        1800 per arm/run
training worlds:         12
random tapes/world:      3
rollouts/candidate:      36
development evaluation:  22000–22399
```

Reserved confirmation: `23000–23399` — **do not inspect during development**.

Training structural-world pool: `21000–21031`; full V1 uses the first 12.

## Decision gate

### Robust incumbent training improves

Repeated-tape training itself is useful. Keep incumbent execution unless backup adds a clear incremental effect.

### Co-adapted robust backup improves materially

Training and contingent execution are complementary; this becomes a candidate architecture for a later frozen protocol.

### Both robust arms tie old frozen references

Mean replicated training does not capture the remaining stochastic headroom. A later explicit tail-risk/CVaR objective becomes more justified than further executor tweaking.

### Both worsen

Close V1 and retain the incumbent.

No confirmation is authorized by quick evidence or an ambiguous development result.

## Secondary future track

The best-of-5 frozen-program oracle reached `0.938`, a `+13.62` pp gap over mean incumbent performance. Context-dependent strategy selection remains a justified secondary experiment after this robust-training test.

## Evidence ledger

Consumed development/evidence includes:

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

Untouched reserved blocks tied to older protocols must not be repurposed:

- `6000–6399`
- `7000–7399`
- `8000–8399`
- `10000–10399`
- `12000–12399`
- `14000–14399`
- `16000–16399`
- `18000–18399`
- `20000–20399`

Current robust protocol:

- `21000–21031`: training structural worlds
- `22000–22399`: development evaluation
- `23000–23399`: reserved confirmation

## Claims policy

Supported development-level conclusions:

- optimizer-aware 60-token rule search remains the strategic incumbent;
- optimizer-native V2 was materially worse;
- corrected rolling-horizon execution did not improve the incumbent;
- perfect-sensing headroom was essentially zero on `17000–17399`;
- deterministic valid interactions showed large diagnostic headroom (`+19.8` pp, CI entirely positive);
- best-of-5 frozen-program oracle showed substantial scenario-selection headroom (`+13.62` pp);
- reliability-weighted Hungarian did not improve survival on the full fresh screen;
- contingent backup produced a small positive point estimate (`+1.55` pp) but did not establish a robust improvement.

Not supported:

- stochastic-robust training superiority before the active experiment runs;
- deterministic interaction success as attainable;
- contingent-backup executor superiority;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
