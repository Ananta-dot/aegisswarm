# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** RELIABILITY EXECUTOR SCREEN COMPLETE; STOCHASTIC-ROBUST TRAINING IS NEXT  
**Active branch:** `agent/reliability-aware-assignment`  
**Completed protocol:** `aegisswarm-reliability-aware-screen-v1`

Read `docs/AEGISSWARM_SKILL.md` for long-form history, `EVIDENCE_HARDENING.md` for Simulator V2 headroom evidence, and `RELIABILITY_AWARE.md` for the completed executor screen.

## Incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

The incumbent is not replaced by the reliability screen.

## Why stochastic reliability is the main bottleneck

Evidence-hardening development on fresh Simulator V2 seeds `17000–17399` found:

```text
incumbent v2 normal:              0.801
perfect sensing diagnostic:      0.801
deterministic interaction diag:  0.999
best-of-5 oracle v2:              0.938
sensing headroom:                -0.0005 CI=[-0.00225, 0.0]
interaction headroom:            +0.1980 CI=[0.166, 0.23625]
```

Normal program-scenario episodes averaged `15.661` failed real interaction attempts and exhausted abstract uses in `85.15%` of episodes. Undetected penetrations were zero. The deterministic-success result is a loose counterfactual diagnostic, not an attainable-policy or mathematical upper-bound claim.

## Reliability-aware executor screen — COMPLETE

Fresh development block `19000–19399`, five frozen incumbent programs, Simulator V2 indexed randomness:

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

### Decision

1. **Reliability-weighted Hungarian is effectively a null result.** The full-screen point estimate is only `+0.03` percentage points and the interval is centered on zero. Do not pursue weighting-only variants.
2. **Contingent backup is a weak positive, not an established win.** Its point estimate is `+1.55` pp, four of five program-level effects are positive, but the hierarchical interval crosses zero and runtime is about 2x the incumbent.
3. Do **not** consume `20000–20399` confirmation. The executor has not earned a freeze.
4. Do **not** declare backup the incumbent or launch a confirmation campaign.
5. The executor experiment captures only a small fraction of the `+19.8` pp interaction headroom. The next hypothesis should therefore operate at the training/objective level rather than add more one-step assignment heuristics.

## Next experiment — stochastic-robust strategy training

The current 60-token programs were discovered under the legacy simulator, where each candidate sees one stochastic realization per training scenario. That is misaligned with the Simulator V2 evidence: stochastic interaction outcomes are the dominant measured loss source.

Next question:

> Holding the 60-token representation and conventional local/evolutionary search family fixed, does training each candidate across multiple policy-independent Simulator V2 random tapes per scenario produce strategies that generalize better under stochastic interaction outcomes?

The next protocol should:

- keep scenario geometry and random-tape seeds separate;
- evaluate every candidate on the same matched random tapes (common random numbers);
- average the existing scalar fitness over repeated tapes; do not introduce a CVaR/risk-weight hyperparameter in the first version;
- compare robust training with the incumbent executor against robust training with contingent backup under the same candidate budget and tape bundle;
- retain the old frozen incumbent programs as a reference only;
- use fresh training/development/confirmation seeds because the protocol is motivated by inspected `17000–17399` and `19000–19399` results.

No Axplorer/proposer comparison is needed in this first robust-training experiment; local/evolutionary search is the strongest established search baseline.

## Secondary future track

The best-of-5 frozen-program oracle reached `0.938`, a `+13.62` pp gap over mean incumbent performance. Context-dependent strategy selection remains a justified secondary experiment, but it follows stochastic-robust training because the interaction-reliability headroom is larger and more directly diagnosed.

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

Untouched reserved blocks tied to older protocols must not be silently repurposed:

- `6000–6399`
- `7000–7399`
- `8000–8399`
- `10000–10399`
- `12000–12399`
- `14000–14399`
- `16000–16399`
- `18000–18399`
- `20000–20399` — reliability-aware confirmation; **do not run**

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

- deterministic interaction success as attainable;
- contingent-backup executor superiority;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
