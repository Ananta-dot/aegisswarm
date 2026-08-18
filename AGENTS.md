# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `PPO_ADAPTIVE_CONTROL.md` — active online-adaptation protocol.
4. `ORACLE_DECOMPOSITION.md` — completed oracle decomposition.
5. `STRATEGY_SELECTOR.md` — closed selector protocol.
6. `STOCHASTIC_TRAINING_ABLATION.md` — closed repeated-tape V2.
7. `STOCHASTIC_ROBUST.md` — closed robust-training V1.
8. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
9. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
10. `ROLLING_HORIZON.md` — completed planner history.

## Non-negotiable rules

1. Never consume reserved confirmation/replication seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside a protocol.
4. Compare components by ablation, not ideology.
5. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
6. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
7. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
8. Keep handoff/status docs current after major experiments.
9. Do not run confirmation merely because a quick or development point estimate is positive.
10. Legacy `Simulator` and `SimulatorV2` are different protocol generations; label them explicitly.
11. Do not treat hindsight oracle performance as deployable or predictable without held-out stochastic evidence.
12. RL observations must never expose undetected threat state, scenario seed, future outcomes or oracle information.
13. PPO V1 must not directly choose combinatorial defender-threat assignments; the constrained assignment layer remains underneath the RL controller.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

No tested proposer, compact representation, planner, reliability executor, repeated-tape training scheme, or static selector has robustly replaced it.

## Completed oracle decomposition — selection closed

Full `30000–30399`, 400 worlds × 8 tapes/world:

```text
single-tape oracle-fixed:       +0.1037 CI=[+0.0825,+0.12625]
expected oracle-fixed:          +0.0495 CI=[+0.0421875,+0.056875]
cross-tape oracle-fixed:        -0.0150 CI=[-0.024375,-0.0053125]
cross-tape choice agreement:     0.305
tape-oracle modal fraction:      0.501
```

Decision:

- raw best-of-five performance is substantially hindsight-driven;
- per-world program identity does not generalize across independent tapes;
- episode-level frozen-program selection is closed;
- do not inspect `31000–31399` and do not build another static selector by default.

## Active phase — hierarchical PPO online adaptation V1

Branch: `agent/ppo-adaptive-control`  
Protocol: `aegisswarm-hierarchical-ppo-v1`

Motivation: Simulator V2 deterministic-interaction relaxation previously showed approximately `+19.8 pp` synthetic headroom, while static reliability/planning/training/selector changes did not capture it. Online RL is now justified because it can react to **realized** failures and resource state rather than predicting stochastic outcomes in advance.

### Architecture

```text
observable detected/known state + realized history
    -> PPO chooses tactical mode
    -> frozen base rule program index 1
    -> constrained assignment layer
    -> Simulator V2 outcome
    -> repeat
```

PPO action space:

```text
0 incumbent
1 urgency
2 conserve
3 reliability
4 backup
5 failure_recovery
```

The fixed tactical comparator is chosen by mean established reward on PPO training/calibration seeds only. PPO must beat both incumbent and that fixed comparator to establish online-learning value.

Reward is a scaled difference in the existing established episode score; `gamma=1.0` preserves telescoping of the undiscounted shaped return.

### Fresh blocks

```text
32000–32999  training/calibration
33000–33399  development
34000–34399  confirmation — DO NOT INSPECT
```

Quick:

```text
model seeds:            42101, 42102
100k env steps/model
calibration:            32000–32099
evaluation:             33000–33019
```

Install optional dependencies once:

```bash
pip install -e '.[rl]'
```

Then run only:

```bash
pytest -q
python -m aegisswarm.adaptive_rl_cli --workers 14
```

Do not use `--full` until quick output is inspected.

### Quick decision

- PPO > incumbent and static-best: authorize full development.
- PPO > incumbent but <= static-best: no evidence for adaptation; prefer simpler fixed mode.
- PPO ties/worsens: inspect mode collapse/learning behavior before any larger model or budget; close V1 if no adaptive signal.

Do not claim PPO or RL superiority from this protocol alone.
