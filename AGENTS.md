# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in this order before changing algorithms or evidence protocols:

1. `docs/AEGISSWARM_SKILL.md`
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay
3. `RELIABILITY_AWARE.md` — active protocol
4. `EVIDENCE_HARDENING.md` — completed headroom protocol
5. `ROLLING_HORIZON.md` — completed planner history

## Non-negotiable rules

1. Never consume reserved confirmation seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside an evidence protocol.
4. Compare components by controlled ablation.
5. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
6. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
7. Legacy `Simulator` and `SimulatorV2` are different protocol generations; label them explicitly.
8. Do not make real-world effectiveness or deployment claims from these synthetic experiments.

## Incumbent before active reliability screen

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

Closed tracks:

- optimizer-native V2: materially worse; no V3; do not use `12000–12399` confirmation;
- rolling-horizon V1/V2: no useful gain and much slower; no planner V3; do not use `16000–16399` confirmation.

## Completed evidence-hardening result

Fresh Simulator V2 development `17000–17399`:

```text
incumbent normal:              0.801
perfect sensing:              0.801
interaction deterministic:    0.999
best-of-5 oracle:              0.938
interaction headroom:        +0.1980 CI=[0.166,0.23625]
sensing headroom:            -0.0005 CI=[-0.00225,0.0]
```

Important diagnostics:

```text
real interaction failures mean:     15.661
resource exhausted fraction:         0.8515
penetrations undetected mean:        0.0
decoy resource uses mean:            1.3665
best-of-5 oracle gap:                +0.1362
```

Interpretation: sensing is not the immediate bottleneck. The dominant measured headroom is stochastic abstract interaction reliability under scarce capacity. Deterministic success is only a loose diagnostic relaxation, not an attainable-policy claim.

`18000–18399` remains untouched and belongs to the completed evidence-hardening protocol. Do not repurpose it.

## Active experiment — reliability-aware assignment

Branch: `agent/reliability-aware-assignment`  
Protocol: `aegisswarm-reliability-aware-screen-v1`

Question:

> Holding the same five 60-token programs fixed, can success-probability-aware allocation improve over the incumbent one-step Hungarian executor under SimulatorV2?

Three variants:

1. incumbent `RuleGuidedHungarianPolicy`;
2. `ReliabilityWeightedHungarianPolicy` — same one-to-one matching, score = strategic utility × abstract success probability;
3. `ReliabilityAwareBackupPolicy` — set-packing executor with either one defender or an ordered primary+contingent-backup pair per threat, maximum two defenders per threat.

No strategy retraining in the screen.

Fresh reliability blocks:

- `19000–19399`: development
- `20000–20399`: reserved confirmation — **do not inspect**

Quick mode uses `19000–19019`.

## Immediate runbook

```bash
git fetch origin
git checkout agent/reliability-aware-assignment
git pull origin agent/reliability-aware-assignment
pytest -q
python -m aegisswarm.reliability_cli --workers 14
```

Do not run `--full` until quick output is inspected.

## Decision gate

- weighted improves and backup does not -> keep one-to-one reliability weighting;
- backup materially improves beyond weighted -> contingent backup is worth deeper evaluation;
- both tie/worsen -> close this formulation and move to robust stochastic training/objectives rather than executor tuning;
- strategy-selection work remains secondary and should use a separate fresh protocol if pursued.
