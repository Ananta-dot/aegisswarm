# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `STOCHASTIC_TRAINING_ABLATION.md` — active V2 protocol.
4. `STOCHASTIC_ROBUST.md` — closed V1 robust-training history.
5. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
6. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
7. `ROLLING_HORIZON.md` — completed planner history.

## Non-negotiable rules

1. Never consume reserved confirmation seeds for development.
2. Once inspected, a block is never untouched again.
3. Do not silently change simulator/scoring/budgets inside a protocol.
4. Compare components by ablation, not ideology.
5. Existing Hungarian and tabular-Q baselines are simple baselines, not representatives of optimization/RL generally.
6. Keep implementation abstract, synthetic, defensive, and decision-support oriented.
7. Record protocol IDs, seeds, budgets, source commit, artifacts, uncertainty, and architecture changes caused by inspected results.
8. Keep handoff/status docs current after major experiments.
9. Do not run confirmation merely because a quick or development point estimate is positive.
10. Legacy `Simulator` and `SimulatorV2` are different protocol generations; label them explicitly.

## Current incumbent

```text
60-token state-reactive rule representation
+ optimizer-aware local/evolutionary offline search
+ one-step RuleGuidedHungarianPolicy
```

No tested proposer, compact representation, planner, reliability weighting, or backup executor has robustly replaced it.

## Key current-generation evidence

Simulator V2 headroom (`17000–17399`): normal `0.801`, perfect sensing `0.801`, deterministic interactions `0.999`, interaction diagnostic headroom `+0.1980 CI=[+0.166,+0.23625]`, best-of-5 oracle `0.938`.

Reliability executor (`19000–19399`): incumbent `0.809`, weighted `0.810`, backup `0.825`; weighting is null and backup is only a weak positive (`+0.0155 CI=[-0.00625,+0.03575625]`). Do not inspect `20000–20399`.

Stochastic-robust V1 quick (`22000–22019`) closed the backup/co-adaptation hypothesis:

```text
robust inc/inc:          0.713
robust backup/backup:    0.625
co-adapted delta:       -0.0875 CI=[-0.225,+0.05]
per-run deltas:         [-0.05,-0.125]
```

Do not run V1 full and do not inspect `23000–23399`. V1 quick inspected training worlds `21000–21003` and evaluation `22000–22019`; do not reuse the remainder of those V1 blocks as unseen evidence for a changed protocol.

## Active phase — stochastic-training ablation V2

Branch: `agent/stochastic-training-ablation`  
Protocol: `aegisswarm-stochastic-training-ablation-v2`

Primary comparison:

1. single-tape Simulator V2 training;
2. repeated-tape Simulator V2 training.

Both arms use the same incumbent `RuleGuidedHungarianPolicy`, 60-token representation, local/evolutionary search, search seeds, structural worlds, candidate budget and scalar score. The repeated arm includes the single arm's replicate-0 tape plus additional matched tapes for every world.

Fresh V2 blocks:

- `24000–24031`: structural training worlds;
- `25000–25399`: development evaluation;
- `26000–26399`: reserved confirmation — **do not inspect**.

Quick V2:

```text
2 paired search runs
128 candidates/arm/run
4 structural worlds
single:   1 tape/world = 4 rollouts/candidate
repeated: 2 tapes/world = 8 rollouts/candidate
evaluation: 25000–25019
```

Run only:

```bash
python -m aegisswarm.stochastic_training_ablation_cli --workers 14
```

Do not run `--full` until quick V2 is inspected.

## Secondary track

Best-of-5 oracle headroom is `+13.62` pp. Context-dependent strategy selection is the leading separate hypothesis if repeated-tape training does not produce a useful gain.
