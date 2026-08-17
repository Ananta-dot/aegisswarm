# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Before changing algorithms, experiments, seed splits, claims, or submission material, read in this order:

1. [`docs/AEGISSWARM_SKILL.md`](docs/AEGISSWARM_SKILL.md) — canonical long-form history/methodology.
2. [`docs/AEGISSWARM_STATUS.md`](docs/AEGISSWARM_STATUS.md) — latest-result/current-decision overlay; this supersedes older current-status wording.
3. [`EVIDENCE_HARDENING.md`](EVIDENCE_HARDENING.md) — active simulator-v2/headroom protocol.
4. [`ROLLING_HORIZON.md`](ROLLING_HORIZON.md) — completed planner V1/V2 history.

## Non-negotiable rules

1. Never consume reserved confirmation seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside an evidence protocol.
4. Compare components by ablation, not ideology.
5. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
6. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
7. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
8. Keep handoff/status docs current after major experiments.
9. Do not run a reserved confirmation merely because a development result is positive.
10. Simulator-version results must remain labeled. Legacy `Simulator` and `SimulatorV2` are different protocol generations.

## Current incumbent architecture

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy execution
```

Do not reopen proposer/vector/planner tuning by default. The evidence to date is:

- hybrid-objective local `0.805`, Axplorer `0.810`, delta `+0.0055`, CI `[-0.0235,+0.0320]`;
- optimizer-native V2 rules `0.813` vs native `0.701`, delta `-0.1120`, CI `[-0.1405,-0.08249]`;
- rolling-horizon V2 one-step `0.808` vs rolling `0.801`, delta `-0.0065`, CI `[-0.0325,+0.01825]`, ~14x slower.

## Closed tracks

- optimizer-native representation: closed; no V3; do not use `12000–12399` confirmation.
- rolling-horizon V1/V2: closed; no planner-aware training or planner V3 by default; do not use `16000–16399` confirmation.

## Active phase — evidence hardening / simulator headroom

Branch: `agent/evidence-hardening`  
Protocol: `aegisswarm-evidence-hardening-v1`

The active code adds an **opt-in** `SimulatorV2` with indexed event randomness. Legacy `Simulator` remains untouched for reproducibility.

New core files:

- `aegisswarm/random_tape.py`
- `aegisswarm/simulator_v2.py`
- `aegisswarm/evidence_hardening.py`
- `aegisswarm/evidence_hardening_cli.py`
- `tests/test_evidence_hardening.py`
- `EVIDENCE_HARDENING.md`

Frozen incumbent programs are evaluated under:

- normal Simulator V2;
- perfect-sensing diagnostic;
- deterministic-interaction diagnostic;
- combined diagnostic;
- best-of-5 per-scenario oracle;
- fixed-optimizer V2 baseline;
- descriptive legacy-Simulator reference.

Diagnostic relaxations are not deployable assumptions or mathematical upper bounds. Best-of-5 is a non-deployable oracle.

## Active evidence blocks

- `17000–17399`: development
- `18000–18399`: reserved evidence/confirmation — do not inspect

Quick mode consumes only `17000–17019` as development.

## Immediate runbook

```bash
git checkout agent/evidence-hardening
git pull origin agent/evidence-hardening
pytest -q
python -m aegisswarm.evidence_hardening_cli --workers 14
```

Do not run `--full` until quick output is inspected. If quick is valid:

```bash
python -m aegisswarm.evidence_hardening_cli --full --workers 14
```

## Decision after headroom measurement

- large best-of-5 gap -> investigate strategy selector/meta-policy;
- large sensing gap -> prioritize observation/state-estimation/sensor-allocation research;
- large stochastic-interaction gap -> prioritize robustness/risk-aware objectives and stochastic replication;
- large resource/overload residual -> sequential resource allocation/adaptive methods become better motivated;
- small headroom -> stop chasing a higher score in this benchmark and move to richer scenarios, robustness, tail risk, stronger baselines, scaling, and external calibration.
