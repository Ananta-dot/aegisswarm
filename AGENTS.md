# AegisSwarm Agent Handoff

This repository is an active research project. **The architecture is not frozen for external claims.**

Read in order before changing algorithms, protocols, seeds, or claims:

1. `docs/AEGISSWARM_SKILL.md` — long-form history.
2. `docs/AEGISSWARM_STATUS.md` — latest-state overlay; supersedes older current wording.
3. `ORACLE_DECOMPOSITION.md` — active diagnostic.
4. `STRATEGY_SELECTOR.md` — closed selector V1.
5. `STOCHASTIC_TRAINING_ABLATION.md` — closed repeated-tape V2.
6. `STOCHASTIC_ROBUST.md` — closed robust-training V1.
7. `EVIDENCE_HARDENING.md` — completed Simulator V2/headroom protocol.
8. `RELIABILITY_AWARE.md` — completed reliability-executor screen.
9. `ROLLING_HORIZON.md` — completed planner history.

## Non-negotiable rules

1. Never consume reserved confirmation/replication seeds for development without an explicit protocol decision.
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

No tested proposer, compact representation, planner, reliability executor, repeated-tape training scheme, or t=0 observable selector has robustly replaced it.

## Completed evidence that matters now

Simulator V2 headroom on `17000–17399`:

```text
normal mean:                  0.801
perfect sensing:             0.801
deterministic interactions:  0.999
best-of-5 frozen oracle:     0.938
```

Reliability executor on `19000–19399`: weighting null; backup only `+1.55 pp` with CI crossing zero. Do not inspect `20000–20399`.

Stochastic-robust V1 quick: co-adapted backup minus incumbent `-8.75 pp`; V1 closed. Do not inspect `23000–23399`.

Clean stochastic-training V2 quick: repeated minus single `-6.25 pp`, both paired runs negative. Do not inspect `26000–26399`.

Observable selector V1 full development on `28000–28399`:

```text
fixed best:             0.8275
selector:               0.8113
selector-fixed:        -0.0163 CI=[-0.0350,+0.0025]
selector-fixed reward: -2.960 CI=[-5.3340,-0.6094]
raw hindsight oracle:   0.9338
```

Selector V1 is closed. Do not inspect `29000–29399` and do not tune selector features/models on that block by default.

## Active phase — oracle decomposition V1

Branch: `agent/oracle-decomposition`  
Protocol: `aegisswarm-oracle-decomposition-v1`

The raw best-of-5 oracle is not assumed to be predictable strategy specialization. `SimulatorV2` interaction draws are indexed by `(timestep, defender_id, threat_id)`, so different programs encounter different stochastic event paths. Same-realization hindsight can therefore reward stochastic luck.

No policy is trained or changed in this phase.

Fresh structural-world blocks:

- `30000–30399`: oracle-decomposition development
- `31000–31399`: reserved independent replication — **do not inspect during development**

Quick protocol:

```text
20 worlds: 30000–30019
4 indexed tapes/world
5 frozen programs
```

Primary diagnostic: symmetric cross-tape oracle. Select the best program per structural world on one half of the tapes, evaluate it on the held-out half, then reverse. Compare against a global fixed program selected/evaluated with the same cross-tape split.

Report:

- single-tape hindsight oracle gap;
- expected-outcome same-tape oracle gap;
- cross-tape oracle gap — primary;
- first-half vs second-half best-program agreement;
- modal stability of tape-specific oracle choices;
- fraction of raw oracle gap retained cross-tape.

Run only:

```bash
pytest -q
python -m aegisswarm.oracle_decomposition_cli --workers 14
```

Do not use `--full` until quick output is inspected.

## Interpretation

- Large positive cross-tape gap + stable choices: genuine structural specialization; richer/later-state gating may be justified.
- Raw oracle large but cross-tape gap near zero: most apparent headroom is stochastic hindsight; stop treating ~93–94% as a realistic selector target.
- Cross-tape oracle below fixed: per-world strategy identity is unstable; prefer robust/global or sequentially adaptive control rather than episode-level preselection.
