# AegisSwarm — Current Research Status

**Updated:** 2026-08-17  
**Architecture status:** CURRENT INCUMBENT SELECTED FOR EVIDENCE HARDENING; NOT FROZEN FOR EXTERNAL CLAIMS  
**Active branch:** `agent/evidence-hardening`  
**Active protocol:** `aegisswarm-evidence-hardening-v1`  
**Current decision:** MEASURE SIMULATOR HEADROOM AND HARDEN PAIRED STOCHASTIC EVALUATION BEFORE ANOTHER ARCHITECTURE CHANGE

Read `docs/AEGISSWARM_SKILL.md` for full history and `EVIDENCE_HARDENING.md` for the active protocol.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy executor
```

This remains the incumbent because:

- hybrid-objective development: local `0.805`, Axplorer `0.810`, Axplorer-local `+0.0055`, CI `[-0.0235,+0.0320]`;
- optimizer-native V2: rules `0.813` vs native `0.701`, native-rule `-0.1120`, CI `[-0.1405,-0.08249]`;
- rolling-horizon V2: one-step `0.808` vs rolling `0.801`, rolling-one-step `-0.0065`, CI `[-0.0325,+0.01825]`, roughly 14x slower.

No proposer, representation, or planner variant currently has evidence strong enough to replace it.

## Closed architecture tracks

### Optimizer-native representation

Closed. No V3 vector. Do not consume `12000–12399` confirmation.

### Rolling-horizon planning

Planner V1 was worse and exposed a receding-horizon action-deferral defect. Planner V2 corrected that defect but still failed to improve the incumbent on fresh development seeds `15000–15399`:

```text
fixed_optimizer survival: 0.329
rule_one_step survival:   0.808 CI=[0.776, 0.83575]
rule_rolling_v2 survival: 0.801 CI=[0.76174375, 0.837]
rolling - one_step:      -0.0065 CI=[-0.0325, +0.01825]
per-program deltas:       [-0.025, -0.03625, +0.0225, -0.0075, +0.01375]
scenario sign-flip p:     0.333083
runtime one-step/rolling: 0.0128 s / 0.1774 s
```

Do not run planner-aware training, do not build planner V3 by default, and do not consume `16000–16399` confirmation.

## Active evidence-hardening phase

The repeated low-80% survival regime has survived proposer, representation, and executor changes. The next question is therefore:

> **How much headroom exists in the current synthetic environment, and which simulator-level limitations account for the remaining asset losses?**

### Simulator V2

New files:

- `aegisswarm/random_tape.py`
- `aegisswarm/simulator_v2.py`
- `aegisswarm/evidence_hardening.py`
- `aegisswarm/evidence_hardening_cli.py`
- `tests/test_evidence_hardening.py`
- `EVIDENCE_HARDENING.md`

Legacy `Simulator` is deliberately untouched. Simulator V2 is an opt-in evidence path using policy-independent indexed random draws keyed by scenario seed and event identity for detection, motion noise, and abstract interaction outcomes.

This improves common-random-number coupling without invalidating old protocols.

### Frozen-program headroom diagnostics

The active protocol loads the same five incumbent rule programs and evaluates:

```text
legacy incumbent reference
fixed optimizer under Simulator V2
incumbent under normal Simulator V2
incumbent + perfect sensing diagnostic
incumbent + deterministic interaction diagnostic
incumbent + combined diagnostic
best-of-5 per-scenario oracle diagnostic
```

The relaxations are development diagnostics, not deployable assumptions or mathematical upper bounds. Best-of-5 is a non-deployable oracle used only to estimate scenario-dependent strategy-selection headroom.

### Failure attribution

For asset-loss episodes, the suite first checks whether paired sensing/interaction relaxations improve survival. Residual cases are labeled from direct simulator counters including:

- undetected penetrations;
- real interaction failures;
- resource exhaustion;
- decoy resource use;
- overload steps;
- no in-range defender;
- penetrations despite reachable remaining resources.

These categories are descriptive development diagnostics, not causal proof.

## Active evidence blocks

- `17000–17399`: evidence-hardening development
- `18000–18399`: reserved evidence/confirmation — **do not inspect**

Quick mode uses `17000–17019`; once inspected those are development data.

## Immediate runbook

```bash
git fetch origin
git checkout agent/evidence-hardening
git pull origin agent/evidence-hardening
pytest -q
python -m aegisswarm.evidence_hardening_cli --workers 14
```

Do not run `--full` until the quick output is inspected for:

1. reproducibility/test failures;
2. pathological shift between legacy reference and normal Simulator V2;
3. nonsensical diagnostic ordering;
4. failure-attribution bugs.

If quick is valid:

```bash
python -m aegisswarm.evidence_hardening_cli --full --workers 14
```

## Decision tree after full headroom development

### Large best-of-5 oracle gap

Investigate a context-dependent strategy selector/meta-policy.

### Large perfect-sensing gap

Prioritize observation/state-estimation or abstract sensor-allocation work.

### Large deterministic-interaction gap

Prioritize robust/risk-aware objectives, stochastic replications, and uncertainty-aware evaluation rather than more policy complexity.

### Large resource/overload residual

Sequential resource allocation/adaptive learning becomes better motivated.

### Small headroom across diagnostics

Stop optimizing this benchmark toward an arbitrary higher survival rate. Shift toward richer scenario families, robustness, tail risk/CVaR, scaling, stronger baselines, and external calibration.

## Evidence ledger

Consumed development/evidence blocks include:

- `2000–2099`: structured development-test;
- `2100–2499`: V1 formal holdout;
- `3000–3399`: Axplorer V2 development;
- `4000–4399`: hybrid-executor development;
- `5000–5399`: hybrid-objective development;
- `9000–9399`: optimizer-native V1 development;
- `11000–11399`: optimizer-native V2 development;
- `13000–13399`: rolling-horizon planner V1 development;
- `15000–15399`: rolling-horizon planner V2 development.

Untouched older reserved blocks tied to abandoned/unfrozen protocols must not be silently repurposed as confirmation:

- `6000–6399`;
- `7000–7399`;
- `8000–8399`;
- `10000–10399`;
- `12000–12399`;
- `14000–14399`;
- `16000–16399`.

Active:

- `17000–17399`: evidence development;
- `18000–18399`: reserved evidence/confirmation.

## Claims policy

Supported development-level conclusions:

- optimizer-aware searched 60-token rule strategies substantially improve the current fixed hand-written myopic objective in the legacy synthetic simulator;
- Axplorer did not materially outperform conventional local/evolutionary search under the matched hybrid-objective protocol;
- optimizer-native V2 was 11.2 percentage points worse than the 60-token rule representation on fresh development data;
- corrected rolling-horizon V2 was effectively tied/slightly worse than one-step execution and about 14x slower;
- the 60-token rules + optimizer-aware local search + one-step Hungarian executor remain the incumbent architecture.

Not yet supported:

- that ~81% is the attainable simulator ceiling;
- any Simulator V2 performance claim before the active evidence protocol runs;
- superiority to optimization generally;
- superiority to state-of-the-art RL/MARL;
- real-world effectiveness or deployment readiness.

## External target

The project is still working backward from the currently tracked iDEX Open Challenge deadline of **30 September 2026, 11:59 PM**, last verified on 2026-08-17. Re-check the official source before submission work.
