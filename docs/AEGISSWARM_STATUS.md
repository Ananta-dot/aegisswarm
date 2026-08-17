# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** INCUMBENT SELECTED; NEW RELIABILITY-AWARE EXECUTOR EXPERIMENT JUSTIFIED  
**Completed protocol:** `aegisswarm-evidence-hardening-v1`  
**Current decision:** INTERACTION RELIABILITY IS THE DOMINANT MEASURED HEADROOM SOURCE; TEST RELIABILITY-AWARE ASSIGNMENT ON FRESH DEVELOPMENT DATA

Read `docs/AEGISSWARM_SKILL.md` for long-form history and `EVIDENCE_HARDENING.md` for the completed headroom protocol.

## Incumbent before the next experiment

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

This remains the incumbent until a fresh controlled experiment demonstrates a better executor.

## Completed evidence-hardening result

Simulator V2 uses policy-independent indexed random draws and leaves the legacy simulator untouched. Full development used fresh seeds `17000–17399` and the same five frozen incumbent programs.

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

Best-of-5 oracle gap: `+0.1362` survival. Oracle choice counts across the 400 scenarios:

```text
{program0: 63, program1: 180, program2: 77, program3: 53, program4: 27}
```

Normal Simulator V2 diagnostic means:

```text
detection_opportunities:               58.4975
detections:                            29.9975
real_interaction_attempts:             30.2020
real_interaction_failures:             15.6610
decoy_resource_uses:                    1.3665
penetrations_undetected:                0.0000
penetrations_no_in_range_defender:      0.0000
penetrations_in_range_no_resource:      2.0450
penetrations_with_reachable_resource:   0.4350
overload_steps:                        42.6960
resource_uses_remaining:                0.5315
resource_exhausted fraction:            0.8515
```

Development-only failed-episode attribution:

```text
interaction_stochasticity:      0.9956268
strategy_selection_headroom:    0.0029155
interaction_failure_residual:   0.0014577
```

Interpretation boundary: the deterministic-interaction relaxation is a loose counterfactual diagnostic, not an attainable-policy claim or mathematical upper bound. The attribution says failed episodes improve under the relaxation; it is descriptive rather than causal proof.

## Main conclusion from headroom measurement

The repeated ~80% regime is **not explained by sensing** and is **not close to the loose simulator envelope**.

The strongest measured bottleneck is the combination of stochastic abstract interaction outcomes and scarce resource use:

- perfect sensing changes survival by essentially zero;
- deterministic valid interactions add about `+19.8` percentage points with a hierarchical CI entirely above zero;
- normal episodes average `15.661` failed real interaction attempts;
- resources are fully exhausted in about `85.15%` of program-scenario episodes;
- undetected penetrations are zero;
- decoy consumption is comparatively small.

This motivates an executor that explicitly accounts for expected interaction success and scarce capacity rather than another proposer, strategic representation, or longer planning horizon.

## Secondary conclusion — strategy specialization

The non-deployable best-of-5 oracle reaches `0.938`, a `+13.62` pp gap above the mean frozen incumbent. All five programs are selected in some scenarios, so scenario-dependent strategy specialization is real enough to justify a later selector/meta-policy experiment.

This is secondary to reliability-aware assignment because interaction headroom is larger and directly tied to resource loss.

## Next experiment — reliability-aware assignment

New architecture question:

> Holding the five frozen 60-token programs fixed, can an executor that incorporates abstract success probability and limited contingent backup allocation improve survival/resource efficiency over the current one-step Hungarian executor?

The experiment should separate two effects:

1. **reliability-weighted one-to-one assignment** — same one-to-one semantics as the incumbent, but strategic utility is weighted by abstract success probability;
2. **reliability-aware contingent backup allocation** — allow at most one backup resource for a high-value threat and optimize expected strategic value under stochastic failure, while preserving each defender's one-assignment-per-step constraint.

No strategy retraining in the initial screen. No change to sensing, scenario generation, or stochastic interaction law.

Because this architecture is motivated by the inspected `17000–17399` development result, it must use fresh evidence blocks.

Proposed fresh blocks:

- `19000–19399`: reliability-aware development
- `20000–20399`: reserved reliability-aware confirmation — do not inspect during development

Keep `18000–18399` untouched and tied to the completed evidence-hardening protocol; do not repurpose it.

## Closed tracks

- optimizer-native V2: materially worse; no V3; do not use `12000–12399` confirmation;
- rolling-horizon V1/V2: no useful gain and much slower; no planner V3; do not use `16000–16399` confirmation;
- sensing as the immediate bottleneck: not supported by evidence-hardening development.

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

Untouched reserved blocks tied to older protocols:

- `6000–6399`
- `7000–7399`
- `8000–8399`
- `10000–10399`
- `12000–12399`
- `14000–14399`
- `16000–16399`
- `18000–18399`

## Claims policy

Supported development-level conclusions now include:

- the incumbent remains much stronger than the fixed hand-written optimizer baseline in the synthetic simulator;
- Axplorer did not materially outperform optimizer-aware local/evolutionary search under the matched protocol;
- optimizer-native V2 was materially worse than the 60-token rule representation;
- corrected rolling-horizon execution did not improve the incumbent and was substantially slower;
- under Simulator V2, perfect sensing produced essentially no survival headroom on `17000–17399`;
- deterministic valid interactions produced a large positive diagnostic headroom (`+19.8` pp, CI `[+16.6,+23.625]` pp);
- a best-of-5 frozen-program oracle produced substantial scenario-selection headroom (`+13.62` pp).

Not supported:

- that deterministic interactions are attainable in a deployable system;
- that reliability-aware assignment will improve performance before it is tested on fresh data;
- superiority to optimization or RL generally;
- real-world effectiveness or deployment readiness.
